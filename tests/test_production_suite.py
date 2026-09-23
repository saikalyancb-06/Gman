import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.rag_service import GroundedRAGService
from backend.optimizer import ItineraryOptimizer
from backend.recommendation import RecommendationEngine

client = TestClient(app)

def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "SQLite" in data["db"]

def test_cities_list():
    response = client.get("/api/cities")
    assert response.status_code == 200
    cities = response.json()["cities"]
    assert len(cities) >= 2
    city_names = [c["name"] for c in cities]
    assert "Hampi" in city_names or "Bengaluru" in city_names

def test_context_now_hampi():
    response = client.get("/api/context/now?city_id=1")
    assert response.status_code == 200
    data = response.json()
    assert data["location"]["city"] == "Hampi"
    assert "temp_c" in data["weather"]
    assert "sunset" in data["weather"]
    assert "grounded_briefing" in data
    assert data["grounded_briefing"]["verified"] is True
    assert "copilot_next_action" in data
    assert data["copilot_next_action"]["urgency"] in ["HIGH", "MEDIUM", "LOW"]

def test_rag_groundedness_ticket():
    rag = GroundedRAGService()
    res = rag.answer_query("Do I need one ticket or many?", language="en", city_id=1, city_name="Hampi")
    assert "Vittala" in res["answer"]
    assert "₹30" in res["answer"]
    assert res["verified"] is True
    assert "ASI" in res["source"]

def test_rag_multilingual_kannada():
    rag = GroundedRAGService()
    res = rag.answer_query("Do I need a ticket?", language="kn", city_id=1, city_name="Hampi")
    assert res["language"] == "kn"
    assert "₹30" in res["answer"]
    assert res["verified"] is True

def test_recommendation_ranking():
    rec = RecommendationEngine()
    pois = [
        {"id": 1, "name": "Vittala Temple", "short_desc": "Architecture monument", "entry_fee_inr": 30, "is_step_free": 1, "lat": 15.33, "lng": 76.47},
        {"id": 2, "name": "Matanga Hill", "short_desc": "Steep nature climb", "entry_fee_inr": 0, "is_step_free": 0, "lat": 15.33, "lng": 76.46}
    ]
    ranked = rec.rank_pois(
        pois=pois,
        user_prefs={"interests": ["Architecture"], "step_free_only": True, "budget_tier": "mid"},
        context={"weather": {"condition": "clear"}}
    )
    assert len(ranked) == 2
    # Step-free place should rank first when step_free_only is requested
    assert ranked[0]["poi"]["name"] == "Vittala Temple"
    assert ranked[0]["score"] > ranked[1]["score"]

def test_itinerary_optimizer_constraints():
    opt = ItineraryOptimizer()
    plan_2h = opt.solve(city_id=1, duration_type="2_hours", optimization_filter="less_walking")
    assert len(plan_2h["items"]) == 2
    assert plan_2h["is_feasible"] is True

    plan_4h = opt.solve(city_id=1, duration_type="4_hours", optimization_filter="cheaper")
    assert len(plan_4h["items"]) == 3
    assert plan_4h["metrics"]["cost_inr"] == 0  # Cheaper filter should select free places

def test_natural_language_replanning():
    opt = ItineraryOptimizer()
    plan = opt.solve(city_id=1, natural_instruction="Bro I am tired, make it less walking")
    assert plan["optimization_filter"] == "less_walking"
    for item in plan["items"]:
        assert item["is_step_free"] is True

def test_vision_identify_endpoint():
    response = client.post("/api/vision/identify", json={"landmark_hint": "chariot", "city_id": 1})
    assert response.status_code == 200
    data = response.json()
    assert "Vittala" in data["name"]
    assert data["confidence"] > 0.8
    assert "ASI" in data["source"]

def test_evidence_endpoint():
    response = client.get("/api/places/1/evidence")
    assert response.status_code == 200
    data = response.json()
    assert len(data["sources"]) >= 2
    for s in data["sources"]:
        assert s["verified"] is True
