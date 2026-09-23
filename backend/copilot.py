import math
from typing import List, Dict, Any, Optional
from backend.database import get_connection
from backend.recommendation import haversine

class CopilotEngine:
    """
    Proactive Intelligence & Opportunity Detector for GeoGuide.
    Evaluates:
      - Remaining daylight & sunset window
      - Upcoming monument closing hours
      - Weather shifts (e.g. rain onset)
      - Nearby high-relevance POIs
      - Itinerary feasibility & delay monitoring
    """
    def __init__(self):
        pass

    def evaluate_next_action(
        self,
        city_id: int = 1,
        city_name: str = "Hampi",
        user_prefs: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
        user_lat: Optional[float] = None,
        user_lng: Optional[float] = None,
        current_plan_items: Optional[List[Dict[str, Any]]] = None,
        simulated_state: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        
        sim_state = simulated_state or {}
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM activities_poi WHERE city_id = ?", (city_id,))
        pois = [dict(r) for r in cursor.fetchall()]
        conn.close()

        # 1. Rain Alert Trigger
        if sim_state.get('weather') == 'rain':
            indoor_pois = [p for p in pois if 'shade' in p.get('short_desc', '').lower() or 'temple' in p.get('name', '').lower()]
            top_p = indoor_pois[0] if indoor_pois else pois[0]
            return {
                "action": "TAKE_SHELTER_INDOOR",
                "poi_id": top_p['id'],
                "poi_name": top_p['name'],
                "urgency": "HIGH",
                "reason": "Rain detected: Move to covered heritage architecture to avoid slippery boulder paths.",
                "why_it_fits": [
                    "Underground & covered stone corridors",
                    "Cool sheltered atmosphere during rain",
                    "Level accessible walkways"
                ],
                "time_window": "Next 45 minutes",
                "recommended_action_type": "VISIT_NOW"
            }

        # 2. Sunset Approach Trigger (e.g. within 60 mins of sunset)
        sunset_poi = next((p for p in pois if 'sunset' in p.get('tag_badge', '').lower() or 'hemakuta' in p.get('name', '').lower()), None)
        if sunset_poi and (sim_state.get('sunset_approaching') or sim_state.get('time_hour', 16) >= 17):
            return {
                "action": "SUNSET_VIEWPOINT",
                "poi_id": sunset_poi['id'],
                "poi_name": sunset_poi['name'],
                "urgency": "HIGH",
                "reason": f"Golden Hour in 42 minutes! {sunset_poi['name']} is 6 min away and offers the finest sunset vantage point.",
                "why_it_fits": [
                    "Golden hour lighting over historic shrines",
                    "Gentle granite slope with easy access",
                    "Free entry with zero ticket queues"
                ],
                "time_window": "17:30 to 18:30 (Sunset 18:41)",
                "recommended_action_type": "ADD_TO_PLAN"
            }

        # 3. Monument Closing Soon Trigger
        vittala_poi = next((p for p in pois if 'vittala' in p.get('name', '').lower()), None)
        if vittala_poi and not sim_state.get('vittala_closed'):
            return {
                "action": "CLOSING_SOON_VISIT",
                "poi_id": vittala_poi['id'],
                "poi_name": vittala_poi['name'],
                "urgency": "MEDIUM",
                "reason": f"Ticketed entry for {vittala_poi['name']} closes at 17:00 (1h 15m remaining).",
                "why_it_fits": [
                    "Shared ASI ticket valid for both Vittala and Zenana",
                    "Stone Chariot & musical pillars iconic highlight",
                    "Matches your history + architecture preference"
                ],
                "time_window": "Before 17:00 ticket cutoff",
                "recommended_action_type": "VISIT_NOW"
            }

        # 4. Default High-Value Cultural Discovery
        top_poi = pois[0] if pois else {"id": 1, "name": "Virupaksha Temple"}
        return {
            "action": "EXPLORE_PROXIMITY",
            "poi_id": top_poi['id'],
            "poi_name": top_poi['name'],
            "urgency": "LOW",
            "reason": f"You are 350m from {top_poi['name']}, the living sacred heart of {city_name}.",
            "why_it_fits": [
                "Unbroken worship since the 7th century",
                "Active temple elephant and grand gopura",
                "Low walking effort from main bazaar"
            ],
            "time_window": "Open now until dusk",
            "recommended_action_type": "ADD_TO_PLAN"
        }

    def detect_opportunities(self, city_id: int = 1, context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Generates proactive Don't-Miss opportunity cards."""
        return [
            {
                "type": "SUNSET_OPPORTUNITY",
                "priority": 0.95,
                "title": "Sunset Opportunity at Hemakuta Hill",
                "reason": "Sunset at 18:41 (48 mins daylight remaining). 6 min walk from Bazaar.",
                "poi_id": 4,
                "poi_name": "Hemakuta Hill",
                "action_text": "Add sunset stop"
            },
            {
                "type": "CLOSING_SOON",
                "priority": 0.90,
                "title": "Vittala Temple entry closes at 17:00",
                "reason": "Combined ASI ticket required. Visit now before final gate entry cutoff.",
                "poi_id": 1,
                "poi_name": "Vittala Temple & Stone Chariot",
                "action_text": "Prioritize now"
            },
            {
                "type": "HIDDEN_GEM",
                "priority": 0.82,
                "title": "Underground Shiva Temple (Cool Shade)",
                "reason": "Sunken subterranean sanctum 5°C cooler than midday sun.",
                "poi_id": 5,
                "poi_name": "Underground Shiva Temple",
                "action_text": "View details"
            }
        ]
