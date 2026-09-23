# CLEAN DATA MIGRATION REPORT
**GeoGuide Knowledge Layer Reset & PostgreSQL Rebuild**
*Timestamp: 2026-09-23T16:40:00+05:30*
*Environment: Windows / PostgreSQL 17 / Python 3.14*

---

## 1. Executive Summary
The GeoGuide knowledge layer underwent a comprehensive clean reset to eliminate data contamination, attribute mismatch, and hallucinated responses caused by legacy SQLite and mock vector stores. 

Before any destructive action was taken:
1. A complete inventory and forensic audit of all existing database tables was performed.
2. A binary SQLite snapshot, a deterministic SQL dump, and a JSON manifest with SHA-256 integrity checksums were archived into `data/backups/`.
3. Contaminated application and RAG knowledge tables (`place_kb`, `poi_facts_kb`, legacy embedding caches) were permanently removed.
4. A canonical PostgreSQL knowledge store was deployed with a normalized schema, PostGIS/spatial capabilities, and dense semantic vector persistence.

---

## 2. Pre-Destructive Inventory & Backup Manifest
Prior to dropping tables, the backup script `scripts/backup_pre_reset.py` recorded the complete state:
- **Binary Backup File**: `data/backups/geoguide_pre_reset_20260923_163908.db` (SHA-256: `7d046f4b6fb7d4a22c54ca55e648c66ba6f987e9ecdbff1c43f728fa54f85e3a`)
- **SQL Dump File**: `data/backups/geoguide_pre_reset_20260923_163908.sql` (SHA-256: `e081122a210d797171d18f5d082fc89d53c20c0c6eef9bf9c394801122703831`)
- **JSON Manifest**: `data/backups/inventory_manifest_20260923_163908.json`
- **Total Tables Recorded**: 21 tables, 77 rows.
- **Reference Package Preserved**: The original canonical package `data/source/ps13_original.sqlite` was retained untouched as an immutable archived reference.

---

## 3. Contaminated Tables Dropped & Purged
The following contaminated tables were permanently dropped from the runtime database:
- `place_kb` (purged and removed from schema)
- `poi_facts_kb` (purged and removed from schema)
- In-memory mock FAISS vector indexes and TF-IDF cache matrices

---

## 4. Canonical PostgreSQL Knowledge Persistence
PostgreSQL 17 was configured as the single source of truth for all RAG and dynamic knowledge retrieval (`postgresql://geoguide:geoguide@127.0.0.1:5432/geoguide`). The relational schema enforces:
1. `entities`: Canonical places, cities, and landmarks with GPS coordinates, tags, and aliases.
2. `knowledge_sources`: Verified provenance registries (OpenStreetMap, Wikipedia API, Archaeological Survey of India, Open-Meteo).
3. `knowledge_documents`: Ingested external documents with content hashes and update timestamps.
4. `knowledge_chunks`: Cleanly chunked passages with topic classification, city scoping, and 384-dimensional unit-normalized semantic embeddings (`vector(384)` / `float8[]`).
5. `web_cache`: External API cache with TTL tracking and HTTP response hashes.
6. `operational_status`: Verified open/closed notices and seasonal hours.

---

## 5. Verification & Test Confirmation
- Pre-reset row count: 77 legacy rows across 21 tables.
- Post-reset factual knowledge row count: Exactly 0 rows upon corpus reset.
- Dynamic Ingestion: 100% of factual knowledge is discovered, validated, and persisted dynamically through external APIs (OSM Nominatim, Wikipedia API, Open-Meteo).
- All 67 automated regression and clean-rebuild unit tests pass without error.
