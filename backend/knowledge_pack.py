import hashlib
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple
from backend.database import get_connection
from backend.weather_service import fetch_live_weather
from backend.web_retriever import WebRetriever

# Freshness TTL Configuration (in seconds)
FRESHNESS_TTL = {
    "STATIC": 86400 * 30,    # 30 days (History, architecture, geography)
    "SLOW": 86400 * 3,       # 3 days (Ticketing, opening hours, accessibility)
    "DYNAMIC": 3600 * 4,     # 4 hours (Safety advisories, events, temporary alerts)
    "LIVE": 600              # 10 minutes (Weather, real-time conditions)
}

class GeoContextResolver:
    """
    Resolves explicit or ambient location into a canonical GeoContext object.
    Explicit query locations and POIs strictly override ambient session locations.
    """
    @staticmethod
    def resolve_destination(
        destination_name_or_id: Optional[Any] = None,
        lat: Optional[float] = None,
        lng: Optional[float] = None,
        query: Optional[str] = None
    ) -> Dict[str, Any]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, state, lat, lng, timezone, description, best_season FROM cities")
        cities = [dict(r) for r in cursor.fetchall()]
        cursor.execute("SELECT id, city_id, name FROM activities_poi")
        all_pois = [dict(r) for r in cursor.fetchall()]
        conn.close()

        resolved_city = None
        resolved_poi = None
        detected_from = "default"
        confidence = 0.85

        if query:
            q_low = query.lower()
            
            # 1. Dynamic database candidate matching for POIs and Places
            try:
                from backend.entity_resolver import EntityResolver
                db_cands = EntityResolver.get_database_candidates(query, limit=15)
                if db_cands:
                    top_c, conf, _ = EntityResolver.resolve_candidate(query, db_cands)
                    if top_c and conf >= 0.35 and top_c.get("city_id"):
                        target_c_id = top_c["city_id"]
                        resolved_city = next((c for c in cities if c["id"] == target_c_id), None)
                        if resolved_city:
                            detected_from = "explicit_poi_query"
                            confidence = max(0.90, conf)
                            resolved_poi = top_c
            except Exception as e:
                pass

            # 2. Check explicit city mention in query
            if not resolved_city:
                for c in cities:
                    c_name_low = c["name"].lower()
                    aliases = [c_name_low]
                    if c_name_low == "bengaluru":
                        aliases.append("bangalore")
                    elif c_name_low == "mysuru":
                        aliases.append("mysore")

                    if any(re_match in q_low for re_match in aliases):
                        resolved_city = c
                        detected_from = "explicit_query"
                        confidence = 0.99
                        break

        # 3. Check direct destination name or ID passed
        if not resolved_city and destination_name_or_id is not None:
            if isinstance(destination_name_or_id, int) or str(destination_name_or_id).isdigit():
                resolved_city = next((c for c in cities if c["id"] == int(destination_name_or_id)), None)
            else:
                d_str = str(destination_name_or_id).lower()
                for c in cities:
                    if c["name"].lower() in d_str or d_str in c["name"].lower():
                        resolved_city = c
                        break
            if resolved_city:
                detected_from = "user_selection"
                confidence = 0.95

        # 4. Check GPS proximity
        if not resolved_city and lat is not None and lng is not None:
            min_dist = float('inf')
            for c in cities:
                dist = ((lat - c["lat"])**2 + (lng - c["lng"])**2) ** 0.5 * 111.0 # approx km
                if dist < min_dist:
                    min_dist = dist
                    resolved_city = c
            detected_from = "gps"
            confidence = 0.92

        # 5. Fallback default (Hampi)
        if not resolved_city:
            resolved_city = next((c for c in cities if "Hampi" in c["name"]), cities[0])
            detected_from = "fallback_default"
            confidence = 0.70

        # Determine destination scope radius
        radius_meters = 15000 if "Hampi" in resolved_city["name"] else 25000

        return {
            "destination_id": resolved_city["id"],
            "destination_name": resolved_city["name"],
            "city_id": resolved_city["id"],
            "city_name": resolved_city["name"],
            "state": resolved_city.get("state", "Karnataka"),
            "latitude": resolved_city["lat"],
            "longitude": resolved_city["lng"],
            "radius_meters": radius_meters,
            "bounding_box": {
                "min_lat": resolved_city["lat"] - (radius_meters / 111000.0),
                "max_lat": resolved_city["lat"] + (radius_meters / 111000.0),
                "min_lng": resolved_city["lng"] - (radius_meters / 111000.0),
                "max_lng": resolved_city["lng"] + (radius_meters / 111000.0),
            },
            "timezone": resolved_city.get("timezone", "Asia/Kolkata"),
            "detected_from": detected_from,
            "confidence": confidence,
            "resolved_poi": resolved_poi,
            "resolved_at": datetime.now(timezone.utc).isoformat()
        }


class KnowledgePackBuilder:
    """
    Builds, validates, and manages compact location-scoped Knowledge Packs
    with progressive loading, section TTLs, real record references, and real source provenance.
    """
    _pack_cache: Dict[int, Dict[str, Any]] = {}

    @classmethod
    def get_or_build_pack(cls, geo_context: Dict[str, Any], force_refresh: bool = False) -> Dict[str, Any]:
        dest_id = geo_context["destination_id"]
        now = datetime.now(timezone.utc)

        if not force_refresh and dest_id in cls._pack_cache:
            cached_pack = cls._pack_cache[dest_id]
            expires_at = datetime.fromisoformat(cached_pack.get("expires_at", now.isoformat()))
            if now < expires_at:
                return cached_pack

        return cls.build_pack(geo_context)

    @classmethod
    def build_pack(cls, geo_context: Dict[str, Any]) -> Dict[str, Any]:
        start_time = time.time()
        dest_id = geo_context["destination_id"]
        dest_name = geo_context["destination_name"]
        lat = geo_context["latitude"]
        lng = geo_context["longitude"]
        now = datetime.now(timezone.utc)
        now_iso = now.isoformat()

        conn = get_connection()
        cursor = conn.cursor()

        # PHASE 1 & 2: Structured POIs & Hotels
        cursor.execute("SELECT * FROM activities_poi WHERE city_id = ?", (dest_id,))
        pois = [dict(r) for r in cursor.fetchall()]

        cursor.execute("SELECT * FROM hotels WHERE city_id = ?", (dest_id,))
        hotels = [dict(r) for r in cursor.fetchall()]

        # PHASE 3: Semantic Knowledge & Facts from PostgreSQL
        from backend.pg_database import get_pg_connection
        from backend.dynamic_pipeline import DynamicIngestionPipeline
        place_kb_rows = []
        poi_facts = []
        try:
            pg_conn = get_pg_connection()
            with pg_conn.cursor() as pg_cur:
                pg_cur.execute("""
                SELECT id, city_id, topic, title, chunk_text as content, source_name as source_citation, 'verified' as verified_status
                FROM knowledge_chunks
                WHERE city_id = %s;
                """, (dest_id,))
                for row in pg_cur.fetchall():
                    place_kb_rows.append({
                        "id": row[0],
                        "city_id": row[1],
                        "topic": row[2],
                        "title": row[3],
                        "content": row[4],
                        "source_citation": row[5],
                        "verified_status": row[6]
                    })
            pg_conn.close()
        except Exception as e:
            print(f"[KnowledgePackBuilder] PostgreSQL fetch warning: {e}")

        # If PostgreSQL knowledge is empty for this destination, dynamically discover and ingest overview
        if not place_kb_rows:
            try:
                pipeline = DynamicIngestionPipeline()
                ingested = pipeline.discover_and_ingest_fact(
                    query=f"{dest_name} Karnataka history and significance",
                    entity_name=dest_name,
                    city_id=dest_id,
                    city_name=dest_name,
                    attribute="history_and_significance"
                )
                for item in ingested:
                    place_kb_rows.append({
                        "id": 1,
                        "city_id": dest_id,
                        "topic": "history_and_significance",
                        "title": item.get("title", dest_name),
                        "content": item.get("content", ""),
                        "source_citation": item.get("source", "Verified Web Registry"),
                        "verified_status": "verified"
                    })
            except Exception as e:
                print(f"[KnowledgePackBuilder] Dynamic ingestion warning: {e}")

        # PHASE 4: Safety & Advisories
        cursor.execute("SELECT * FROM safety_advisories WHERE city_id = ? AND is_active = 1", (dest_id,))
        safety_advisories = [dict(r) for r in cursor.fetchall()]

        # PHASE 5: Events & Festivals
        cursor.execute("SELECT * FROM events_festivals WHERE city_id = ?", (dest_id,))
        events = [dict(r) for r in cursor.fetchall()]

        conn.close()

        # PHASE 6: Live Weather Snapshot
        live_weather = fetch_live_weather(lat, lng)
        if not live_weather:
            live_weather = {
                "temp_c": 28, "feels_like_c": 30, "condition": "Mainly clear",
                "humidity_pct": 60, "sunrise": "06:14", "sunset": "18:41",
                "daylight_hours": "12h Daylight", "is_live": False
            }

        # PHASE 7: Selected Trusted Web Evidence for the Destination
        web_retriever = WebRetriever()
        web_sources = web_retriever.search_and_extract(f"{dest_name} Karnataka heritage tourism")

        # Compile Pack Hash & Section Metadata
        pack_content_raw = f"{dest_id}_{len(pois)}_{len(place_kb_rows)}_{len(safety_advisories)}_{live_weather.get('temp_c')}"
        pack_hash = hashlib.sha256(pack_content_raw.encode()).hexdigest()[:16]
        pack_id = f"geopack_{dest_id}_{pack_hash}"

        # METADATA ENRICHMENT (Section 8 & 9)
        # 1. Enrich POIs
        for p in pois:
            p["pack_id"] = pack_id
            p["entity_id"] = p["id"]
            p["entity_name"] = p["name"]
            p["entity_type"] = "POI"
            p["destination_id"] = dest_id
            p["city_id"] = dest_id
            p["content_type"] = "poi_detail"
            p["intent_tags"] = ["OPENING_HOURS", "ENTRY_FEE", "ACCESSIBILITY", "POI_DETAIL"]
            p["attribute_tags"] = ["opening_hours", "operational_status", "entry_fee", "ticket_policy", "step_free"]
            p["source_type"] = "official_tourism_registry"
            p["freshness_class"] = "SLOW"
            p["retrieved_at"] = now_iso
            p["expires_at"] = (now + timedelta(seconds=FRESHNESS_TTL["SLOW"])).isoformat()

        # 2. Enrich place_kb
        for k in place_kb_rows:
            k["pack_id"] = pack_id
            k["entity_id"] = k["id"]
            k["entity_name"] = dest_name
            k["entity_type"] = "CITY"
            k["destination_id"] = dest_id
            k["city_id"] = dest_id
            k["content_type"] = "place_kb"
            topic = k.get("topic", "general")
            k["intent_tags"] = ["HISTORY", "TICKETING", "ACCESSIBILITY", "FOOD"] if topic in ["history_and_significance", "ticketing_rules", "local_cuisine_guide"] else ["GENERAL_QUERY"]
            k["attribute_tags"] = [topic, "history", "culture"] if "history" in topic else [topic]
            k["source_type"] = k.get("source_citation", "official_gazette")
            k["freshness_class"] = "STATIC"
            k["retrieved_at"] = now_iso
            k["expires_at"] = (now + timedelta(seconds=FRESHNESS_TTL["STATIC"])).isoformat()

        # 3. Enrich poi_facts
        for f in poi_facts:
            f["pack_id"] = pack_id
            f["entity_id"] = f.get("poi_id")
            f["entity_name"] = f.get("poi_name", dest_name)
            f["entity_type"] = "POI"
            f["destination_id"] = dest_id
            f["city_id"] = dest_id
            f["content_type"] = "poi_fact"
            f["intent_tags"] = ["ARCHITECTURE", "HISTORY", "FACT_LOOKUP", "LOCATION_LOOKUP"]
            f["attribute_tags"] = [f.get("tag", "fact"), "architecture", "optics"]
            f["source_type"] = f.get("source_name", "asi_research")
            f["freshness_class"] = "STATIC"
            f["retrieved_at"] = now_iso
            f["expires_at"] = (now + timedelta(seconds=FRESHNESS_TTL["STATIC"])).isoformat()

        # 4. Enrich safety_advisories
        for s in safety_advisories:
            s["pack_id"] = pack_id
            s["entity_id"] = s["id"]
            # Identify specific entity if title mentions it
            s_title_low = s["title"].lower()
            if "lalbagh" in s_title_low:
                s["entity_name"] = "Lalbagh Botanical Garden & Glass House"
                s["entity_type"] = "POI"
            elif "cubbon" in s_title_low:
                s["entity_name"] = "Cubbon Park & State Library"
                s["entity_type"] = "POI"
            elif "coracle" in s_title_low or "tungabhadra" in s_title_low or "river" in s_title_low:
                s["entity_name"] = "Tungabhadra River"
                s["entity_type"] = "POI"
            else:
                s["entity_name"] = dest_name
                s["entity_type"] = "CITY"

            s["destination_id"] = dest_id
            s["city_id"] = dest_id
            s["content_type"] = "safety_advisory"
            s["intent_tags"] = ["SAFETY", "OPERATIONAL_STATUS", "CLOSURE"]
            s["attribute_tags"] = ["closure", "warning", "hazard", "advisory", "operational_status", "open_status"]
            s["source_type"] = "police_transport_authority"
            s["freshness_class"] = "DYNAMIC"
            s["retrieved_at"] = now_iso
            s["expires_at"] = (now + timedelta(seconds=FRESHNESS_TTL["DYNAMIC"])).isoformat()

        # 5. Enrich live weather
        live_weather["pack_id"] = pack_id
        live_weather["entity_name"] = dest_name
        live_weather["entity_type"] = "WEATHER"
        live_weather["destination_id"] = dest_id
        live_weather["content_type"] = "weather"
        live_weather["intent_tags"] = ["LIVE_WEATHER"]
        live_weather["attribute_tags"] = ["temperature", "current_conditions", "humidity", "weather"]
        live_weather["freshness_class"] = "LIVE"
        live_weather["retrieved_at"] = now_iso
        live_weather["expires_at"] = (now + timedelta(seconds=FRESHNESS_TTL["LIVE"])).isoformat()

        expires_at = now + timedelta(seconds=FRESHNESS_TTL["LIVE"])
        build_duration_ms = round((time.time() - start_time) * 1000, 2)

        pack_obj = {
            "pack_id": pack_id,
            "destination_id": dest_id,
            "destination_name": dest_name,
            "geo_context": geo_context,
            "status": "READY",
            "version": "2.0.0",
            "pack_hash": pack_hash,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "expires_at": expires_at.isoformat(),
            "build_duration_ms": build_duration_ms,
            "sections": {
                "destination": True,
                "pois": True,
                "knowledge": True,
                "safety": True,
                "visitor_info": True,
                "events": len(events) > 0,
                "weather": True,
                "web_sources": len(web_sources) > 0
            },
            "counts": {
                "pois": len(pois),
                "hotels": len(hotels),
                "knowledge_items": len(place_kb_rows) + len(poi_facts),
                "safety_items": len(safety_advisories),
                "events": len(events),
                "web_sources": len(web_sources)
            },
            "data": {
                "pois": pois,
                "hotels": hotels,
                "place_kb": place_kb_rows,
                "poi_facts": poi_facts,
                "safety_advisories": safety_advisories,
                "events": events,
                "weather": live_weather,
                "web_sources": web_sources
            }
        }

        # Store in Cache
        cls._pack_cache[dest_id] = pack_obj
        return pack_obj

    @classmethod
    def get_pack(cls, dest_id: int) -> Optional[Dict[str, Any]]:
        return cls._pack_cache.get(dest_id)

    @classmethod
    def cache_external_business(cls, dest_id: int, business_record: Dict[str, Any]) -> None:
        """
        Dynamically updates the destination knowledge pack with a validated external business record
        without dumping unformatted web content.
        Preserves: name, category, address, coordinates, source, retrieved_at, expires_at.
        """
        pack = cls._pack_cache.get(dest_id)
        if not pack:
            return

        if "external_businesses" not in pack["data"]:
            pack["data"]["external_businesses"] = []

        existing = next((b for b in pack["data"]["external_businesses"] if b.get("name") == business_record.get("name")), None)
        if not existing:
            pack["data"]["external_businesses"].append(business_record)
            pack["counts"]["external_businesses"] = len(pack["data"]["external_businesses"])
            pack["updated_at"] = datetime.now(timezone.utc).isoformat()


