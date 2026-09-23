import re
from typing import List, Dict, Any, Optional
from backend.geo_context import GeoContext
from backend.location_service import LocationService
from backend.dynamic_pipeline import DynamicIngestionPipeline
from backend.entity_resolver import EntityResolver

class LocalSearchService:
    """
    Dedicated Local Search & Nearby Recommendation Engine for GeoGuide.
    Features:
    - Coordinate-first spatial retrieval via PostGIS / earthdistance
    - Natural-language preference extraction (quietness, nature, food, budget)
    - Explainable recommendation synthesis
    - Dynamic external discovery when local data is missing
    - STRICT NO-GENERIC-CITY-FALLBACK invariant
    """
    def __init__(self):
        self.pipeline = DynamicIngestionPipeline()

    @staticmethod
    def extract_search_preferences(query: str) -> Dict[str, Any]:
        """Extracts spatial, atmospheric, and activity preferences from natural language query."""
        q_low = query.lower()
        prefs = {
            "is_quiet_relaxation": False,
            "is_food": False,
            "is_nature": False,
            "is_heritage": False,
            "category_intent": None,
            "requested_radius_m": 5000,
            "step_free_preferred": False
        }

        # Radius mentions
        rad_match = re.search(r'within\s+(\d+)\s*(km|meter|m)', q_low)
        if rad_match:
            val = int(rad_match.group(1))
            unit = rad_match.group(2)
            prefs["requested_radius_m"] = val * 1000 if "km" in unit else val
        elif "walking distance" in q_low or "walk" in q_low:
            prefs["requested_radius_m"] = 1200

        # Quiet / Relaxing / Peaceful
        if any(w in q_low for w in ["quiet", "relax", "relaxing", "peaceful", "calm", "serene", "chill", "unwind", "tranquil"]):
            prefs["is_quiet_relaxation"] = True
            prefs["is_nature"] = True

        # Food & Dining
        if any(w in q_low for w in ["restaurant", "food", "eat", "cafe", "coffee", "darshini", "lunch", "dinner", "breakfast"]):
            prefs["is_food"] = True
            prefs["category_intent"] = "RESTAURANT"

        # Stays & Lodging
        if any(w in q_low for w in ["hotel", "lodge", "stay", "accommodation", "guesthouse"]):
            if not prefs["is_food"]:
                prefs["category_intent"] = "ACCOMMODATION"

        # Temples / Worship
        if any(w in q_low for w in ["temple", "worship", "pooja", "deity"]):
            prefs["category_intent"] = "TEMPLE"
            prefs["is_heritage"] = True

        if any(w in q_low for w in ["wheelchair", "step-free", "accessible", "flat"]):
            prefs["step_free_preferred"] = True

        return prefs

    def execute_nearby_recommendation(
        self,
        query: str,
        geo_ctx: GeoContext,
        top_k: int = 4
    ) -> Dict[str, Any]:
        """
        Executes a true proximity recommendation:
        1. Validates device coordinates
        2. Queries PostGIS / earthdistance within adaptive radius
        3. Scores candidates against extracted preferences
        4. Synthesizes explainable recommendations
        5. NEVER falls back to city overview
        """
        # Fall back to destination coordinates with an advisory note if GPS coordinates are unavailable or imprecise
        lat = geo_ctx.latitude
        lon = geo_ctx.longitude
        prefs = self.extract_search_preferences(query)
        radius_m = prefs["requested_radius_m"]
        is_fallback_location = not geo_ctx.is_precise()


        # 1. Retrieve nearby places via PostGIS spatial search
        nearby_candidates = LocationService.search_nearby_places(
            lat=lat,
            lon=lon,
            max_radius_m=radius_m,
            limit=12
        )

        # 2. Score candidates based on query preferences
        scored = []
        for p in nearby_candidates:
            score = 1.0 - (p["distance_m"] / float(radius_m * 1.5))
            reasons = [f"{int(p['distance_m'])} m away (~{p['walk_time_mins']} min walk)"]

            text_corpus = (p.get("name", "") + " " + p.get("short_desc", "") + " " + p.get("tag_badge", "")).lower()

            if prefs["is_quiet_relaxation"]:
                # High score for parks, nature, library, gardens, temples
                if any(w in text_corpus for w in ["park", "garden", "library", "temple", "quiet", "green", "lake", "shrine"]):
                    score += 0.40
                    reasons.append("Tranquil green environment ideal for relaxation")
                elif any(w in text_corpus for w in ["food", "traffic", "crowded", "bazaar"]):
                    score -= 0.30

            if prefs["is_food"]:
                if any(w in text_corpus for w in ["restaurant", "cafe", "food", "dose", "coffee"]):
                    score += 0.35
                    reasons.append("Popular local culinary spot")

            if prefs["step_free_preferred"] and p.get("is_step_free"):
                score += 0.20
                reasons.append("Step-free accessible pathways")

            p_copy = dict(p)
            p_copy["recommendation_score"] = round(score, 3)
            p_copy["why_it_fits"] = reasons
            scored.append(p_copy)

        scored.sort(key=lambda x: x["recommendation_score"], reverse=True)
        top_places = scored[:top_k]

        # 3. If local DB returned no places in radius, dynamically discover nearby places via OSM
        if not top_places:
            location_hint = geo_ctx.neighborhood or geo_ctx.locality or geo_ctx.city
            category_label = "coffee shops and cafes" if prefs["is_food"] else ("quiet parks and gardens" if prefs["is_quiet_relaxation"] else "places to visit")
            search_prompt = f"{category_label} in {location_hint}"
            external_places = self.pipeline.discover_and_ingest_local_business(
                query=search_prompt,
                location_hint=location_hint,
                destination_name=geo_ctx.city,
                city_id=geo_ctx.city_id,
                category_intent=prefs["category_intent"],
                max_results=top_k
            )
            for ep in external_places:
                dist_m = 800.0
                if ep.get("latitude") and ep.get("longitude"):
                    from backend.location_service import haversine_distance
                    dist_m = haversine_distance(lat, lon, ep["latitude"], ep["longitude"])
                top_places.append({
                    "name": ep["name"],
                    "category": ep["category"],
                    "distance_m": round(dist_m, 1),
                    "distance_km": round(dist_m / 1000.0, 2),
                    "walk_time_mins": max(1, int(dist_m / 80.0)),
                    "address": ep["address"],
                    "short_desc": f"{ep['name']} ({ep['category']}) in {ep['address']}",
                    "why_it_fits": [f"{int(dist_m)} m away", "Found in your local area"],
                    "source": ep["source"]
                })

        # 4. Formulate structured recommendation answer (NEVER city overview)
        if not top_places:
            return {
                "answerable": True,
                "retrieval_mode": "LOCAL_SEARCH_RECOMMENDATION",
                "answer": (
                    f"I couldn't find verified places matching that criteria within {radius_m}m of your location "
                    f"in {geo_ctx.get_display_location()}. Try expanding your search radius."
                ),
                "places": [],
                "source": "OpenStreetMap Local Places Spatial Index",
                "source_tag": "Nearby Proximity Search",
                "verified": True
            }

        # Build explainable response
        if is_fallback_location:
            header = (
                f"*(Device GPS location was unavailable, showing places around {geo_ctx.get_display_location()} center)*\n\n"
                f"Here are the top places near {geo_ctx.get_display_location()}:\n\n"
            )
        else:
            header = f"Here are the top places near you in {geo_ctx.get_display_location()}:\n\n"
        place_items = []
        for idx, pl in enumerate(top_places, 1):
            reasons_str = " • ".join(pl.get("why_it_fits", []))
            p_lat = pl.get("lat") or pl.get("latitude")
            p_lng = pl.get("lng") or pl.get("longitude")
            nav_link = ""
            if p_lat and p_lng:
                nav_link = f"\n   - 🗺️ [Open Navigation Map](https://www.google.com/maps/dir/?api=1&destination={p_lat},{p_lng})"
            elif pl.get("address"):
                import urllib.parse
                nav_link = f"\n   - 🗺️ [Open Navigation Map](https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(pl['name'] + ' ' + pl['address'])})"

            place_items.append(
                f"{idx}. **{pl['name']}** ({pl.get('distance_km', 0.5)} km • ~{pl.get('walk_time_mins', 5)} min walk)\n"
                f"   - *Why it fits*: {reasons_str}\n"
                f"   - *Details*: {pl.get('short_desc', '')}{nav_link}"
            )

        full_answer = header + "\n\n".join(place_items)

        return {
            "answerable": True,
            "retrieval_mode": "LOCAL_SEARCH_RECOMMENDATION",
            "answer": full_answer,
            "places": top_places,
            "source": top_places[0].get("source", "PostGIS Spatial Proximity Index"),
            "source_tag": "Nearby Spatial Recommendation • PostGIS",
            "evidence_count": len(top_places),
            "evidence_snippets": [
                {
                    "title": pl["name"],
                    "content": f"{pl['name']} is {pl.get('distance_m')}m away. {pl.get('short_desc')}",
                    "source": pl.get("source", "Spatial Proximity")
                } for pl in top_places
            ],
            "verified": True
        }
