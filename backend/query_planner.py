import re
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple
from backend.geo_context import UserGeoContext, QueryDestinationContext
from backend.pg_database import get_pg_connection
from backend.entity_resolver import EntityResolver, normalize_name

@dataclass
class QueryIntent:
    raw_query: str
    intent: str                            # FACT_LOOKUP, OPERATIONAL_STATUS, OPENING_HOURS, ENTRY_FEE, LIVE_WEATHER, LOCAL_SEARCH, LOCAL_NEARBY_RECOMMENDATION, LOCATION_LOOKUP, ACCESSIBILITY, DRESS_CODE, RIVER_SAFETY, FOOD, FACTUAL_COUNT, OUT_OF_DOMAIN, GENERAL_OVERVIEW
    attribute: str                         # POPULATION, OPEN_STATUS, STANDARD_HOURS, TICKETING, WEATHER_CURRENT, PROXIMITY_RECOMMENDATION, LOCAL_BUSINESS, LOCATION, STEP_FREE, ETIQUETTE, CORACLE_SAFETY, LOCAL_CUISINE, NUMERICAL_COUNT, OUT_OF_DOMAIN, CITY_OVERVIEW, POI_OVERVIEW
    temporal: str = "NONE"                 # NOW, TODAY, SCHEDULE, NONE
    freshness: str = "STATIC"              # LIVE_REQUIRED, DYNAMIC, SLOW, STATIC
    requires_numeric: bool = False
    resolved_entity: Optional[str] = None
    resolved_entity_id: Optional[int] = None
    entity_type: str = "CITY"              # POI, CITY, EXTERNAL, GENERAL
    destination_id: Optional[int] = None
    destination_name: Optional[str] = None
    location_hint: Optional[str] = None    # e.g. "Gandhi Bazaar", "Girinagar"
    poi_ref: Optional[str] = None
    user_location_required: bool = False
    destination_required: bool = True
    confidence: float = 0.85
    category_intent: Optional[str] = None

class QueryPlanner:
    """
    General-purpose Structured Query Understanding & Planning Engine.
    Converts natural-language queries into typed QueryIntent instances.
    Uses database-backed entity resolution and general linguistic/semantic pattern matching.
    """

    NEIGHBOURHOODS = [
        "gandhi bazaar", "gandhi bazar", "basavanagudi", "malleswaram", "malleshwaram",
        "koramangala", "indiranagar", "jayanagar", "jayanagara", "rajajinagar",
        "commercial street", "mg road", "brigade road", "lalbagh", "cubbon",
        "whitefield", "electronic city", "hebbal", "yelahanka", "jp nagar",
        "banashankari", "vijayanagar", "frazer town", "richmond town",
        "girinagar", "chamarajpet", "shankarapuram", "kamalapura", "hampi bazaar", "anegundi"
    ]

    @classmethod
    def parse_query(
        cls,
        query: str,
        session_city_id: int = 1,
        user_geo_context: Optional[UserGeoContext] = None
    ) -> QueryIntent:
        q_clean = query.strip()
        q_low = q_clean.lower()

        # 1. Check for Out-of-Domain External entities
        for ext in ["tokyo", "paris", "london", "mars", "moon", "alien"]:
            if ext in q_low:
                return QueryIntent(
                    raw_query=query,
                    intent="OUT_OF_DOMAIN" if ext in ["mars", "moon", "alien"] else "EXTERNAL_LOOKUP",
                    attribute="EXTERNAL_FACT",
                    temporal="NONE",
                    freshness="STATIC",
                    requires_numeric=False,
                    resolved_entity=ext.title(),
                    entity_type="EXTERNAL",
                    destination_name="External",
                    destination_required=False,
                    confidence=0.99
                )

        # 2. Extract Neighborhood / Location Hint
        location_hint = None
        for nb in cls.NEIGHBOURHOODS:
            if nb in q_low:
                location_hint = nb.title()
                break

        # 3. Detect Proximity / Near Me signals
        _ood_exclusions = [
            "ticket", "entry fee", "how much", "open now", "closed",
            "history", "built", "century", "dynasty", "booking", "reserve",
            "who is", "manager", "phone", "contact", "flight", "train"
        ]
        is_near_me = any(w in q_low for w in [
            "near me", "nearby", "around here", "close to me",
            "quiet place to relax", "place to relax", "places to relax", "peaceful place"
        ]) and not any(ex in q_low for ex in _ood_exclusions)

        # 4. Resolve Target Place / Entity dynamically against Database
        resolved_entity = None
        resolved_entity_id = None
        entity_type = "CITY"
        dest_id = None
        dest_name = None
        poi_ref = None

        db_candidates = EntityResolver.get_database_candidates(query, limit=20)
        if db_candidates and not is_near_me:
            top_cand, cand_conf, _ = EntityResolver.resolve_candidate(query, db_candidates, location_hint=location_hint)
            if top_cand and cand_conf >= 0.35:
                resolved_entity = top_cand.get("name")
                resolved_entity_id = top_cand.get("id")
                raw_type = top_cand.get("entity_type", "POI")
                # Normalize specific places/businesses to POI, cities to CITY, out-of-domain to EXTERNAL
                entity_type = "POI" if raw_type in ["POI", "BUSINESS", "MONUMENT", "PARK", "ATTRACTION"] else raw_type
                dest_id = top_cand.get("city_id")
                # Cross-reference city name
                if dest_id == 1:
                    dest_name = "Hampi"
                elif dest_id == 2:
                    dest_name = "Bengaluru"
                elif dest_id == 3:
                    dest_name = "Mysuru"
                elif top_cand.get("city_name"):
                    dest_name = top_cand.get("city_name")

        # Check explicit city names if entity not yet found
        if not dest_id:
            if any(w in q_low for w in ["bangalore", "bengaluru"]):
                dest_id = 2
                dest_name = "Bengaluru"
            elif any(w in q_low for w in ["hampi"]):
                dest_id = 1
                dest_name = "Hampi"
            elif any(w in q_low for w in ["mysore", "mysuru"]):
                dest_id = 3
                dest_name = "Mysuru"

        # Check for unknown place candidates in query e.g. "is <entity> in <neighborhood> open"
        if not resolved_entity:
            patterns = [
                r'\b(?:is|are)\s+([\w\s]+?)\s+(?:in|near|around|at)\s+([\w\s]+?)(?:\s+(?:open|closed|operating|hours|timing))?\??$',
                r'\b(?:where is|where are|find me|how to reach)\s+([\w\s]+?)(?:\s+(?:in|near|around|at)\s+([\w\s]+?))?\??$',
                r'\b(?:tell me about|info on|details of)\s+([\w\s]+?)(?:\s+(?:in|near|around|at)\s+([\w\s]+?))?\??$',
            ]
            for pat in patterns:
                m = re.search(pat, q_low)
                if m:
                    cand_entity = m.group(1).strip()
                    if cand_entity and cand_entity not in ["it", "there", "the place", "a quiet place", "places", "food", "a good place"]:
                        resolved_entity = cand_entity.title()
                        entity_type = "POI"
                        dest_id = dest_id or session_city_id or 2
                        dest_name = dest_name or ("Bengaluru" if dest_id == 2 else "Hampi")
                        break

        # Ambient Destination Fallback
        if not dest_id:
            dest_id = session_city_id or 1
            dest_name = "Bengaluru" if dest_id == 2 else ("Mysuru" if dest_id == 3 else "Hampi")
        if not resolved_entity:
            resolved_entity = dest_name

        # 5. Extract Category Intent
        category_intent = None
        if any(w in q_low for w in ["hotel", "lodge", "stay", "accommodation", "guesthouse", "hostel"]):
            category_intent = "ACCOMMODATION"
        elif any(w in q_low for w in ["restaurant", "food", "eat", "cafe", "coffee", "darshini", "lunch", "dinner", "breakfast"]):
            category_intent = "RESTAURANT"
        elif any(w in q_low for w in ["temple", "worship", "pooja", "deity"]):
            category_intent = "TEMPLE"

        # 6. Intent and Attribute Determination
        intent = "GENERAL_OVERVIEW"
        attribute = "CITY_OVERVIEW" if entity_type == "CITY" else "POI_OVERVIEW"
        temporal = "NONE"
        freshness = "STATIC"
        requires_numeric = False
        user_loc_req = False

        # Population
        if any(w in q_low for w in ["population", "how many people", "number of people", "demographic", "inhabitants", "residents"]):
            intent = "FACT_LOOKUP"
            attribute = "POPULATION"
            requires_numeric = True
            freshness = "STATIC"

        # Proximity recommendation
        elif is_near_me:
            intent = "LOCAL_NEARBY_RECOMMENDATION"
            attribute = "PROXIMITY_RECOMMENDATION"
            freshness = "DYNAMIC"
            user_loc_req = True

        # Operational status (open now / closed today)
        elif any(w in q_low for w in ["open now", "closed now", "open today", "closed today", "operating right now", "operating today", "currently open", "is it open", "is it closed", "can i visit now"]):
            intent = "OPERATIONAL_STATUS"
            attribute = "OPEN_STATUS"
            temporal = "NOW" if any(w in q_low for w in ["now", "right now", "currently"]) else "TODAY"
            freshness = "LIVE_REQUIRED"

        # Opening hours / Timings
        elif any(w in q_low for w in [
            "hours", "timing", "timings", "when does it open", "when does it close",
            "opening time", "closing time", "closing", "closes", "what time does it close",
            "what time is the", "what time does"
        ]):
            intent = "OPENING_HOURS"
            attribute = "STANDARD_HOURS"
            temporal = "SCHEDULE"
            freshness = "SLOW"

        # Live Weather
        elif any(w in q_low for w in ["weather", "temperature", "rain", "raining", "cloudy", "sunny", "forecast", "climate"]):
            intent = "LIVE_WEATHER"
            attribute = "WEATHER_CURRENT"
            temporal = "NOW"
            freshness = "LIVE_REQUIRED"

        # Ticket / Entry fee
        elif any(w in q_low for w in ["ticket", "cost", "fee", "entry", "price", "how much is", "charges"]):
            intent = "ENTRY_FEE"
            attribute = "TICKETING"
            requires_numeric = True
            freshness = "SLOW"

        # Local places search
        elif (
            any(w in q_low for w in ["restaurant", "restaurants", "cafe", "cafes", "coffee shop", "eatery", "eateries", "food places", "where to eat", "dine", "hotels in", "hotels near", "nearby places"])
            or (location_hint and any(w in q_low for w in ["hotel", "hotels", "restaurant", "cafe", "eat"]))
            or (any(w in q_low for w in ["where is", "where are", "find me"]) and any(w in q_low for w in ["hotel", "restaurant", "cafe", "lodge", "darshini"]))
        ) and not any(ex in q_low for ex in _ood_exclusions):
            intent = "LOCAL_SEARCH"
            attribute = "LOCAL_BUSINESS"
            freshness = "SLOW"

        # Location lookup
        elif any(w in q_low for w in ["where are", "where is", "which place has", "where can i see", "where can i find"]):
            intent = "LOCATION_LOOKUP"
            attribute = "LOCATION"
            freshness = "STATIC"

        # Accessibility
        elif any(w in q_low for w in ["step-free", "wheelchair", "accessible", "stairs", "ramp"]):
            intent = "ACCESSIBILITY"
            attribute = "STEP_FREE"

        # Dress code
        elif any(w in q_low for w in ["dress", "wear", "clothes", "etiquette", "shoes"]):
            intent = "DRESS_CODE"
            attribute = "ETIQUETTE"

        # River / Boat safety
        elif any(w in q_low for w in ["boat", "coracle", "river", "ferry"]):
            intent = "RIVER_SAFETY"
            attribute = "CORACLE_SAFETY"
            temporal = "NOW"
            freshness = "DYNAMIC"

        # Food / Cuisine
        elif any(w in q_low for w in ["eat", "food", "dish", "breakfast", "rotti", "idli", "dosa", "culinary"]):
            intent = "FOOD"
            attribute = "LOCAL_CUISINE"

        # Out of domain / Unanswerable External queries
        elif any(w in q_low for w in ["who is", "manager", "phone", "contact", "flight", "train", "hotel booking", "alien", "mars"]):
            intent = "OUT_OF_DOMAIN"
            attribute = "OUT_OF_DOMAIN"

        # Numerical Count
        elif any(w in q_low for w in ["how many", "how much", "count of", "number of people", "number of monuments", "number of stones", "exact number"]):
            intent = "FACTUAL_COUNT"
            attribute = "NUMERICAL_COUNT"
            requires_numeric = True

        # History
        elif re.search(r'\b(history|built|who made|century|dynasty|king|empire)\b', q_low):
            intent = "HISTORY"
            attribute = "HISTORY_ARCHITECTURE"

        return QueryIntent(
            raw_query=query,
            intent=intent,
            attribute=attribute,
            temporal=temporal,
            freshness=freshness,
            requires_numeric=requires_numeric,
            resolved_entity=resolved_entity,
            resolved_entity_id=resolved_entity_id,
            entity_type=entity_type,
            destination_id=dest_id,
            destination_name=dest_name,
            location_hint=location_hint,
            poi_ref=poi_ref,
            user_location_required=user_loc_req,
            destination_required=True,
            confidence=0.90,
            category_intent=category_intent
        )
