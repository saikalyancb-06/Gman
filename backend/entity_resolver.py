import re
import unicodedata
from typing import List, Dict, Any, Optional, Tuple
from backend.location_service import haversine_distance

def normalize_name(text: str) -> str:
    """Normalizes string for exact and near-exact entity comparison."""
    if not text:
        return ""
    # Unicode NFKD normalization
    text = unicodedata.normalize('NFKD', text)
    text = text.lower().strip()
    # Remove punctuation
    text = re.sub(r'[^\w\s]', ' ', text)
    # Collapse whitespace
    tokens = text.split()
    return " ".join(tokens)

class EntityResolver:
    """
    Multi-Stage Entity Resolution Engine for GeoGuide.
    Eliminates false name collapses (e.g. SLV Hotel -> SLV Delite).
    
    Stages:
    1. Candidate Generation (Exact match, word overlap, spatial candidates)
    2. Name Normalization & Exact Token Match
    3. Category Alignment (Restaurant vs Lodging vs Worship)
    4. Geographic Neighborhood Proximity
    5. Multi-Factor Confidence Scoring
    6. Ambiguity Detection (offers options instead of false guessing)
    """

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
        req_tokens = set(norm_req.split())

        scored_candidates = []
        for cand in candidates:
            cand_name = cand.get("name") or cand.get("title") or ""
            norm_cand = normalize_name(cand_name)
            cand_tokens = set(norm_cand.split())

            # 1. Name Match Score [0.0 - 0.50]
            if norm_req == norm_cand:
                name_score = 0.50
            elif norm_req in norm_cand or norm_cand in norm_req:
                name_score = 0.40
            else:
                # Token Jaccard overlap
                intersection = req_tokens.intersection(cand_tokens)
                union = req_tokens.union(cand_tokens)
                jaccard = len(intersection) / len(union) if union else 0.0
                name_score = jaccard * 0.35

            # Distinct entity penalty:
            # If user explicitly requested "hotel" but candidate is named "delite" or "corner" without "hotel"
            if "hotel" in req_tokens and "hotel" not in cand_tokens:
                if any(distinct_suffix in cand_tokens for distinct_suffix in ["delite", "corner", "residency", "darshini"]):
                    name_score *= 0.50 # Heavy penalty for distinct branch / entity name

            # 2. Location Match Score [0.0 - 0.25]
            loc_score = 0.0
            cand_addr = cand.get("address", "").lower()
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
            cat_score = 0.10 # default neutral
            cand_cat = cand.get("category", "").lower()
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

        # Check for ambiguity
        # If top two candidates have very close scores (>0.60 and delta < 0.08)
        alternatives = []
        if len(scored_candidates) > 1:
            second = scored_candidates[1]
            if top["resolution_confidence"] - second["resolution_confidence"] < 0.08 and second["resolution_confidence"] >= 0.50:
                alternatives = scored_candidates[:3]

        return top, top["resolution_confidence"], alternatives

    @staticmethod
    def is_exact_match(requested_name: str, candidate_name: str) -> bool:
        """Determines if candidate name is an exact or near-exact match to requested name."""
        norm_req = normalize_name(requested_name)
        norm_cand = normalize_name(candidate_name)
        if norm_req == norm_cand:
            return True
        # Check if identical except generic suffix like "restaurant" or "bengaluru"
        req_clean = re.sub(r'\b(restaurant|hotel|cafe|temple|bengaluru|bangalore)\b', '', norm_req).strip()
        cand_clean = re.sub(r'\b(restaurant|hotel|cafe|temple|bengaluru|bangalore)\b', '', norm_cand).strip()
        return bool(req_clean and req_clean == cand_clean)
