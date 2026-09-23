import pytest
from backend.rag_service import GroundedRAGService, QueryIntentClassifier

def test_stones_query_abstains_and_no_food():
    """1. How many stones are there in Hampi? -> Must NOT return food / must abstain or state unverified."""
    rag = GroundedRAGService()
    res = rag.answer_query("How many stones are there in Hampi?", language="en", city_id=1, city_name="Hampi")
    ans_lower = res["answer"].lower()
    
    assert "jolada" not in ans_lower
    assert "rotti" not in ans_lower
    assert "ennegayi" not in ans_lower
    assert "brinjal" not in ans_lower
    assert res["support_status"] in ["UNSUPPORTED", "PARTIALLY_SUPPORTED"]

def test_bangalore_weather_query():
    """2. What is the best thing about Bangalore weather? -> Must use Bangalore/weather evidence, no Hampi food."""
    rag = GroundedRAGService()
    res = rag.answer_query("What is the best thing about Bangalore weather?", language="en", city_id=1, city_name="Hampi")
    ans_lower = res["answer"].lower()
    
    assert "jolada" not in ans_lower
    assert "rotti" not in ans_lower
    assert "weather" in ans_lower or "climate" in ans_lower or "bengaluru" in ans_lower or "temperature" in ans_lower

def test_bangalore_live_weather():
    """3. What is the weather in Bangalore right now? -> Must call live weather API."""
    rag = GroundedRAGService()
    res = rag.answer_query("What is the weather in Bangalore right now?", language="en", city_id=1, city_name="Hampi")
    ans_lower = res["answer"].lower()
    
    assert "bengaluru" in ans_lower or "bangalore" in ans_lower
    assert "°c" in res["answer"] or "temperature" in ans_lower or "humidity" in ans_lower
    assert "Open-Meteo" in res["source"] or "Live Weather" in res["source_tag"]
    assert res["verified"] is True

def test_jolada_rotti_food_query():
    """4. What is Jolada rotti? -> Food chunk used ONLY for food."""
    rag = GroundedRAGService()
    res = rag.answer_query("What is Jolada rotti?", language="en", city_id=1, city_name="Hampi")
    ans_lower = res["answer"].lower()
    
    assert "jolada rotti" in ans_lower or "millet" in ans_lower or "flatbread" in ans_lower
    assert res["support_status"] == "SUPPORTED"
    assert res["verified"] is True

def test_virupaksha_history_query():
    """5. What is the history of Virupaksha Temple? -> Virupaksha RAG evidence."""
    rag = GroundedRAGService()
    res = rag.answer_query("What is the history of Virupaksha Temple?", language="en", city_id=1, city_name="Hampi")
    ans_lower = res["answer"].lower()
    
    assert "virupaksha" in ans_lower
    assert "shiva" in ans_lower or "gopura" in ans_lower or "temple" in ans_lower or "vijayanagara" in ans_lower
    assert "jolada" not in ans_lower

def test_tungabhadra_coracle_status():
    """6. What is the current status of the Tungabhadra coracle service? -> River advisory evidence."""
    rag = GroundedRAGService()
    res = rag.answer_query("What is the current status of the Tungabhadra coracle service?", language="en", city_id=1, city_name="Hampi")
    ans_lower = res["answer"].lower()
    
    assert "tungabhadra" in ans_lower or "coracle" in ans_lower or "river" in ans_lower
    assert "suspended" in ans_lower or "bukkasagara" in ans_lower or "advisory" in ans_lower or "bridge" in ans_lower

def test_mars_population_clean_abstention():
    """7. What is the population of Mars? -> Clean abstention (no Hampi/food)."""
    rag = GroundedRAGService()
    res = rag.answer_query("What is the population of Mars?", language="en", city_id=1, city_name="Hampi")
    ans_lower = res["answer"].lower()
    
    assert "jolada" not in ans_lower
    assert "rotti" not in ans_lower
    assert res["support_status"] == "UNSUPPORTED"
    assert res["verified"] is False
    assert res["answerable"] is False

def test_capital_of_karnataka():
    """8. What is the capital of Karnataka? -> Bengaluru evidence or city overview."""
    rag = GroundedRAGService()
    res = rag.answer_query("What is the capital of Karnataka?", language="en", city_id=1, city_name="Hampi")
    ans_lower = res["answer"].lower()
    
    assert "jolada" not in ans_lower
    assert "rotti" not in ans_lower

def test_mysore_query():
    """9. Tell me something interesting about Mysore. -> Mysore evidence."""
    rag = GroundedRAGService()
    res = rag.answer_query("Tell me something interesting about Mysore.", language="en", city_id=1, city_name="Hampi")
    ans_lower = res["answer"].lower()
    
    assert "jolada" not in ans_lower
    assert "rotti" not in ans_lower
    assert "mysur" in ans_lower or "mysore" in ans_lower or "palace" in ans_lower or "karnataka" in ans_lower

def test_is_it_raining_bangalore():
    """10. Is it raining in Bangalore right now? -> Live weather API check."""
    rag = GroundedRAGService()
    res = rag.answer_query("Is it raining in Bangalore right now?", language="en", city_id=1, city_name="Hampi")
    ans_lower = res["answer"].lower()
    
    assert "bengaluru" in ans_lower or "bangalore" in ans_lower
    assert "Open-Meteo" in res["source"] or "Live Weather" in res["source_tag"]
    assert res["verified"] is True
