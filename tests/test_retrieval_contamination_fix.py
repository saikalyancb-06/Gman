import pytest
from backend.rag_service import GroundedRAGService, QueryContext, RelevanceGate

@pytest.fixture
def rag():
    return GroundedRAGService()

def test_hard_negative_lalbagh_not_tungabhadra(rag):
    """Lalbagh query must never retrieve Tungabhadra or Hampi chunks as evidence."""
    res = rag.answer_query("Is Lalbagh open now?", city_id=1, language="en")
    assert res["resolved_entity"] == "Lalbagh Botanical Garden & Glass House"
    assert res["destination"] == "Bengaluru"
    assert "tungabhadra" not in res["answer"].lower()
    assert "hampi" not in res["answer"].lower()
    assert "vittala" not in res["answer"].lower()
    assert "Department of Horticulture" in res["source"] or "Lalbagh" in res["source"]

def test_hard_negative_population_not_generic_overview(rag):
    """Population query must reject generic city overview and retrieve population data."""
    res = rag.answer_query("What is the population of Bangalore?", city_id=1, language="en")
    assert res["attribute"] == "POPULATION"
    assert res["retrieval_mode"] in ["WEB_RETRIEVAL", "PACK_SEMANTIC"]
    # If generic overview was evaluated, it must have been rejected
    rejected_titles = [r["doc_title"] for r in res.get("rejected_candidates", [])]
    if "Overview of Bengaluru" in [c.get("title") for c in rag.documents]:
        assert "Overview of Bengaluru" in rejected_titles
    # Answer must contain verified numeric population
    clean_ans = res["answer"].replace("\u202f", " ").replace("\xa0", " ")
    assert any(num in clean_ans for num in ["8.4 million", "8.5 million", "8 million", "8.4"])

def test_hard_negative_vittala_not_virupaksha(rag):
    """Virupaksha query must not retrieve Vittala musical pillars."""
    q_ctx = QueryContext.resolve("What is the history of Virupaksha Temple?")
    for doc in rag.documents:
        if "musical pillars" in doc.get("title", "").lower():
            valid, reason = RelevanceGate.validate_chunk(doc, q_ctx.query, q_ctx, 0.8)
            assert valid is False
            assert "MISMATCH" in reason

def test_hard_negative_weather_not_history(rag):
    """Weather query must never retrieve history or food chunks."""
    q_ctx = QueryContext.resolve("What's the weather in Hampi?")
    for doc in rag.documents:
        if doc.get("type") in ["poi_detail", "place_kb"]:
            valid, reason = RelevanceGate.validate_chunk(doc, q_ctx.query, q_ctx, 0.8)
            assert valid is False
            assert "WEATHER_REQUIRED" in reason or "MISMATCH" in reason

def test_hard_negative_opening_hours_differentiation(rag):
    """Opening hours query retrieves standard schedule, while 'open now' checks operational notices."""
    res_hours = rag.answer_query("What are Lalbagh's opening hours?", city_id=1, language="en")
    assert res_hours["attribute"] == "STANDARD_HOURS"
    assert "06:00" in res_hours["answer"]

    res_now = rag.answer_query("Is Lalbagh open now?", city_id=1, language="en")
    assert res_now["attribute"] == "OPEN_STATUS"
    assert res_now["temporal_requirement"] == "NOW"
    assert "open" in res_now["answer"].lower() or "06:00" in res_now["answer"]

def test_hard_negative_explicit_location_overrides_session(rag):
    """User in Bengaluru asking about Tungabhadra resolves to Hampi."""
    res = rag.answer_query("Is the Tungabhadra coracle ride open?", city_id=2, language="en")
    assert res["destination"] == "Hampi"
    assert "Tungabhadra" in res["source"] or "coracle" in res["answer"].lower()
    assert "lalbagh" not in res["answer"].lower()

def test_all_14_queries_pass(rag):
    """Verify all 14 benchmark queries resolve with valid grounded output."""
    queries = [
        ("What is the population of Bangalore?", "8."),
        ("What is the population of Bengaluru?", "8."),
        ("Tell me about Bangalore.", "Bengaluru"),
        ("Is Lalbagh open now?", "06:00"),
        ("What are Lalbagh's opening hours?", "06:00"),
        ("Is Lalbagh closed today?", "Lalbagh"),
        ("Where are the musical pillars?", "Vittala Temple"),
        ("What is the history of Virupaksha Temple?", "Virupaksha"),
        ("Is the Tungabhadra coracle ride open?", "Tungabhadra"),
        ("What's the weather in Bangalore?", "Bengaluru"),
        ("What's the weather in Hampi?", "Hampi"),
        ("Tell me about Bengaluru Palace.", "Palace"),
        ("Which place has the Stone Chariot?", "Vittala Temple"),
        ("Where can I see the inverted shadow effect?", "Virupaksha")
    ]
    for q, expected_substr in queries:
        ans = rag.answer_query(q, city_id=1, language="en")
        assert ans["answerable"] is True
        assert expected_substr.lower() in ans["answer"].lower()

