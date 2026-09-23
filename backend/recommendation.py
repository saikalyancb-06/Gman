import math
from typing import List, Dict, Any, Optional

def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0 # km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 2)

class RecommendationEngine:
    """
    Explainable, deterministic Multi-Factor Scoring Engine for POIs.
    Outputs: normalized score [0.0 - 1.0] and auditable attribution reasons.
    """
    def __init__(self):
        # Default baseline weights
        self.weights = {
            "interest_match": 0.25,
            "proximity": 0.15,
            "time_fit": 0.12,
            "accessibility": 0.12,
            "budget_fit": 0.10,
            "open_status": 0.10,
            "weather_fit": 0.08,
            "carbon_penalty": 0.04,
            "walking_penalty": 0.04
        }

    def score_poi(
        self,
        poi: Dict[str, Any],
        user_prefs: Dict[str, Any],
        context: Dict[str, Any],
        user_lat: Optional[float] = None,
        user_lng: Optional[float] = None
    ) -> Dict[str, Any]:
        reasons = []
        raw_features = {}

        # 1. Proximity / Distance calculation
        if user_lat is not None and user_lng is not None:
            dist_km = haversine(user_lat, user_lng, poi['lat'], poi['lng'])
        else:
            dist_km = poi.get('distance_km', 1.0)
        
        # Proximity score (decay after 5km)
        prox_score = max(0.0, 1.0 - (dist_km / 10.0))
        raw_features["distance_km"] = dist_km
        raw_features["proximity_score"] = prox_score
        if dist_km <= 1.0:
            reasons.append(f"Only {int(dist_km*1000)}m away ({poi.get('travel_time_mins', 5)} min)")
        elif dist_km <= 3.0:
            reasons.append(f"Short {dist_km:.1f} km hop ({poi.get('travel_time_mins', 10)} min travel)")

        # 2. Interest Match
        user_interests = [i.lower() for i in user_prefs.get('interests', ['history', 'architecture', 'photography'])]
        poi_text = (poi.get('name', '') + ' ' + poi.get('short_desc', '') + ' ' + poi.get('full_desc', '') + ' ' + poi.get('tag_badge', '')).lower()
        matched_interests = [i for i in user_interests if i in poi_text or (i == 'history' and 'monument' in poi_text)]
        interest_score = min(1.0, len(matched_interests) * 0.45) if user_interests else 0.7
        raw_features["interest_score"] = interest_score
        if matched_interests:
            reasons.append(f"Matches your interest in {', '.join(matched_interests).title()}")

        # 3. Accessibility & Walking Fit
        is_step_free = bool(poi.get('is_step_free', 0))
        req_step_free = bool(user_prefs.get('step_free_only', False))
        max_walk = float(user_prefs.get('max_walking_km', 3.0))

        if req_step_free:
            access_score = 1.0 if is_step_free else 0.0
            if is_step_free:
                reasons.append("Step-free & wheelchair accessible")
        else:
            access_score = 1.0 if is_step_free else 0.75
        raw_features["accessibility_score"] = access_score

        # Walking penalty
        walk_penalty = 0.0
        if dist_km > max_walk and poi.get('travel_mode') == 'walk':
            walk_penalty = min(1.0, (dist_km - max_walk) / 2.0)
            raw_features["walking_penalty"] = walk_penalty

        # 4. Budget Fit
        fee = poi.get('entry_fee_inr', 0)
        budget_tier = user_prefs.get('budget_tier', 'mid')
        budget_limits = {'free': 0, 'budget': 100, 'mid': 500, 'luxury': 5000}
        max_fee = budget_limits.get(budget_tier, 500)

        if fee == 0:
            budget_score = 1.0
            reasons.append("Free entry / no ticket barrier")
        elif fee <= max_fee:
            budget_score = 0.9
            reasons.append(f"Fits within your ₹{max_fee} budget (₹{fee})")
        else:
            budget_score = max(0.1, 1.0 - (fee - max_fee) / 1000.0)
        raw_features["budget_score"] = budget_score

        # 5. Open Status & Daylight Window
        open_score = 1.0 # default open in daytime
        raw_features["open_score"] = open_score

        # 6. Weather Fit
        weather_cond = context.get('weather', {}).get('condition', 'Clear').lower()
        if 'rain' in weather_cond:
            weather_score = 1.0 if ('indoor' in poi_text or 'palace' in poi_text or 'museum' in poi_text or 'shiva' in poi_text) else 0.3
            if weather_score >= 0.9:
                reasons.append("Sheltered & weather-appropriate during rain")
        else:
            weather_score = 0.95
        raw_features["weather_score"] = weather_score

        # 7. Carbon Fit
        carbon_kg = float(poi.get('carbon_kg', 0.0))
        carbon_score = max(0.0, 1.0 - (carbon_kg / 1.0))
        raw_features["carbon_score"] = carbon_score

        # Weighted Total Score
        total_score = (
            self.weights["interest_match"] * interest_score +
            self.weights["proximity"] * prox_score +
            self.weights["accessibility"] * access_score +
            self.weights["budget_fit"] * budget_score +
            self.weights["open_status"] * open_score +
            self.weights["weather_fit"] * weather_score +
            0.05 * carbon_score -
            self.weights["walking_penalty"] * walk_penalty
        )
        total_score = max(0.01, min(0.99, round(total_score, 3)))

        return {
            "poi": poi,
            "score": total_score,
            "raw_features": raw_features,
            "reasons": reasons[:4] if reasons else ["Top rated cultural highlight", "Convenient location"]
        }

    def rank_pois(
        self,
        pois: List[Dict[str, Any]],
        user_prefs: Dict[str, Any],
        context: Dict[str, Any],
        user_lat: Optional[float] = None,
        user_lng: Optional[float] = None,
        hidden_gem_mode: bool = False
    ) -> List[Dict[str, Any]]:
        scored = [self.score_poi(p, user_prefs, context, user_lat, user_lng) for p in pois]

        if hidden_gem_mode:
            # Boost less popular but high interest/nature places
            for item in scored:
                p = item["poi"]
                review_count = p.get('review_count', 1000)
                is_gem = (review_count < 1000) or ('hidden' in p.get('tag_badge', '').lower()) or ('monolith' in p.get('tag_badge', '').lower())
                if is_gem:
                    item["score"] = min(0.98, item["score"] + 0.25)
                    item["reasons"].insert(0, "Hidden Gem: Uncrowded & high cultural value")

        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored
