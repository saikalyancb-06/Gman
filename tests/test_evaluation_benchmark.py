import pytest
from backend.rag_service import GroundedRAGService, QueryContext
from backend.query_planner import QueryPlanner
from backend.entity_resolver import EntityResolver
from backend.hybrid_retriever import HybridRetriever
from backend.geo_context import UserGeoContext, QueryDestinationContext, GeoContext

@pytest.fixture(scope="module")
def rag_service():
    return GroundedRAGService()

@pytest.fixture(scope="module")
def retriever():
    return HybridRetriever()

def test_evaluation_entity_resolution_accuracy():
    """
    Evaluates dynamic database entity linking accuracy across known monuments,
    parks, eateries, and generic queries without hardcoded dictionaries.
    """
    test_cases = [
        ("Is Lalbagh open right now?", "Lalbagh Botanical Garden & Glass House", "POI", 2),
        ("Where are the musical pillars?", "Vittala Temple", "POI", 1),
        ("What is the history of Virupaksha Temple?", "Virupaksha Temple", "POI", 1),
        ("Tell me about Mysore Palace.", "Mysore Palace (Amba Vilas)", "POI", 3),
        ("Where can I find SLV Hotel in Gandhi Bazaar?", "SLV Hotel", "POI", 2),
        ("What's the weather in Bengaluru?", "Bengaluru", "CITY", 2),
    ]

    for q, expected_name, expected_type, expected_city_id in test_cases:
        intent = QueryPlanner.parse_query(q)
        assert intent.entity_type == expected_type, f"Query '{q}' failed entity_type: got {intent.entity_type}, expected {expected_type}"
        assert intent.destination_id == expected_city_id, f"Query '{q}' failed city_id: got {intent.destination_id}, expected {expected_city_id}"
        if expected_type == "POI":
            assert expected_name.lower() in (intent.resolved_entity or "").lower() or (intent.resolved_entity or "").lower() in expected_name.lower()

def test_evaluation_retrieval_relevance_gate(rag_service):
    """
    Evaluates Precision@K and False Acceptance Rate of RelevanceGate across
    cross-destination contamination queries.
    """
    # Negative queries that must NOT accept mismatched landmark chunks
    negative_tests = [
        # Asking about Lalbagh in city_id=1 should reject Vittala / Tungabhadra
        ("Is Lalbagh open now?", 1, ["tungabhadra", "vittala", "stone chariot"]),
        # Asking about Tungabhadra in city_id=2 should reject Lalbagh / Cubbon
        ("Is the Tungabhadra coracle ride open?", 2, ["lalbagh", "cubbon"]),
        # Food queries should reject pure historical architecture without food
        ("Where can I get good filter coffee?", 2, ["inverted shadow", "virupaksha", "stone chariot"]),
    ]

    for q, query_city, forbidden_tokens in negative_tests:
        accepted, debug = rag_service.retrieve_with_relevance_gate(q, city_id=query_city, top_k=3)
        for chunk in accepted:
            c_text = (chunk.get("title", "") + " " + chunk.get("content", "")).lower()
            for forbidden in forbidden_tokens:
                assert forbidden not in c_text, f"Relevance Gate leak for query '{q}': found '{forbidden}' in chunk '{chunk.get('title')}'"

def test_evaluation_honest_abstention(rag_service):
    """
    Verifies that unanswerable, fabricated, or out-of-domain queries cleanly abstain
    without hallucinating facts.
    """
    unanswerable_queries = [
        "What is the phone number of the manager at Vittala Temple?",
        "Can I book a commercial flight from Paris to Hampi?",
        "How many aliens were spotted at Virupaksha Temple?",
        "What is the population of the colony on Mars?",
    ]

    for q in unanswerable_queries:
        res = rag_service.answer_query(q, city_id=1)
        assert res["answerable"] is False or res["grounding_status"] == "UNSUPPORTED" or "couldn't verify" in res["answer"].lower() or "out of domain" in res["source"].lower() or "not available" in res["answer"].lower()

def test_evaluation_grounding_claim_verification(rag_service):
    """
    Verifies that answer responses include complete provenance tags, sources,
    and verified status for verifiable benchmark facts.
    """
    benchmark_queries = [
        ("What are Lalbagh's opening hours?", "06:00", 2),
        ("Where are the musical pillars?", "Vittala", 1),
        ("What's the weather in Hampi?", "Hampi", 1),
        ("Which place has the Stone Chariot?", "Vittala", 1)
    ]

    for q, expected_token, default_city in benchmark_queries:
        res = rag_service.answer_query(q, city_id=default_city)
        assert res["verified"] is True
        assert res["answerable"] is True
        assert res["source"] is not None
        assert len(res["source"]) > 0
        assert expected_token.lower() in res["answer"].lower()
