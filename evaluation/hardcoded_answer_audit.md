# Hardcoded Answer Removal & Grounded RAG Audit Report
*System Audit: Zero Hardcoded / Canned Responses Policy Enforcement*  
*Date: 2026-09-23 | Team Ctrl+Alt+Defeat | KogniVera Hackathon 2026*

---

## 1. Executive Summary

An exhaustive codebase audit was conducted across GeoGuide's frontend and backend systems to identify and permanently purge all hardcoded answers, static response dictionaries, and canned fallbacks.

All answers returned by GeoGuide are now **100% grounded in verified retrieved evidence** or **real-time external APIs** (Open-Meteo Weather API), with strict abstention (`UNSUPPORTED` status) whenever verifiable evidence is unavailable.

---

## 2. Hardcoded Answer Deletion Log

The following canned answers, static fallback blocks, and hardcoded dictionary mappings were permanently removed from `backend/rag_service.py`:

| # | Removed Logic / Block | Previous Hardcoded Behavior | New Grounded / Dynamic Architecture |
|---|---|---|---|
| **1** | `if intent == "ENTRY_FEE": answer_en = "One ASI combined ticket of ₹30..."` | Returned static Hampi ticket text for any query classified as ticket fee (including Bangalore or other cities). | Dynamic vector retrieval with `topic="ticketing_rules"` filtering and entity constraints. |
| **2** | `elif intent == "FOOD": answer_en = "Iconic local Karnataka delicacies in Hampi include Jolada rotti..."` | **CRITICAL FAILURE**: Returned Jolada rotti food text for unrelated queries (e.g. "how many stones are there in Hampi", "Bangalore weather"). | Hard `RelevanceGate` filtering: Food chunks are **strictly prohibited** unless the query intent is explicitly food-related. |
| **3** | `elif intent == "DRESS_CODE": answer_en = "At active shrines like Virupaksha..."` | Canned temple etiquette text. | Grounded extraction from `place_kb` (`dress_code_etiquette`). |
| **4** | `elif intent == "ACCESSIBILITY": answer_en = "Lotus Mahal, Zenana Enclosure..."` | Canned accessibility summary. | Grounded extraction from `place_kb` (`accessibility_wheelchair`). |
| **5** | `elif intent == "SUNSET_VIEWPOINT": answer_en = "Hemakuta Hill is just 2 minutes..."` | Canned sunset hill response. | Dynamic retrieval against `activities_poi` terrain & `best_time_window`. |
| **6** | `elif intent == "RIVER_SAFETY": answer_en = "Coracle crossings on the Tungabhadra..."` | Canned coracle text. | Dynamic retrieval from `safety_advisories` table (`is_active = 1`). |
| **7** | Static Multilingual Dictionaries (`answer_kn`, `answer_hi`) | Hardcoded Kannada and Hindi canned strings. | Dynamic synthesis via Groq / multi-language translation and verified bilingual citations. |

---

## 3. Benchmark Verification Across 10 Critical Test Queries

All 10 benchmark queries have been automated in `tests/test_no_hardcoded_answers.py` and pass with 100% precision:

```
================================================================================
Query 1: "How many stones are there in Hampi?"
Intent: FACTUAL_COUNT | City: Hampi
Gate: REJECTED (Food chunks) -> Clean Abstention
Result: "GeoGuide couldn't verify that specific information from its verified knowledge sources for Hampi."
Status: UNSUPPORTED | verified: False | Jolada Rotti Leak: NO
--------------------------------------------------------------------------------
Query 2: "What is the best thing about Bangalore weather?"
Intent: LIVE_WEATHER | City: Bengaluru
Retrieval: Live Open-Meteo Meteorological API (12.9716°N, 77.5946°E)
Result: "Current temperature in Bengaluru is 24°C with pleasant conditions and 65% humidity."
Status: SUPPORTED | verified: True | Jolada Rotti Leak: NO
--------------------------------------------------------------------------------
Query 3: "What is the weather in Bangalore right now?"
Intent: LIVE_WEATHER | City: Bengaluru
Retrieval: Open-Meteo API Real-Time
Status: SUPPORTED | verified: True
--------------------------------------------------------------------------------
Query 4: "What is Jolada rotti?"
Intent: FOOD | City: Hampi
Retrieval: activities_poi & place_kb (food_culinary)
Result: "Jolada rotti with ennegayi: Millet flatbread with stuffed brinjal, the staple of this part of Karnataka."
Status: SUPPORTED | verified: True
--------------------------------------------------------------------------------
Query 5: "What is the history of Virupaksha Temple?"
Intent: HISTORY | City: Hampi
Retrieval: activities_poi (Virupaksha Temple) & poi_facts_kb
Result: "Virupaksha Temple: In worship for centuries, with a 50 m eastern gopura. One of India's oldest continuously functioning temples dedicated to Lord Shiva."
Status: SUPPORTED | verified: True
--------------------------------------------------------------------------------
Query 6: "What is the current status of the Tungabhadra coracle service?"
Intent: RIVER_SAFETY | City: Hampi
Retrieval: safety_advisories (Coracle crossings suspended)
Result: "Coracle crossings suspended: The Tungabhadra is in spate after upstream releases. Cross to Anegundi by the Bukkasagara road bridge instead (40 min auto)."
Status: SUPPORTED | verified: True
--------------------------------------------------------------------------------
Query 7: "What is the population of Mars?"
Intent: OUT_OF_DOMAIN
Gate: REJECTED (Out of Domain) -> Clean Abstention
Result: "GeoGuide couldn't verify that specific information from its verified knowledge sources."
Status: UNSUPPORTED | verified: False | answerable: False
--------------------------------------------------------------------------------
Query 8: "What is the capital of Karnataka?"
Intent: GENERAL_QUERY | Entity: Karnataka
Retrieval: cities (Bengaluru overview)
Status: SUPPORTED | verified: True
--------------------------------------------------------------------------------
Query 9: "Tell me something interesting about Mysore."
Intent: GENERAL_QUERY | City: Mysuru
Retrieval: cities & place_kb (Mysuru overview)
Status: SUPPORTED | verified: True
--------------------------------------------------------------------------------
Query 10: "Is it raining in Bangalore right now?"
Intent: LIVE_WEATHER | City: Bengaluru
Retrieval: Live Open-Meteo Meteorological API
Status: SUPPORTED | verified: True
================================================================================
```

---

## 4. Test Suite Execution Summary

```bash
python -m pytest tests/
============================= test session starts =============================
collected 25 items

tests/test_no_hardcoded_answers.py ..........                            [ 40%]
tests/test_production_suite.py ..........                                [ 80%]
tests/test_rag_relevance_gate.py .....                                   [100%]

============================== 25 passed in 5.86s ==============================
```
