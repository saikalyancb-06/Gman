import time
import pytest
from backend.pg_database import reset_knowledge_corpus, get_pg_connection
from backend.vector_store import PgVectorStore
from backend.dynamic_pipeline import DynamicIngestionPipeline
from backend.rag_service import GroundedRAGService, QueryContext, RelevanceGate

@pytest.fixture(autouse=True)
def setup_empty_corpus():
    """Ensures each test starts with an explicitly clean and empty PostgreSQL knowledge corpus and reseeds after."""
    reset_knowledge_corpus()
    yield
    # Reseed baseline entities from activities_poi and local businesses after clean rebuild tests run
    try:
        conn = get_pg_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT id, name, city_id, short_desc, lat, lng FROM activities_poi")
            pois = cur.fetchall()
            for p in pois:
                cur.execute(
                    "INSERT INTO entities (name, entity_type, city_id, latitude, longitude, category, address) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING;",
                    (p[1], 'POI', p[2], p[4], p[5], 'Heritage / Monument', p[3])
                )
            cur.execute(
                "INSERT INTO entities (name, entity_type, city_id, latitude, longitude, category, address) "
                "VALUES ('SLV Hotel', 'POI', 2, 12.9430, 77.5730, 'Food / Restaurant', 'Gandhi Bazaar, Basavanagudi') "
                "ON CONFLICT DO NOTHING;"
            )
        conn.close()
    except Exception:
        pass

def test_1_empty_corpus_state():
    """Verify that after reset, all factual RAG tables are empty."""
    store = PgVectorStore()
    assert store.count_chunks() == 0
    
    conn = get_pg_connection()
    with conn.cursor() as cur:
        for t in ['knowledge_chunks', 'knowledge_documents', 'knowledge_sources', 'web_cache', 'entities', 'operational_status']:
            cur.execute(f"SELECT count(*) FROM {t}")
            assert cur.fetchone()[0] == 0, f"Table {t} was not empty after reset"
    conn.close()

def test_2_first_query_external_ingestion_and_second_query_cache():
    """
    Test empty-corpus -> external-retrieval -> database-ingestion.
    First query: database miss -> dynamic external retrieval -> store -> answer.
    Second query: database hit -> faster latency, identical provenance.
    """
    rag = GroundedRAGService()
    store = PgVectorStore()
    
    # Pre-condition: corpus is 0
    assert store.count_chunks() == 0
    
    # First Query
    t0 = time.time()
    res1 = rag.answer_query("Where is SLV Hotel?", language="en", city_id=2, city_name="Bengaluru")
    t1 = time.time()
    latency_query_1 = t1 - t0
    
    assert res1["answerable"] is True
    assert "slv" in res1["answer"].lower()
    assert res1["retrieval_mode"] in ["LOCAL_PLACES_SEARCH", "WEB_RETRIEVAL"]
    assert "OpenStreetMap" in res1["source"] or "Verified" in res1["source_tag"]
    
    # Assert new chunks were actually stored in PostgreSQL
    chunk_count_after_1 = store.count_chunks()
    assert chunk_count_after_1 > 0, "No chunks were persisted to PostgreSQL after first query"
    
    # Second Query
    t2 = time.time()
    res2 = rag.answer_query("Where is SLV Hotel?", language="en", city_id=2, city_name="Bengaluru")
    t3 = time.time()
    latency_query_2 = t3 - t2
    
    assert res2["answerable"] is True
    assert "slv" in res2["answer"].lower()
    # Query 2 should be faster or hit cache
    assert latency_query_2 <= latency_query_1 + 0.5
    # No duplicate chunks created
    assert store.count_chunks() == chunk_count_after_1

def test_3_population_dynamic_retrieval_and_persistence():
    """Verify that asking for population retrieves from external source and persists."""
    rag = GroundedRAGService()
    store = PgVectorStore()
    assert store.count_chunks() == 0
    
    res = rag.answer_query("What is the population of Bengaluru?", language="en", city_id=2, city_name="Bengaluru")
    assert res["attribute"] == "POPULATION"
    assert res["answerable"] is True
    assert any(num in res["answer"] for num in ["8.4 million", "8.5 million", "8 million", "million"])
    assert store.count_chunks() > 0

def test_4_cross_destination_contamination_rejected():
    """Hampi / Tungabhadra queries must not contaminate Bangalore queries."""
    rag = GroundedRAGService()
    res = rag.answer_query("Is Lalbagh open now?", city_id=1, language="en")
    assert res["resolved_entity"] == "Lalbagh Botanical Garden & Glass House"
    assert res["destination"] == "Bengaluru"
    assert "tungabhadra" not in res["answer"].lower()
    assert "hampi" not in res["answer"].lower()

def test_5_unsupported_out_of_domain_abstains_cleanly():
    """Queries for Mars population or alien life must abstain cleanly without hallucinating."""
    rag = GroundedRAGService()
    res = rag.answer_query("What is the population of Mars?", language="en")
    assert res["answerable"] is False
    assert res["support_status"] == "UNSUPPORTED"
    assert "couldn't verify" in res["answer"].lower()

def test_6_no_sqlite_rag_dependency():
    """Verify SQLite no longer contains place_kb or poi_facts_kb tables."""
    import sqlite3
    import os
    db_path = os.path.join(os.path.dirname(__file__), '..', 'backend', 'geoguide.db')
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('place_kb', 'poi_facts_kb')")
    found = cur.fetchall()
    conn.close()
    assert len(found) == 0, f"Found deprecated RAG tables in SQLite: {found}"

def test_7_no_hardcoded_answers_in_code():
    """Check that rag_service does not have static question-to-answer hardcoded dictionaries."""
    import inspect
    from backend import rag_service
    source = inspect.getsource(rag_service)
    assert 'if query == "where is slv hotel":' not in source.lower()
    assert 'answers = {' not in source.lower()
    assert 'if query contains "slv":' not in source.lower()
