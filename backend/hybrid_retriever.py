import math
from typing import List, Dict, Any, Optional, Tuple
from backend.pg_database import get_pg_connection
from backend.vector_store import PgVectorStore, compute_text_embedding, cosine_similarity_arrays
from backend.location_service import LocationService, haversine_distance
from backend.query_planner import QueryIntent

class HybridRetriever:
    """
    Unified Production Hybrid Retrieval Pipeline for GeoGuide.
    Combines:
    1. Dense Semantic Retrieval (384-dim PyTorch embeddings in PostgreSQL)
    2. Lexical / Full-Text / Trigram Retrieval (`pg_trgm`)
    3. Entity-Linked Document & POI Chunks
    4. PostGIS / earthdistance Spatial Proximity Search
    5. Configurable Multi-Signal Reranking (Normalized signals)
    """

    def __init__(self, config: Optional[Dict[str, float]] = None):
        self.vector_store = PgVectorStore()
        # Explicit, configurable ranking weights
        self.weights = config or {
            "semantic": 0.40,
            "lexical": 0.35,
            "entity": 0.15,
            "spatial": 0.10
        }

    def retrieve(
        self,
        query: str,
        query_intent: QueryIntent,
        top_k: int = 5,
        min_relevance: float = 0.04,
        user_lat: Optional[float] = None,
        user_lon: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Executes hybrid candidate generation, deduplication, scoring, and reranking.
        """
        candidate_pool: Dict[str, Dict[str, Any]] = {}

        # -------------------------------------------------------------
        # 1. DENSE SEMANTIC RETRIEVAL (PostgreSQL Chunks)
        # -------------------------------------------------------------
        semantic_results = self.vector_store.search(
            query=query,
            city_id=query_intent.destination_id,
            top_k=top_k * 3,
            min_similarity=min_relevance
        )
        for r in semantic_results:
            key = f"chunk::{r.get('id')}"
            candidate_pool[key] = {
                "id": r.get("id"),
                "type": "knowledge_chunk",
                "title": r.get("title", ""),
                "content": r.get("chunk_text", r.get("content", "")),
                "source": r.get("source_name", r.get("source", "Official Registry")),
                "source_type": r.get("source_type", "database"),
                "city_id": r.get("city_id"),
                "topic": r.get("topic", "general"),
                "semantic_score": float(r.get("relevance_score", 0.0)),
                "lexical_score": 0.0,
                "entity_score": 0.0,
                "spatial_score": 0.0,
                "distance_m": None,
                "verified": bool(r.get("confidence", 0.9) >= 0.8)
            }

        # -------------------------------------------------------------
        # 2. LEXICAL & TRIGRAM RETRIEVAL (PostgreSQL Chunks & POIs)
        # -------------------------------------------------------------
        conn = get_pg_connection()
        with conn.cursor() as cur:
            # Query chunks by title & chunk_text using GREATEST pg_trgm similarity
            cur.execute("""
            SELECT id, title, chunk_text, source_name, source_type, city_id, topic,
                   similarity(title, %s) as title_sim,
                   similarity(chunk_text, %s) as content_sim
            FROM knowledge_chunks
            WHERE (%s::int IS NULL OR city_id = %s::int)
            ORDER BY GREATEST(similarity(title, %s), similarity(chunk_text, %s)) DESC
            LIMIT %s;
            """, (query, query, query_intent.destination_id, query_intent.destination_id, query, query, top_k * 3))
            
            for row in cur.fetchall():
                key = f"chunk::{row[0]}"
                lex_score = max(float(row[7]), float(row[8]))
                if key in candidate_pool:
                    candidate_pool[key]["lexical_score"] = lex_score
                elif lex_score > 0.03:
                    candidate_pool[key] = {
                        "id": row[0],
                        "type": "knowledge_chunk",
                        "title": row[1],
                        "content": row[2],
                        "source": row[3],
                        "source_type": row[4],
                        "city_id": row[5],
                        "topic": row[6],
                        "semantic_score": 0.0,
                        "lexical_score": lex_score,
                        "entity_score": 0.0,
                        "spatial_score": 0.0,
                        "distance_m": None,
                        "verified": True
                    }

            # ---------------------------------------------------------
            # 3. ENTITY & POI MATCHING (activities_poi & safety_advisories)
            # ---------------------------------------------------------
            cur.execute("""
            SELECT id, name, tag_badge, short_desc, full_desc, lat, lng,
                   city_id, open_time, close_time, entry_fee_inr, is_step_free, ticket_policy,
                   similarity(name, %s) as name_sim,
                   GREATEST(similarity(short_desc, %s), similarity(full_desc, %s)) as desc_sim
            FROM activities_poi
            WHERE (%s::int IS NULL OR city_id = %s::int)
            ORDER BY GREATEST(similarity(name, %s), similarity(short_desc, %s), similarity(full_desc, %s)) DESC
            LIMIT %s;
            """, (query, query, query, query_intent.destination_id, query_intent.destination_id, query, query, query, top_k * 2))
            
            for p in cur.fetchall():
                key = f"poi::{p[0]}"
                content = f"{p[1]}: {p[3]} {p[4]} Ticket Policy: {p[12]} Hours: {p[8]}-{p[9]} Fee: ₹{p[10]}"
                cand_score = max(float(p[13]), float(p[14]))
                candidate_pool[key] = {
                    "id": p[0],
                    "type": "poi_detail",
                    "title": p[1],
                    "content": content,
                    "source": "ASI / Official Tourism Registry",
                    "source_type": "official_registry",
                    "city_id": p[7],
                    "lat": p[5],
                    "lng": p[6],
                    "topic": "poi_detail",
                    "semantic_score": 0.0,
                    "lexical_score": cand_score,
                    "entity_score": 0.80 if cand_score > 0.20 else 0.40,
                    "spatial_score": 0.0,
                    "distance_m": None,
                    "verified": True
                }

            # Also include safety advisories
            cur.execute("""
            SELECT id, title, description, severity, detour_advice, city_id,
                   similarity(title, %s) as adv_sim
            FROM safety_advisories
            WHERE is_active = 1 AND (%s::int IS NULL OR city_id = %s::int)
            ORDER BY similarity(title, %s) DESC
            LIMIT %s;
            """, (query, query_intent.destination_id, query_intent.destination_id, query, top_k))
            for sa in cur.fetchall():
                key = f"advisory::{sa[0]}"
                content = f"{sa[1]}: {sa[2]} Advice: {sa[4] or ''}"
                candidate_pool[key] = {
                    "id": sa[0],
                    "type": "safety_advisory",
                    "title": sa[1],
                    "content": content,
                    "source": "State & District Tourism Advisory",
                    "source_type": "advisory",
                    "city_id": sa[5],
                    "topic": "safety_advisory",
                    "semantic_score": 0.0,
                    "lexical_score": float(sa[6]),
                    "entity_score": 0.60 if float(sa[6]) > 0.15 else 0.20,
                    "spatial_score": 0.0,
                    "distance_m": None,
                    "verified": True
                }
        conn.close()

        # -------------------------------------------------------------
        # 4. SPATIAL PROXIMITY SCORING (When user coordinates are active)
        # -------------------------------------------------------------
        if user_lat is not None and user_lon is not None:
            for cand in candidate_pool.values():
                c_lat = cand.get("lat")
                c_lng = cand.get("lng")
                if c_lat is not None and c_lng is not None:
                    dist_m = haversine_distance(user_lat, user_lon, c_lat, c_lng)
                    cand["distance_m"] = round(dist_m, 1)
                    # Normalized spatial score: 1.0 at 0m, decaying to 0.0 at 10km
                    cand["spatial_score"] = max(0.0, 1.0 - (dist_m / 10000.0))

        # -------------------------------------------------------------
        # 5. MULTI-SIGNAL NORMALIZATION & RERANKING
        # -------------------------------------------------------------
        ranked_candidates = []
        req_entity_low = (query_intent.resolved_entity or "").lower()
        is_generic_city = query_intent.entity_type == "CITY"

        for cand in candidate_pool.values():
            # Compute semantic score if 0.0 and text exists
            if cand["semantic_score"] == 0.0:
                q_emb = compute_text_embedding(query)
                c_emb = compute_text_embedding(f"{cand['title']} {cand['content']}")
                cand["semantic_score"] = max(0.0, cosine_similarity_arrays(q_emb, c_emb))

            # Entity relevance boost (only when specific entity requested, not broad city)
            if not is_generic_city and req_entity_low and req_entity_low in (cand["title"] + " " + cand["content"]).lower():
                cand["entity_score"] = max(cand["entity_score"], 0.85)

            # Combined weighted score
            final_score = (
                self.weights["semantic"] * cand["semantic_score"] +
                self.weights["lexical"] * cand["lexical_score"] +
                self.weights["entity"] * cand["entity_score"] +
                self.weights["spatial"] * cand["spatial_score"]
            )
            cand["relevance_score"] = round(final_score, 4)
            ranked_candidates.append(cand)

        ranked_candidates.sort(key=lambda x: x["relevance_score"], reverse=True)
        return ranked_candidates[:top_k]
