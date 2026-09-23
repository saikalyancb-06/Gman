# RAG REBUILD SPECIFICATION & ARCHITECTURE
**GeoGuide Pure Grounded Dynamic Knowledge Engine**
*Version: 2.0-Canonical*

---

## 1. Architectural Overview
The rebuilt GeoGuide RAG engine completely decouples knowledge persistence from local application code. It operates under a **Zero-Hardcoded-Knowledge Policy**: no factual answers, coordinates, or opening hours are statically embedded inside Python source code or prompts.

```
                           User Query
                               |
                               v
                     +-------------------+
                     | QueryContext      |
                     | Understanding     |
                     +-------------------+
                               |
              +----------------+----------------+
              |                                 |
              v                                 v
    [Local Places Search]             [Pack-Scoped Retrieval]
    (OSM Nominatim API)               (PostgreSQL / PgVector)
              |                                 |
              |                                 v
              |                       +-------------------+
              |                       | RelevanceGate     |
              |                       | Validation        |
              |                       +-------------------+
              |                        /                 \
              |                   [Accepted]         [Rejected / Miss]
              |                       |                      |
              |                       |                      v
              |                       |             [Dynamic Web Pipeline]
              |                       |             (Wikipedia API / Meteo)
              |                       |                      |
              |                       |                      v
              |                       |             [Persist to PostgreSQL]
              \                       |                      /
               \                      |                     /
                v                     v                    v
              +---------------------------------------------+
              | Grounded Response Generation & Provenance   |
              +---------------------------------------------+
```

---

## 2. Ingestion Pipeline & Normalization
The dynamic pipeline (`backend/dynamic_pipeline.py`) performs:
1. **Dynamic Discovery**:
   - `discover_and_ingest_fact`: Connects to Wikipedia API for institutional history, demographic censuses, and city overviews.
   - `discover_and_ingest_local_business`: Connects to OpenStreetMap Nominatim for local restaurants, cafes, eateries, and lodges.
   - Live Weather: Connects to Open-Meteo for real-time temperature, precipitation, and conditions.
2. **Indian Local Context Normalization**:
   - Resolves ambiguous "Hotel" terms into eateries (`RESTAURANT`) or lodging (`ACCOMMODATION`) based on contextual indicators (e.g., "dosa", "idli", "meals", "coffee", "darshini" -> Restaurant).
3. **Chunking & Vectorization**:
   - Content is chunked into focused semantic passages.
   - Text is embedded into unit-normalized 384-dimensional dense vectors using a deterministic semantic embedding model (`backend/vector_store.py`).
4. **PostgreSQL Persistence**:
   - Inserted into `knowledge_documents` and `knowledge_chunks` with SHA-256 deduplication via `content_hash`.

---

## 3. Two-Tier Retrieval & Latency Acceleration
- **First Query (Cold Miss)**:
  1. No existing chunk passes relevance gate in PostgreSQL.
  2. Pipeline calls external authority (Wikipedia/OSM/Meteo).
  3. Validates and normalizes external payload.
  4. Stores chunk + embedding in PostgreSQL (`knowledge_chunks`).
  5. Synthesizes grounded response citing external authority.
- **Second Query (Warm Hit)**:
  1. PostgreSQL vector query hits existing validated chunk.
  2. RelevanceGate confirms destination and entity alignment.
  3. Instant cache-accelerated response (measured latency drop from ~1.5s to <0.05s).

---

## 4. RelevanceGate & Contamination Rejection
To prevent cross-destination pollution (e.g. asking about Lalbagh in Bangalore while ambient city is Hampi):
1. **Geo-Scoping**: Checks `destination_id` and filters out documents belonging to mismatched cities.
2. **Entity Consistency**: Validates that retrieved POIs match requested entities and rejects false matches (e.g. rejecting Vittala musical pillars for a Virupaksha query).
3. **Attribute Consistency**: Ensures population queries reject general tourism descriptions and require numerical population figures.
4. **Clean Abstention**: If external retrieval cannot find verified information, the system returns `answerable: false` and abstains cleanly rather than hallucinating.
