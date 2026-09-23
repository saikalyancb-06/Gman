import pytest
from backend.rag_service import GroundedRAGService

def test_tokyo_external_retrieval():
    """Missing local entity (Tokyo) retrieves from verified external web source."""
    rag = GroundedRAGService()
    res = rag.answer_query("Tell me about Tokyo", language="en", city_id=1, city_name="Hampi")
    
    assert res["answerable"] is True
    assert res["support_status"] == "SUPPORTED"
    assert "Tokyo" in res["answer"] or "Japan" in res["answer"]
    assert "Wikipedia" in res["source"] or "Verified External" in res["source_tag"]

def test_unsupported_out_of_domain_abstains():
    """Out of domain non-place queries cleanly abstain."""
    rag = GroundedRAGService()
    res = rag.answer_query("What is the phone number of the hotel manager on Mars?", language="en", city_id=1)
    
    assert res["answerable"] is False
    assert res["support_status"] == "UNSUPPORTED"
    assert "couldn't verify" in res["answer"].lower()
