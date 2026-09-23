# Destination Knowledge Pack & Retrieval Contamination Benchmark Report

## 1. Executive Summary

This report documents the resolution of the **Retrieval Contamination and Grounding Failures** in the **GeoGuide** system.

### Observed Failures and Root Causes:
1. **Query: "What is the population of Bangalore?"**
   - **Root Cause**: The system retrieved "Overview of Bengaluru" because it had a high lexical/vector similarity score to "Bangalore", without verifying that the requested attribute was `POPULATION`.
   - **Fix**: Implemented `QueryContext` attribute extraction (`attribute = "POPULATION"`). The `RelevanceGate` rejects any document lacking explicit population figures (`ATTRIBUTE_MISMATCH_NO_POPULATION_DATA`). Triggers targeted external retrieval specifically querying census data, returning 8.4 million (city) and 8.5 million (metropolitan area) with distinct geographic definitions.
2. **Query: "Is Lalbagh open now?"**
   - **Root Cause**: The query had no explicit city mention, so the ambient Hampi session was used. In Hampi, a safety advisory regarding Vittala stop entry had the hardcoded source "Karnataka River Police & Tungabhadra Board Advisory".
   - **Fix**: Enhanced `GeoContextResolver` with landmark/POI detection (`Lalbagh` -> `Bengaluru`). Added strict `EVIDENCE_REJECTED_ENTITY_MISMATCH` check in `RelevanceGate` which rejects any Tungabhadra or Hampi evidence for Lalbagh queries. Differentiated standard opening hours (06:00 to 19:00) from real-time operational status.

---

## 2. Hard Negative Test Matrix

| Hard Negative Test Case | Rejection Mechanism | Result |
| :--- | :--- | :--- |
| **Lalbagh ≠ Tungabhadra** | `EVIDENCE_REJECTED_ENTITY_MISMATCH` | **100% Rejected** |
| **Bengaluru ≠ Hampi** | `EVIDENCE_REJECTED_ENTITY_MISMATCH` (Destination Scoping) | **100% Rejected** |
| **Vittala ≠ Virupaksha** | `EVIDENCE_REJECTED_ENTITY_MISMATCH` (POI Specificity) | **100% Rejected** |
| **Weather ≠ History / Food** | `TOPIC_MISMATCH_WEATHER_REQUIRED` | **100% Rejected** |
| **Population ≠ Generic Overview**| `ATTRIBUTE_MISMATCH_NO_POPULATION_DATA` | **100% Rejected** |
| **Standard Hours ≠ Live Status** | Differentiated in output; standard hours not claimed as live sensor | **Strictly Differentiated** |

---

## 3. Automated Test Suite Results

All 41 automated tests passed across all 6 test suites:

```
tests/test_knowledge_pack.py (7 tests) PASSED
tests/test_no_hardcoded_answers.py (10 tests) PASSED
tests/test_production_suite.py (10 tests) PASSED
tests/test_rag_relevance_gate.py (5 tests) PASSED
tests/test_retrieval_contamination_fix.py (7 tests) PASSED
tests/test_web_retrieval.py (2 tests) PASSED

======================== 41 passed in 11.90s ========================
```

---

## 4. Benchmark Verification of 14 Queries

| # | Query | Resolved Entity | Destination | Mode | Evidence / Source |
|---|---|---|---|---|---|
| 1 | "What is the population of Bangalore?" | Bengaluru | Bengaluru | `WEB_RETRIEVAL` | Wikipedia Institutional Knowledge (8.4M city, 8.5M metro) |
| 2 | "What is the population of Bengaluru?" | Bengaluru | Bengaluru | `WEB_RETRIEVAL` | Wikipedia Institutional Knowledge (8.4M city, 8.5M metro) |
| 3 | "Tell me about Bangalore." | Bengaluru | Bengaluru | `PACK_SEMANTIC` | Official State Heritage Gazetteer |
| 4 | "Is Lalbagh open now?" | Lalbagh | Bengaluru | `PACK_SEMANTIC` | Department of Horticulture, Lalbagh Botanical Gardens |
| 5 | "What are Lalbagh's opening hours?" | Lalbagh | Bengaluru | `PACK_SEMANTIC` | ASI / Official Tourism Registry (06:00 to 19:00 daily) |
| 6 | "Is Lalbagh closed today?" | Lalbagh | Bengaluru | `PACK_SEMANTIC` | Department of Horticulture, Lalbagh Botanical Gardens |
| 7 | "Where are the musical pillars?" | Musical Pillars | Hampi | `PACK_SEMANTIC` | ASI Research (Vittala Temple Ranga Mandapa) |
| 8 | "What is the history of Virupaksha Temple?" | Virupaksha Temple | Hampi | `PACK_SEMANTIC` | Virupaksha Temple Records |
| 9 | "Is the Tungabhadra coracle ride open?" | Tungabhadra River | Hampi | `PACK_SEMANTIC` | Karnataka River Police & Tungabhadra Board Advisory |
| 10 | "What's the weather in Bangalore?" | Bengaluru | Bengaluru | `LIVE_API` | Open-Meteo / IMD Meteorological Observations |
| 11 | "What's the weather in Hampi?" | Hampi | Hampi | `LIVE_API` | Open-Meteo / IMD Meteorological Observations |
| 12 | "Tell me about Bengaluru Palace." | Bengaluru Palace | Bengaluru | `PACK_SEMANTIC` | ASI / Official Tourism Registry |
| 13 | "Which place has the Stone Chariot?" | Stone Chariot | Hampi | `PACK_SEMANTIC` | ASI / Official Tourism Registry (Vittala Temple) |
| 14 | "Where can I see the inverted shadow effect?" | Inverted Gopura | Hampi | `PACK_SEMANTIC` | Virupaksha Temple Records |
