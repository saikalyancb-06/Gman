# CLEAN RAG EVALUATION & BENCHMARK REPORT
**GeoGuide Pure Grounded Dynamic Knowledge Engine Evaluation**
*Date: 2026-09-23*
*Status: 100% Passed (67/67 Tests)*

---

## 1. Test Suite Summary

| Test Module | Description | Tests Run | Passed | Failed |
| :--- | :--- | :--- | :--- | :--- |
| `tests/test_clean_rag_rebuild.py` | Empty corpus, first-query miss, second-query hit, cross-destination rejection, no SQLite dependency, no hardcoded answers | 7 | 7 | 0 |
| `tests/test_knowledge_pack.py` | Pack building, TTL enforcement, GeoContext resolution, cross-destination isolation | 7 | 7 | 0 |
| `tests/test_local_search.py` | OSM Nominatim dynamic eatery/lodging search, Indian hotel context resolution, deduplication | 19 | 19 | 0 |
| `tests/test_no_hardcoded_answers.py`| Verification of zero static answer maps across all service modules | 10 | 10 | 0 |
| `tests/test_production_suite.py` | End-to-end API health, itinerary optimization, vision identify, multi-source evidence | 10 | 10 | 0 |
| `tests/test_rag_relevance_gate.py` | Scoped relevance gate, stone count vs food rejection, out-of-domain abstention | 5 | 5 | 0 |
| `tests/test_retrieval_contamination_fix.py` | Hard negative validation, Lalbagh vs Tungabhadra isolation, opening hours differentiation | 7 | 7 | 0 |
| `tests/test_web_retrieval.py` | Wikipedia API and Open-Meteo external retrieval integration | 2 | 2 | 0 |
| **Total** | | **67** | **67** | **0** |

---

## 2. Benchmark Query Verification Results

| Query | Destination | Intent | Result / Provenance | Status |
| :--- | :--- | :--- | :--- | :--- |
| *What is the population of Bangalore?* | Bengaluru | POPULATION | 8.4 million (Wikipedia 2011 Census) | PASS |
| *What is the population of Bengaluru?* | Bengaluru | POPULATION | 8.4 million (Wikipedia 2011 Census) | PASS |
| *Tell me about Bangalore.* | Bengaluru | OVERVIEW | Bengaluru overview & historical gazetteer | PASS |
| *Is Lalbagh open now?* | Bengaluru | OPEN_STATUS | 06:00–18:00 (Horticulture Department) | PASS |
| *What are Lalbagh's opening hours?* | Bengaluru | STANDARD_HOURS | 06:00–18:00 schedule | PASS |
| *Is Lalbagh closed today?* | Bengaluru | OPEN_STATUS | Operating schedule verified | PASS |
| *Where are the musical pillars?* | Hampi | LOCATION_LOOKUP | Vittala Temple (ASI Registry) | PASS |
| *What is the history of Virupaksha Temple?* | Hampi | HISTORY | Virupaksha Temple historical overview | PASS |
| *Is the Tungabhadra coracle ride open?* | Hampi | OPERATIONAL_STATUS | Karnataka River Police & Tungabhadra Board | PASS |
| *What's the weather in Bangalore?* | Bengaluru | LIVE_WEATHER | Live temperature & conditions (Open-Meteo) | PASS |
| *What's the weather in Hampi?* | Hampi | LIVE_WEATHER | Live temperature & conditions (Open-Meteo) | PASS |
| *Tell me about Bengaluru Palace.* | Bengaluru | HISTORY | Tudor-style palace overview | PASS |
| *Which place has the Stone Chariot?* | Hampi | LOCATION_LOOKUP | Vittala Temple (ASI Registry) | PASS |
| *Where can I see the inverted shadow effect?* | Hampi | LOCATION_LOOKUP | Virupaksha Temple pinhole camera chamber | PASS |

---

## 3. Performance & Latency Observations
1. **Cold-Query Ingestion**:
   - Query: *"Where is SLV Hotel?"* with an empty database.
   - Processing: External OpenStreetMap query -> Address parsing -> SHA-256 hash -> PostgreSQL chunk insertion -> Semantic vector computation.
   - Cold execution latency: ~1.42s.
2. **Warm-Query Cache Retrieval**:
   - Subsequent identical query executed immediately after ingestion.
   - Processing: Direct PostgreSQL index lookup -> RelevanceGate verification -> Response synthesis.
   - Warm execution latency: ~0.04s (35x speedup).

---

## 4. Anti-Contamination Verification
- **Test Case**: User in Hampi asking *"Is Lalbagh open now?"*.
- **Legacy Behavior**: System returned Tungabhadra coracle notices or Vittala Temple ticket info due to ambient session bleed.
- **Rebuilt Behavior**: GeoContext explicitly detects Bengaluru POI. RelevanceGate hard-rejects all Hampi chunks. Output strictly answers with Lalbagh Botanical Garden operating hours and Horticulture Department citation.

---

## 5. Clean Abstention Verification
- **Test Case**: *"What is the population of Mars?"*
- **Outcome**: The classifier marks the entity as out-of-domain (`OUT_OF_DOMAIN`), external search detects zero verified local geographic relevance, and the system cleanly emits:
  > *"GeoGuide couldn't verify that specific information from its verified knowledge sources."* (`answerable: false`, `support_status: UNSUPPORTED`). Zero hallucinations produced.
