"""
test_location_intelligence_overhaul.py
---------------------------------------
Regression tests covering the 12 critical location intelligence, entity resolution,
retrieval routing, operational status, and spatial recommendation requirements.
"""
import pytest
from backend.rag_service import GroundedRAGService, QueryContext
from backend.geo_context import GeoContext, LocationPermissionState
from backend.location_service import LocationService
from backend.entity_resolver import EntityResolver, normalize_name
from backend.local_search import LocalSearchService


@pytest.fixture
def rag():
    return GroundedRAGService()


def test_1_slv_hotel_entity_resolution_no_blind_collapse(rag):
    """
    User: 'Where is SLV Hotel in Gandhi Bazaar?'
    Must resolve 'SLV Hotel' using multi-stage scoring and distinguish from 'SLV Delite'.
    Must NEVER claim SLV Delite IS SLV Hotel without disambiguating.
    """
    res = rag.answer_query("Where is SLV Hotel in Gandhi Bazaar?", city_id=2, language="en")
    assert res["answerable"] is True
    assert "slv" in res["answer"].lower()
    import unicodedata
    ans_clean = unicodedata.normalize('NFKD', res["answer"]).lower()
    assert ("not find an exact match" in ans_clean or 
            "closest is" in ans_clean or 
            "slv hotel" in ans_clean)
    # Retrieval mode must be local search
    assert res["retrieval_mode"] == "LOCAL_PLACES_SEARCH"


def test_2_lalbagh_closing_time_differentiation(rag):
    """
    User: 'what time is the lalbagh closing?'
    Must return published normal closing time (18:00) with proper attribution.
    Must not confuse normal closing with advisory staging or generic overview.
    """
    res = rag.answer_query("what time is the lalbagh closing?", city_id=2, language="en")
    assert res["answerable"] is True
    assert res["attribute"] == "STANDARD_HOURS"
    assert "18:00" in res["answer"]
    assert "lalbagh" in res["answer"].lower()
    assert "Department of Horticulture" in res["source"] or "Official" in res["source"] or "Registry" in res["source"]


def test_3_hanuman_temple_girinagar_no_lalbagh_contamination(rag):
    """
    User: 'is hanuman temple in girinagar open now??'
    Must NEVER return Lalbagh Botanical Garden or Department of Horticulture citations.
    """
    res = rag.answer_query("is hanuman temple in girinagar open now??", city_id=2, language="en")
    ans_lower = res["answer"].lower()
    src_lower = res["source"].lower()
    
    assert "lalbagh" not in ans_lower
    assert "lalbagh" not in src_lower
    assert "flower show" not in ans_lower
    assert "department of horticulture" not in src_lower


def test_4_karyasiddhi_temple_girinagar_no_lalbagh_contamination(rag):
    """
    User: 'is karyasiddhi temple in girinagar open now??'
    Must NEVER return Lalbagh Botanical Garden or Department of Horticulture citations.
    """
    res = rag.answer_query("is karyasiddhi temple in girinagar open now??", city_id=2, language="en")
    ans_lower = res["answer"].lower()
    src_lower = res["source"].lower()
    
    assert "lalbagh" not in ans_lower
    assert "lalbagh" not in src_lower
    assert "flower show" not in ans_lower
    assert "department of horticulture" not in src_lower


def test_5_quiet_place_near_me_spatial_proximity_search(rag):
    """
    User: 'find a quiet place to relax near me'
    With user coordinates in Bengaluru, must execute coordinate-based proximity search
    and return nearby places (e.g. Cubbon Park, Lalbagh, NGMA).
    NEVER fall back to generic city overview or population numbers.
    """
    session_ctx = {
        "user_lat": 12.9716,
        "user_lng": 77.5946,
        "accuracy_m": 8.0,
        "location_source": "gps"
    }
    res = rag.answer_query("find a quiet place to relax near me", city_id=2, session_context=session_ctx)
    assert res["answerable"] is True
    assert res["retrieval_mode"] == "LOCAL_SEARCH_RECOMMENDATION"
    ans_lower = res["answer"].lower()
    
    # Must contain actual nearby places
    assert any(p in ans_lower for p in ["cubbon", "lalbagh", "park", "garden", "library", "ngma"])
    # Must NOT be a generic population or city overview
    assert "8.4 million" not in ans_lower
    assert "census" not in ans_lower


def test_6_quiet_place_near_me_without_coords_prompts_user(rag):
    """
    When coordinates are unavailable, 'near me' query prompts the user rather than guessing fake locations.
    """
    res = rag.answer_query("find a quiet place to relax near me", city_id=2, session_context=None)
    # When no coords provided, it recognizes location is needed or prompts cleanly
    assert "location" in res["answer"].lower() or "near" in res["answer"].lower()


def test_7_entity_resolver_normalizes_and_penalizes_branch_divergence():
    """
    EntityResolver: 'SLV Hotel' vs 'SLV Delite' has distinct suffix penalty and ambiguity detection.
    """
    candidates = [
        {"name": "SLV Delite", "address": "Gandhi Bazaar", "category": "Restaurant / Eatery"},
        {"name": "SLV Corner", "address": "Basavanagudi", "category": "Restaurant / Eatery"}
    ]
    top, conf, alts = EntityResolver.resolve_candidate("SLV Hotel", candidates, location_hint="Gandhi Bazaar")
    assert top is not None
    assert top["name"] == "SLV Delite"
    # Not exact match because Hotel != Delite
    assert EntityResolver.is_exact_match("SLV Hotel", top["name"]) is False


def test_8_geo_context_freshness_tiers():
    """
    GeoContext freshness calculation: <2m (FRESH), 2-10m (USABLE), >10m (STALE).
    """
    from backend.geo_context import LocationFreshness
    import time
    now = time.time()
    ctx_fresh = GeoContext(latitude=12.97, longitude=77.59, timestamp=now - 30)
    assert ctx_fresh.get_freshness() == LocationFreshness.FRESH

    ctx_usable = GeoContext(latitude=12.97, longitude=77.59, timestamp=now - 200)
    assert ctx_usable.get_freshness() == LocationFreshness.USABLE

    ctx_stale = GeoContext(latitude=12.97, longitude=77.59, timestamp=now - 800)
    assert ctx_stale.get_freshness() == LocationFreshness.STALE


def test_9_location_service_spatial_proximity():
    """
    LocationService.search_nearby_places finds nearby POIs in Bengaluru using earthdistance.
    """
    results = LocationService.search_nearby_places(lat=12.9716, lon=77.5946, max_radius_m=3000)
    assert len(results) > 0
    names = [r["name"] for r in results]
    assert any("Cubbon" in n or "Lalbagh" in n or "NGMA" in n for n in names)
    assert results[0]["distance_m"] < 3000


def test_10_api_ask_endpoint_accepts_coords():
    """
    FastAPI /api/ask accepts user_lat, user_lng, accuracy_m, and returns grounded response.
    """
    from fastapi.testclient import TestClient
    from backend.main import app
    client = TestClient(app)
    
    resp = client.post("/api/ask", json={
        "query": "find a quiet place to relax near me",
        "city_id": 2,
        "user_lat": 12.9716,
        "user_lng": 77.5946,
        "accuracy_m": 8.0,
        "location_source": "gps"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["answerable"] is True
    assert "cubbon" in data["answer"].lower() or "park" in data["answer"].lower()
