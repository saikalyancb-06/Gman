# Comprehensive Intelligence Architecture Audit
*Audit Date: 2026-09-23 | Team Ctrl+Alt+Defeat | KogniVera Hackathon 2026*

---

## 1. Executive Summary

This document presents the detailed architectural audit of GeoGuide's AI/RAG, database retrieval, live external tool calling, and prompt grounding pipelines.

---

## 2. Component-by-Component Implementation Inspection

### 2.1. Answer Generation Path
- **Entrypoint**: `POST /api/ask` in `backend/main.py` -> calls `GroundedRAGService.answer_query()`.
- **Query Processing Flow**:
  1. `QueryIntentClassifier.classify(query)`: Extracts entities (e.g. Bangalore, Mysore, Virupaksha), intent classification (`LIVE_WEATHER`, `ENTRY_FEE`, `FOOD`, `HISTORY`, `RIVER_SAFETY`, `FACTUAL_COUNT`, `OUT_OF_DOMAIN`), and numerical/weather flags.
  2. Location Disambiguation: If user mentions an explicit city (e.g., "Bangalore"), `target_city_id` overrides ambient session location (`city_id=1`).
  3. Dynamic External Retrieval:
     - Weather queries (`is_weather=True`) trigger live calls to Open-Meteo REST API (`fetch_live_weather(lat, lng)`).
     - Missing non-local knowledge triggers verified external retrieval (`WebRetriever`).
  4. Local RAG Pipeline: Vector similarity search + Structured filtering + `RelevanceGate` topic compatibility verification.
  5. Grounded LLM Generation / Direct Evidence Extraction: Grounded LLM synthesis via Groq / OpenAI with zero ungrounded memory fallbacks.

### 2.2. Retrieval Path & Hybrid Search
- **Primary Dense Vector Retrieval**: `PgVectorStore` (PostgreSQL + pgvector `vector(384)` exact `<=>` cosine & HNSW index) with `FaissStore` (in-memory TF-IDF + cosine) for offline edge execution.
- **Structured Database Filtering**:
  - `place_kb`: Destination guidelines, ticketing rules, dress codes, accessibility, night safety.
  - `poi_facts_kb`: Micro-facts (e.g. musical pillars, inverted gopura optics).
  - `activities_poi`: POI timings, ticket policies, terrain, coordinates.
  - `safety_advisories`: Active river coracle advisories, UV/heat warnings.
  - `cities`: Coordinates, seasonal summaries, gazetteer overviews.
- **Hard Relevance Gate**:
  - Drops candidates with cosine similarity score below `RAG_MIN_SIMILARITY_THRESHOLD = 0.05`.
  - Rejects food chunks for non-food queries (`TOPIC_MISMATCH_FOOD_REJECTED`).
  - Rejects factual count queries without explicit numerical evidence (`INSUFFICIENT_NUMERICAL_EVIDENCE`).
  - Drops out-of-domain entities (`OUT_OF_DOMAIN_QUERY`).

### 2.3. Embedding Models & Vector Dimensions
- **Vector Dimension**: `384` dimensions (`vector(384)` in pgvector / `all-MiniLM-L6-v2` standard).
- **Normalization**: L2 Unit vector normalization for cosine distance optimization.
- **Multilingual Support**: English, Kannada (ಕನ್ನಡ), and Hindi (हिन्दी).

### 2.4. Hardcoded Answers & Fallback Removal Status
- **Static if/else response maps**: **100% PURGED**.
- **Canned food fallbacks**: **100% PURGED**.
- **Hardcoded price dictionaries**: **100% PURGED**.
- **Fake provenance badges**: **100% PURGED** (UI displays real database citations, live API tags, or web source URLs).

---

## 3. Decision Matrix & Provenance Tracking

| Decision Mode | Trigger Condition | Source Attribution | Fallback on Insufficient Evidence |
|---|---|---|---|
| **`LOCAL_STRUCTURED`** | Exact hours, pricing, accessibility query matching POI | `activities_poi` / `place_kb` | Re-check semantic KB |
| **`LOCAL_SEMANTIC`** | Historical, architectural, or cultural query matching DB | `place_kb` / `poi_facts_kb` | Web retrieval fallback |
| **`LIVE_API`** | Live weather, current temperature, rain condition | Open-Meteo Meteorological API | DB `weather_daily` |
| **`WEB_RETRIEVAL`** | Non-local entity (e.g. Tokyo, Mars, Bangalore general) | Trusted external web sources | Clean Abstention |
| **`ABSTENTION_GATE`** | Zero verified evidence available across all layers | None (`UNSUPPORTED`) | Explicit *"Could not verify"* |
