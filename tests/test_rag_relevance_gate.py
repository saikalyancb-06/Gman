import pytest
from backend.rag_service import GroundedRAGService, QueryIntentClassifier, RelevanceGate

def test_intent_classification():
    # 1. Numerical count
    res1 = QueryIntentClassifier.classify("how many stones are there in hampi")
    assert res1["intent"] == "FACTUAL_COUNT"
    assert res1["is_numerical"] is True

    # 2. Food query
    res2 = QueryIntentClassifier.classify("What is Jolada rotti?")
    assert res2["intent"] == "FOOD"
    assert res2["is_food"] is True

    # 3. Ticket query
    res3 = QueryIntentClassifier.classify("Do I need one ticket or many?")
    assert res3["intent"] == "ENTRY_FEE"

def test_relevance_gate_rejects_food_for_stones_query():
    rag = GroundedRAGService()
    # Query about stones
    accepted, debug = rag.retrieve_with_relevance_gate("how many stones are there in hampi", city_id=1)
    
    # Food chunks must be completely rejected
    titles = [c.get("title", "").lower() for c in accepted]
    assert not any("jolada" in t or "rotti" in t or "delicacy" in t for t in titles)
    
    # Check rejection logs
    rejections = [r["reason"] for r in debug["rejections"]]
    assert any("TOPIC_MISMATCH" in r or "INSUFFICIENT" in r or "OUT_OF_DOMAIN" in r for r in rejections)

def test_stones_query_answer_no_food_no_fabrication():
    rag = GroundedRAGService()
    res = rag.answer_query("how many stones are there in hampi", language="en", city_id=1, city_name="Hampi")
    
    # Assert no food mentioned
    assert "jolada" not in res["answer"].lower()
    assert "rotti" not in res["answer"].lower()
    assert "brinjal" not in res["answer"].lower()
    
    # Assert clean abstention without fabricating fake stone counts
    assert "couldn't verify" in res["answer"].lower()
    assert res["answerable"] is False
    assert res["support_status"] == "UNSUPPORTED"

def test_jolada_rotti_query_correctly_accepted():
    rag = GroundedRAGService()
    res = rag.answer_query("What is Jolada rotti?", language="en", city_id=1, city_name="Hampi")
    
    # Food query SHOULD retrieve food answer
    assert "jolada rotti" in res["answer"].lower()
    assert res["support_status"] == "SUPPORTED"
    assert res["answerable"] is True

def test_unsupported_random_query_abstains():
    rag = GroundedRAGService()
    res = rag.answer_query("Who is the current manager of the Hampi Bazaar restaurant?", language="en", city_id=1)
    
    # System must abstain with unsupported status
    assert res["answerable"] is False
    assert res["support_status"] == "UNSUPPORTED"
    assert "couldn't verify" in res["answer"]
    assert res["verified"] is False
