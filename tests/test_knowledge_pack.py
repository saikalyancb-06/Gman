"""
GeoGuide - Destination Knowledge Pack & GeoContext Test Suite
Validates:
1. GeoContextResolver location extraction & explicit overrides
2. KnowledgePackBuilder construction, hashing, and caching
3. Section-level TTL enforcement (STATIC, SLOW, DYNAMIC, LIVE)
4. Fast Pack-First Retrieval integration with RAG & Web Fallback
"""

import pytest
from backend.knowledge_pack import (
    GeoContextResolver,
    KnowledgePackBuilder,
    FRESHNESS_TTL
)
from backend.rag_service import GroundedRAGService

def test_geocontext_resolver_explicit_query_override():
    """Test that explicit query location names override the ambient session location."""
    # Ambient session is Hampi (city_id=1)
    # Query mentions Bangalore / Bengaluru explicitly
    context = GeoContextResolver.resolve_destination(
        destination_name_or_id=1,
        query="What is the weather in Bangalore today?"
    )
    assert context["destination_id"] == 2
    assert context["destination_name"] == "Bengaluru"
    assert context["detected_from"] == "explicit_query"

def test_geocontext_resolver_ambient_fallback():
    """Test that queries with no explicit location inherit the ambient session location."""
    context = GeoContextResolver.resolve_destination(
        destination_name_or_id=1,
        query="What can I do today?"
    )
    assert context["destination_id"] == 1
    assert context["destination_name"] == "Hampi"
    assert context["detected_from"] == "user_selection"

def test_knowledge_pack_builder_structure():
    """Test that building a knowledge pack populates all expected sections and metadata."""
    geo_context = GeoContextResolver.resolve_destination(destination_name_or_id=1)
    pack = KnowledgePackBuilder.build_pack(geo_context=geo_context)
    
    assert pack is not None
    assert pack["destination_id"] == 1
    assert pack["destination_name"] == "Hampi"
    assert pack["counts"]["pois"] > 0
    assert pack["counts"]["knowledge_items"] > 0
    assert pack["pack_hash"] != ""
    assert pack["sections"]["pois"] is True
    assert pack["sections"]["knowledge"] is True
    assert pack["sections"]["weather"] is True

def test_knowledge_pack_caching():
    """Test that caching returns the pre-built pack instantly with matching hash."""
    geo_context = GeoContextResolver.resolve_destination(destination_name_or_id=1)
    pack1 = KnowledgePackBuilder.get_or_build_pack(geo_context=geo_context)
    pack2 = KnowledgePackBuilder.get_or_build_pack(geo_context=geo_context)
    
    assert pack1["pack_hash"] == pack2["pack_hash"]
    assert pack1["destination_id"] == pack2["destination_id"]

def test_knowledge_pack_section_ttls():
    """Test that section TTL constants are strictly defined for cache lifecycle management."""
    assert FRESHNESS_TTL["STATIC"] == 30 * 86400
    assert FRESHNESS_TTL["SLOW"] == 3 * 86400
    assert FRESHNESS_TTL["DYNAMIC"] == 4 * 3600
    assert FRESHNESS_TTL["LIVE"] == 10 * 60

def test_rag_pack_first_retrieval_flow():
    """Test that asking a grounded query for a known destination uses the Knowledge Pack."""
    rag = GroundedRAGService()
    response = rag.answer_query(
        query="What is the ticket fee for Vittala Temple?",
        city_id=1,
        language="en"
    )
    assert "30" in response["answer"] or "ticket" in response["answer"].lower()
    assert response["verified"] is True
    assert "source" in response

def test_rag_cross_destination_resolution():
    """Test that asking about Bangalore while in Hampi session resolves to Bangalore knowledge without pollution."""
    rag = GroundedRAGService()
    response = rag.answer_query(
        query="What is the entry fee for Lalbagh in Bangalore?",
        city_id=1,  # Ambient is Hampi
        language="en"
    )
    # Must answer about Lalbagh or Bangalore, NOT Hampi Jolada rotti or Vittala temple
    assert "jolada rotti" not in response["answer"].lower()
    assert "lalbagh" in response["answer"].lower() or "30" in response["answer"]
    assert response["verified"] is True
