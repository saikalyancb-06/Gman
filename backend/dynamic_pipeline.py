import urllib.request
import urllib.parse
import json
import re
import hashlib
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from backend.pg_database import get_pg_connection

class DynamicIngestionPipeline:
    """
    Dynamic Discovery, Fetch, Normalization, Entity Resolution,
    Deduplication, Chunking, and PostgreSQL Persistence Pipeline.
    
    Adheres strictly to:
    - Real source metadata (source_name, source_url, authority, retrieved_at)
    - Dynamic place & business discovery (OpenStreetMap Nominatim)
    - Dynamic institutional facts (Wikipedia API / Open Data)
    - Normalized relational schema (entities, sources, documents, chunks, embeddings, cache)
    - Deduplication via content_hash & cache_key
    - Zero hardcoded factual knowledge
    """
    def __init__(self):
        pass

    def check_web_cache(self, cache_key: str) -> Optional[List[Dict[str, Any]]]:
        conn = get_pg_connection()
        with conn.cursor() as cur:
            cur.execute("""
            SELECT payload_json, expires_at 
            FROM web_cache 
            WHERE cache_key = %s AND expires_at > CURRENT_TIMESTAMP;
            """, (cache_key,))
            row = cur.fetchone()
        conn.close()
        if row:
            return row[0]
        return None

    def store_web_cache(self, cache_key: str, query: str, payload: List[Dict[str, Any]], entity_name: str = "", destination_name: str = "", ttl_hours: int = 72, source_name: str = ""):
        expires_at = datetime.now(timezone.utc) + timedelta(hours=ttl_hours)
        conn = get_pg_connection()
        with conn.cursor() as cur:
            cur.execute("""
            INSERT INTO web_cache (cache_key, query, entity_name, destination_name, payload_json, source_name, expires_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (cache_key) DO UPDATE SET payload_json = EXCLUDED.payload_json, expires_at = EXCLUDED.expires_at, retrieved_at = CURRENT_TIMESTAMP;
            """, (cache_key, query, entity_name, destination_name, json.dumps(payload), source_name, expires_at))
        conn.close()

    def discover_and_ingest_fact(
        self,
        query: str,
        entity_name: str,
        city_id: Optional[int] = None,
        city_name: str = "Bengaluru",
        attribute: str = "GENERAL"
    ) -> List[Dict[str, Any]]:
        """
        Dynamically searches external sources, parses, deduplicates,
        stores in PostgreSQL, and generates semantic chunks.
        """
        cache_key = f"fact::{query.lower().strip()}::{city_name.lower()}"
        cached = self.check_web_cache(cache_key)
        if cached:
            return cached

        evidence_list = []
        now = datetime.now(timezone.utc)

        # 1. Wikipedia Institutional Summary API
        try:
            target_topic = entity_name or city_name
            # If population query, ensure the entity is the city
            if attribute == "POPULATION" and city_name:
                target_topic = city_name

            url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(target_topic)}"
            req = urllib.request.Request(url, headers={'User-Agent': 'GeoGuide-Dynamic-Companion/2.0 (contact@geoguide.ai)'})
            with urllib.request.urlopen(req, timeout=4) as response:
                data = json.loads(response.read().decode('utf-8'))
                extract = data.get('extract')
                title = data.get('title', target_topic.title())
                page_url = data.get('content_urls', {}).get('desktop', {}).get('page', f"https://en.wikipedia.org/wiki/{urllib.parse.quote(target_topic)}")
                
                if extract:
                    evidence_list.append({
                        "source": f"Wikipedia Institutional Knowledge ({title})",
                        "source_url": page_url,
                        "source_type": "institutional_encyclopedia",
                        "title": title,
                        "content": extract,
                        "retrieved_at": now.isoformat(),
                        "verified": True,
                        "confidence": 0.95
                    })
        except Exception:
            pass

        # 2. DuckDuckGo Instant Answer API Fallback
        if not evidence_list:
            try:
                ddg_url = f"https://api.duckduckgo.com/?q={urllib.parse.quote(query)}&format=json&no_html=1&skip_disambig=1"
                req2 = urllib.request.Request(ddg_url, headers={'User-Agent': 'GeoGuide-Dynamic-Companion/2.0'})
                with urllib.request.urlopen(req2, timeout=4) as response2:
                    ddg_data = json.loads(response2.read().decode('utf-8'))
                    abstract = ddg_data.get('AbstractText') or ddg_data.get('Answer')
                    if abstract:
                        evidence_list.append({
                            "source": ddg_data.get('AbstractSource', 'Verified Web Registry'),
                            "source_url": ddg_data.get('AbstractURL', 'https://duckduckgo.com'),
                            "source_type": "web_registry",
                            "title": ddg_data.get('Heading', query),
                            "content": abstract,
                            "retrieved_at": now.isoformat(),
                            "verified": True,
                            "confidence": 0.88
                        })
            except Exception:
                pass

        if evidence_list:
            # Persist into PostgreSQL Knowledge Tables
            self._persist_knowledge_items(evidence_list, city_id=city_id, city_name=city_name, attribute=attribute, entity_name=entity_name)
            self.store_web_cache(cache_key, query, evidence_list, entity_name=entity_name, destination_name=city_name, ttl_hours=72, source_name="External Web Discovery")

        return evidence_list

    def discover_and_ingest_local_business(
        self,
        query: str,
        entity_name: Optional[str] = None,
        location_hint: Optional[str] = None,
        destination_name: str = "Bengaluru",
        city_id: Optional[int] = 2,
        category_intent: Optional[str] = None,
        max_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Dynamically retrieves local places & businesses via OpenStreetMap Nominatim.
        Enforces Indian context ("Hotel" disambiguation between restaurant vs stay).
        Normalizes, deduplicates, and stores into PostgreSQL entities & knowledge_chunks.
        """
        cache_key = f"local::{query.lower().strip()}::{str(location_hint).lower()}::{destination_name.lower()}::{str(category_intent).lower()}"
        cached = self.check_web_cache(cache_key)
        if cached:
            return cached

        # Construct targeted queries
        query_terms = []
        if entity_name:
            query_terms.append(entity_name)
        elif category_intent:
            query_terms.append(category_intent.lower())
        else:
            query_terms.append(query)

        if location_hint and location_hint.lower() not in " ".join(query_terms).lower():
            query_terms.append(location_hint)

        if destination_name and destination_name.lower() not in " ".join(query_terms).lower():
            query_terms.append(destination_name)

        targeted_search_str = " ".join(query_terms)
        raw_results = self._query_nominatim(targeted_search_str)

        # Fallback queries
        if not raw_results and entity_name and location_hint:
            raw_results = self._query_nominatim(f"{entity_name} {location_hint}")
        if not raw_results and entity_name:
            raw_results = self._query_nominatim(f"{entity_name} {destination_name}")
        if not raw_results and category_intent and location_hint:
            raw_results = self._query_nominatim(f"{category_intent} {location_hint} {destination_name}")

        normalized_records = []
        seen_names = set()
        now = datetime.now(timezone.utc)

        for item in raw_results:
            name = item.get("name") or item.get("display_name", "").split(",")[0]
            if not name or name in seen_names:
                continue

            address_info = item.get("address", {})
            osm_class = item.get("class", "")
            osm_type = item.get("type", "")

            is_lodging = osm_class in ["tourism", "building"] and osm_type in ["hotel", "motel", "guest_house", "hostel", "apartment"]
            is_restaurant = osm_class in ["amenity"] and osm_type in ["restaurant", "cafe", "fast_food", "food_court"]

            if category_intent == "ACCOMMODATION" and is_restaurant and not is_lodging:
                continue
            if category_intent == "RESTAURANT" and is_lodging and not is_restaurant:
                continue

            resolved_category = "Hotel / Accommodation" if is_lodging else ("Restaurant / Eatery" if is_restaurant else f"{osm_class} ({osm_type})")

            addr_parts = []
            for k in ["amenity", "house_number", "road", "neighbourhood", "suburb", "city_district", "city", "postcode"]:
                v = address_info.get(k)
                if v and v not in addr_parts:
                    addr_parts.append(v)
            address_str = ", ".join(addr_parts) if addr_parts else item.get("display_name", "")

            source_url = f"https://www.openstreetmap.org/{item.get('osm_type', 'node')}/{item.get('osm_id', '')}"
            lat = float(item.get("lat", 0.0))
            lon = float(item.get("lon", 0.0))
            confidence = round(float(item.get("importance", 0.75)), 2)

            record = {
                "name": name,
                "category": resolved_category,
                "is_lodging": is_lodging,
                "is_restaurant": is_restaurant,
                "address": address_str,
                "latitude": lat,
                "longitude": lon,
                "source": "OpenStreetMap Local Places Registry",
                "source_url": source_url,
                "retrieved_at": now.isoformat(),
                "expires_at": (now + timedelta(days=30)).isoformat(),
                "freshness": "SLOW",
                "confidence": confidence,
                "osm_type": osm_type,
                "osm_class": osm_class
            }
            normalized_records.append(record)
            seen_names.add(name)
            if len(normalized_records) >= max_results:
                break

        if normalized_records:
            # Persist entities and chunks in PostgreSQL
            self._persist_local_business_items(normalized_records, city_id=city_id, destination_name=destination_name)
            self.store_web_cache(cache_key, query, normalized_records, entity_name=entity_name or "", destination_name=destination_name, ttl_hours=240, source_name="OpenStreetMap Local Places")

        return normalized_records

    def _query_nominatim(self, search_str: str) -> List[Dict[str, Any]]:
        try:
            url = f"https://nominatim.openstreetmap.org/search?q={urllib.parse.quote(search_str)}&format=json&addressdetails=1&limit=8"
            req = urllib.request.Request(url, headers={'User-Agent': 'GeoGuide-Dynamic-Companion/2.0 (contact@geoguide.ai)'})
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                if isinstance(data, list):
                    return data
        except Exception:
            pass
        return []

    def _persist_knowledge_items(self, items: List[Dict[str, Any]], city_id: Optional[int], city_name: str, attribute: str, entity_name: str):
        from backend.vector_store import PgVectorStore
        vector_store = PgVectorStore()
        conn = get_pg_connection()

        for item in items:
            raw_content = item["content"]
            c_hash = hashlib.sha256(raw_content.encode('utf-8')).hexdigest()
            title = item.get("title", entity_name or city_name)
            source_name = item.get("source", "Verified Web Registry")
            source_url = item.get("source_url", "")
            source_type = item.get("source_type", "web_registry")

            with conn.cursor() as cur:
                # 1. Insert source
                cur.execute("""
                INSERT INTO knowledge_sources (source_name, source_url, source_type, authority_score, verification_state)
                VALUES (%s, %s, %s, %s, 'VERIFIED')
                RETURNING id;
                """, (source_name, source_url, source_type, item.get("confidence", 0.90)))
                source_id = cur.fetchone()[0]

                # 2. Insert entity if not exists
                cur.execute("SELECT id FROM entities WHERE name = %s AND (city_name = %s OR city_id = %s)", (title, city_name, city_id))
                ent_row = cur.fetchone()
                if ent_row:
                    entity_id = ent_row[0]
                else:
                    cur.execute("""
                    INSERT INTO entities (name, entity_type, city_id, city_name, source_url)
                    VALUES (%s, 'CONCEPT', %s, %s, %s)
                    RETURNING id;
                    """, (title, city_id, city_name, source_url))
                    entity_id = cur.fetchone()[0]

                # 3. Insert document (deduplicated by content_hash)
                cur.execute("""
                INSERT INTO knowledge_documents (source_id, entity_id, city_id, title, raw_content, content_hash, content_type)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (content_hash) DO NOTHING
                RETURNING id;
                """, (source_id, entity_id, city_id, title, raw_content, c_hash, attribute))
                doc_row = cur.fetchone()
                doc_id = doc_row[0] if doc_row else None

            # 4. Insert Semantic Chunk into pgvector / PostgreSQL
            vector_store.insert_chunk(
                document_id=doc_id,
                entity_id=entity_id,
                city_id=city_id,
                topic=attribute.lower(),
                attribute=attribute,
                title=title,
                chunk_text=raw_content,
                source_name=source_name,
                source_url=source_url,
                source_type=source_type,
                freshness_class="STATIC" if attribute == "POPULATION" else "SLOW",
                confidence=item.get("confidence", 0.90)
            )

        conn.close()

    def _persist_local_business_items(self, items: List[Dict[str, Any]], city_id: Optional[int], destination_name: str):
        from backend.vector_store import PgVectorStore
        vector_store = PgVectorStore()
        conn = get_pg_connection()

        for biz in items:
            name = biz["name"]
            addr = biz["address"]
            cat = biz["category"]
            lat = biz["latitude"]
            lng = biz["longitude"]
            src_url = biz.get("source_url", "")
            src_name = biz.get("source", "OpenStreetMap Local Places Registry")

            content = f"{name} is a {cat} located at {addr}."
            if lat and lng:
                content += f" Coordinates: {lat:.4f}, {lng:.4f}."
            c_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()

            with conn.cursor() as cur:
                # 1. Source
                cur.execute("""
                INSERT INTO knowledge_sources (source_name, source_url, source_type, authority_score, verification_state)
                VALUES (%s, %s, 'local_places_registry', %s, 'VERIFIED')
                RETURNING id;
                """, (src_name, src_url, biz.get("confidence", 0.85)))
                source_id = cur.fetchone()[0]

                # 2. Entity
                cur.execute("SELECT id FROM entities WHERE name = %s AND (city_name = %s OR city_id = %s)", (name, destination_name, city_id))
                ent_row = cur.fetchone()
                if ent_row:
                    entity_id = ent_row[0]
                else:
                    cur.execute("""
                    INSERT INTO entities (name, entity_type, city_id, city_name, latitude, longitude, category, address, source_url)
                    VALUES (%s, 'BUSINESS', %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id;
                    """, (name, city_id, destination_name, lat, lng, cat, addr, src_url))
                    entity_id = cur.fetchone()[0]

                # 3. Document
                cur.execute("""
                INSERT INTO knowledge_documents (source_id, entity_id, city_id, title, raw_content, content_hash, content_type)
                VALUES (%s, %s, %s, %s, %s, %s, 'local_business')
                ON CONFLICT (content_hash) DO NOTHING
                RETURNING id;
                """, (source_id, entity_id, city_id, name, content, c_hash))
                doc_row = cur.fetchone()
                doc_id = doc_row[0] if doc_row else None

            # 4. Semantic Chunk in PostgreSQL
            vector_store.insert_chunk(
                document_id=doc_id,
                entity_id=entity_id,
                city_id=city_id,
                topic="local_business",
                attribute="LOCAL_BUSINESS",
                title=name,
                chunk_text=content,
                source_name=src_name,
                source_url=src_url,
                source_type="local_places_registry",
                freshness_class="SLOW",
                confidence=biz.get("confidence", 0.85)
            )

        conn.close()
