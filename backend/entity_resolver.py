import re
import unicodedata
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Any, Optional, Tuple
from backend.location_service import haversine_distance
from backend.pg_database import get_pg_connection

def normalize_name(text: str) -> str:
    """Normalizes string for exact, phonetic, and near-exact entity comparison."""
    if not text:
        return ""
    text = unicodedata.normalize('NFKD', text)
    text = text.lower().strip()
    text = re.sub(r'[^\w\s]', ' ', text)
    tokens = text.split()
    return " ".join(tokens)

class EntityResolver:
    """
    Dedicated Multi-Stage Entity Resolution & Disambiguation Subsystem for GeoGuide.
    Features:
    1. Dynamic candidate generation from PostgreSQL (activities_poi & entities) using pg_trgm and token overlap.
    2. Multi-factor scoring: Lexical overlap, category alignment, geographic proximity, branch differentiation.
    3. Branch and distinct entity differentiation (e.g. SLV Hotel vs SLV Delite / SLV Corner).
    4. Ambiguity preservation when multiple candidates are plausible instead of confident guessing.
    """

    @staticmethod
    def get_database_candidates(query_text: str, city_id: Optional[int] = None, limit: int = 15) -> List[Dict[str, Any]]:
        """
        Dynamically fetches entity candidates from PostgreSQL using pg_trgm similarity and word matching.
        Eliminates reliance on hardcoded entity dictionaries.
        """
        norm_q = normalize_name(query_text)
        stopwords = {"the", "what", "where", "near", "open", "timing", "hours", "ticket", "cost", "about", "tell", "which", "place", "has", "can", "see", "are"}
        tokens = [t for t in norm_q.split() if len(t) > 2 and t not in stopwords]
        content_query = " ".join(tokens) if tokens else query_text

        candidates = []
        try:
            conn = get_pg_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # 1. Query activities_poi (evaluating name, features, tag_badge, and descriptions)
                poi_query = """
                SELECT id, name, tag_badge, short_desc, full_desc, lat as latitude, lng as longitude,
                       city_id, category_id, open_time, close_time, entry_fee_inr, is_step_free,
                       rating, 'POI' as entity_type,
                       GREATEST(
                           similarity(name, %s), similarity(name, %s),
                           similarity(COALESCE(tag_badge, ''), %s),
                           similarity(COALESCE(short_desc, ''), %s) * 0.8,
                           similarity(COALESCE(full_desc, ''), %s) * 0.8
                       ) as trigram_sim
                FROM activities_poi
                WHERE (%s::int IS NULL OR city_id = %s::int)
                ORDER BY GREATEST(
                           similarity(name, %s), similarity(name, %s),
                           similarity(COALESCE(tag_badge, ''), %s),
                           similarity(COALESCE(short_desc, ''), %s) * 0.8,
                           similarity(COALESCE(full_desc, ''), %s) * 0.8
                       ) DESC
                LIMIT %s;
                """
                cur.execute(poi_query, (
                    query_text, content_query, content_query, content_query, content_query,
                    city_id, city_id,
                    query_text, content_query, content_query, content_query, content_query,
                    limit
                ))
                for row in cur.fetchall():
                    c = dict(row)
                    c["category"] = "Monument / Heritage" if c.get("category_id") == 1 else ("Food / Dining" if c.get("category_id") == 3 else "Place of Interest")
                    candidates.append(c)

                # 2. Query canonical cities table first
                cur.execute("SELECT id, name, state, lat as latitude, lng as longitude, 'CITY' as entity_type FROM cities;")
                for row in cur.fetchall():
                    c = dict(row)
                    c["category"] = "City / Region"
                    c["city_id"] = c["id"]
                    if not any(normalize_name(x.get("name", "")) == normalize_name(c.get("name", "")) for x in candidates):
                        candidates.append(c)

                # 2b. Query entities table
                ent_query = """
                SELECT id, name, entity_type, city_id, city_name, latitude, longitude,
                       category, address,
                       similarity(name, %s) as trigram_sim
                FROM entities
                WHERE (%s::int IS NULL OR city_id = %s::int)
                ORDER BY similarity(name, %s) DESC
                LIMIT %s;
                """
                cur.execute(ent_query, (query_text, city_id, city_id, query_text, limit))
                for row in cur.fetchall():
                    c = dict(row)
                    if not any(normalize_name(x.get("name", "")) == normalize_name(c.get("name", "")) for x in candidates):
                        candidates.append(c)

                # 2c. Query knowledge_chunks titles & features linked to entities
                kc_query = """
                SELECT k.entity_id as id, p.name as name, 'POI' as entity_type, k.city_id, c.name as city_name,
                       p.lat as latitude, p.lng as longitude, 'Feature / Landmark' as category, p.short_desc as address,
                       GREATEST(similarity(k.title, %s), similarity(k.title, %s)) as trigram_sim
                FROM knowledge_chunks k
                JOIN activities_poi p ON k.entity_id = p.id
                JOIN cities c ON k.city_id = c.id
                WHERE k.entity_id IS NOT NULL AND (%s::int IS NULL OR k.city_id = %s::int)
                ORDER BY GREATEST(similarity(k.title, %s), similarity(k.title, %s)) DESC
                LIMIT %s;
                """
                cur.execute(kc_query, (query_text, content_query, city_id, city_id, query_text, content_query, limit))
                for row in cur.fetchall():
                    c = dict(row)
                    existing = next((x for x in candidates if x.get("id") == c.get("id") and x.get("entity_type") == "POI"), None)
                    if existing:
                        existing["trigram_sim"] = max(float(existing.get("trigram_sim") or 0.0), float(c.get("trigram_sim") or 0.0))
                    else:
                        candidates.append(c)

            conn.close()
        except Exception as e:
            # Fallback for transient DB issue
            pass

        return candidates

    @staticmethod
    def resolve_candidate(
        requested_name: str,
        candidates: List[Dict[str, Any]],
        location_hint: Optional[str] = None,
        category_intent: Optional[str] = None,
        target_lat: Optional[float] = None,
        target_lon: Optional[float] = None
    ) -> Tuple[Optional[Dict[str, Any]], float, List[Dict[str, Any]]]:
        """
        Evaluates candidate places against the requested entity.
        Returns: (top_match, confidence, ambiguity_alternatives)
        """
        if not candidates:
            return None, 0.0, []

        norm_req = normalize_name(requested_name)
        STOPWORDS = {"the", "a", "an", "is", "are", "tell", "me", "about", "what", "where", "which", "place", "has", "can", "see", "find", "how", "reach", "to", "in", "at", "near", "around", "of"}
        salient_req_tokens = {t for t in norm_req.split() if t not in STOPWORDS}
        if not salient_req_tokens:
            salient_req_tokens = set(norm_req.split())

        scored_candidates = []
        for cand in candidates:
            cand_name = cand.get("name") or cand.get("title") or ""
            norm_cand = normalize_name(cand_name)
            cand_tokens = set(norm_cand.split())
            salient_cand_tokens = {t for t in cand_tokens if t not in STOPWORDS}

            cand_desc = f"{cand.get('short_desc') or ''} {cand.get('full_desc') or ''} {cand.get('tag_badge') or ''}"
            cand_desc_tokens = {t for t in normalize_name(cand_desc).split() if t not in STOPWORDS}

            # 1. Lexical / Token Match Score [0.0 - 0.50]
            if norm_req == norm_cand:
                name_score = 0.50
            elif " ".join(sorted(salient_req_tokens)) == " ".join(sorted(salient_cand_tokens)) and salient_cand_tokens:
                name_score = 0.48
            else:
                intersection = salient_req_tokens.intersection(salient_cand_tokens)
                desc_intersection = salient_req_tokens.intersection(cand_desc_tokens)
                if intersection:
                    # Recall of query tokens covered by candidate + precision
                    q_cov = len(intersection) / len(salient_req_tokens)
                    c_cov = len(intersection) / len(salient_cand_tokens) if salient_cand_tokens else 0.0
                    f1 = (2 * q_cov * c_cov) / (q_cov + c_cov) if (q_cov + c_cov) > 0 else 0.0
                    trigram_sim = float(cand.get("trigram_sim") or 0.0)
                    name_score = max(f1 * 0.45, q_cov * 0.40, trigram_sim * 0.40)
                elif desc_intersection:
                    # Feature / landmark description match (e.g. musical pillars in Vittala description)
                    d_cov = len(desc_intersection) / len(salient_req_tokens)
                    trigram_sim = float(cand.get("trigram_sim") or 0.0)
                    name_score = max(d_cov * 0.38, trigram_sim * 0.38)
                else:
                    trigram_sim = float(cand.get("trigram_sim") or 0.0)
                    name_score = trigram_sim * 0.35

            # Distinct entity penalty:
            # If user explicitly requested "hotel" but candidate is named "delite" or "corner" without "hotel"
            if "hotel" in salient_req_tokens and "hotel" not in cand_tokens:
                if any(distinct_suffix in cand_tokens for distinct_suffix in ["delite", "corner", "residency", "darshini"]):
                    name_score *= 0.50

            # 2. Location Match Score [0.0 - 0.25]
            loc_score = 0.0
            cand_addr = (cand.get("address") or cand.get("short_desc") or "").lower()
            if location_hint:
                norm_hint = normalize_name(location_hint)
                if norm_hint in cand_addr or norm_hint in cand_name.lower():
                    loc_score = 0.25
                elif any(t in cand_addr for t in norm_hint.split()):
                    loc_score = 0.15

            if target_lat is not None and target_lon is not None and cand.get("latitude") and cand.get("longitude"):
                dist_m = haversine_distance(target_lat, target_lon, cand["latitude"], cand["longitude"])
                if dist_m < 500:
                    loc_score = max(loc_score, 0.25)
                elif dist_m < 1500:
                    loc_score = max(loc_score, 0.20)
                elif dist_m < 5000:
                    loc_score = max(loc_score, 0.10)

            # 3. Category Match Score [0.0 - 0.15]
            cat_score = 0.10
            cand_cat = (cand.get("category") or "").lower()
            if category_intent:
                if category_intent.lower() in cand_cat:
                    cat_score = 0.15
                elif category_intent == "RESTAURANT" and any(k in cand_cat for k in ["food", "eatery", "cafe", "restaurant", "darshini"]):
                    cat_score = 0.15
                elif category_intent == "ACCOMMODATION" and any(k in cand_cat for k in ["hotel", "lodge", "stay", "guest_house"]):
                    cat_score = 0.15
                elif category_intent == "TEMPLE" and any(k in cand_cat for k in ["worship", "temple", "shrine"]):
                    cat_score = 0.15
                else:
                    cat_score = 0.0

            # 4. Source / Verification Confidence [0.0 - 0.10]
            src_score = 0.10 if cand.get("verified", True) else 0.05

            total_confidence = round(name_score + loc_score + cat_score + src_score, 3)
            cand_copy = dict(cand)
            cand_copy["resolution_confidence"] = total_confidence
            scored_candidates.append(cand_copy)

        scored_candidates.sort(key=lambda x: x["resolution_confidence"], reverse=True)
        top = scored_candidates[0]

        # Check for ambiguity: if top two have very close scores and neither is an exact match
        alternatives = []
        if len(scored_candidates) > 1:
            second = scored_candidates[1]
            if top["resolution_confidence"] - second["resolution_confidence"] < 0.08 and second["resolution_confidence"] >= 0.45:
                alternatives = scored_candidates[:3]

        return top, top["resolution_confidence"], alternatives

    @staticmethod
    def is_exact_match(requested_name: str, candidate_name: str) -> bool:
        """Determines if candidate name is an exact or near-exact match to requested name."""
        norm_req = normalize_name(requested_name)
        norm_cand = normalize_name(candidate_name)
        if norm_req == norm_cand:
            return True
        req_clean = re.sub(r'\b(restaurant|hotel|cafe|temple|bengaluru|bangalore)\b', '', norm_req).strip()
        cand_clean = re.sub(r'\b(restaurant|hotel|cafe|temple|bengaluru|bangalore)\b', '', norm_cand).strip()
        return bool(req_clean and req_clean == cand_clean)
