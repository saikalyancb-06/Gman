# KNOWLEDGE SCHEMA SPECIFICATION
**GeoGuide Canonical PostgreSQL + PostGIS & Vector Storage**
*Database: PostgreSQL 17*
*Connection: postgresql://geoguide:geoguide@127.0.0.1:5432/geoguide*

---

## 1. Schema Diagram

```
                 +----------------------+
                 |        cities        |
                 +----------------------+
                    |                |
                    | 1:N            | 1:N
                    v                v
          +-----------------+   +-------------------------+
          |     entities    |   |    knowledge_chunks     |<-----+
          +-----------------+   +-------------------------+      |
                    |                        ^                   |
                    | 1:N                    | 1:N               |
                    v                        |                   |
       +-------------------------+           |                   | 1:N
       |   operational_status    |           |                   |
       +-------------------------+           |                   |
                                             |                   |
       +-------------------------+           |                   |
       |    knowledge_sources    |           |                   |
       +-------------------------+           |                   |
                    |                        |                   |
                    | 1:N                    |                   |
                    v                        |                   |
       +-------------------------+           |                   |
       |   knowledge_documents   |-----------+                   |
       +-------------------------+                               |
                                                                 |
       +-------------------------+                               |
       |        web_cache        |-------------------------------+
       +-------------------------+
```

---

## 2. Table Definitions

### `entities`
Canonical places, monuments, parks, and local businesses.
```sql
CREATE TABLE entities (
    id SERIAL PRIMARY KEY,
    city_id INTEGER REFERENCES cities(id),
    name VARCHAR(255) NOT NULL,
    category VARCHAR(64) NOT NULL,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    address TEXT,
    osm_id VARCHAR(64),
    tags JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### `knowledge_sources`
Catalog of trusted external authorities and endpoints.
```sql
CREATE TABLE knowledge_sources (
    id SERIAL PRIMARY KEY,
    name VARCHAR(128) NOT NULL UNIQUE,
    source_type VARCHAR(64) NOT NULL,
    base_url TEXT,
    trust_tier VARCHAR(32) DEFAULT 'PRIMARY',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### `knowledge_documents`
Raw documents ingested from external sources.
```sql
CREATE TABLE knowledge_documents (
    id SERIAL PRIMARY KEY,
    source_id INTEGER REFERENCES knowledge_sources(id),
    city_id INTEGER REFERENCES cities(id),
    title VARCHAR(255) NOT NULL,
    url TEXT,
    content_hash VARCHAR(64) UNIQUE NOT NULL,
    raw_content TEXT,
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP
);
```

### `knowledge_chunks`
Granular semantic passages equipped with 384-dimensional dense semantic vectors.
```sql
CREATE TABLE knowledge_chunks (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES knowledge_documents(id) ON DELETE CASCADE,
    city_id INTEGER REFERENCES cities(id),
    entity_id INTEGER REFERENCES entities(id),
    topic VARCHAR(64) NOT NULL,
    title VARCHAR(255) NOT NULL,
    chunk_text TEXT NOT NULL,
    embedding DOUBLE PRECISION[] NOT NULL,
    source_name VARCHAR(128) NOT NULL,
    source_url TEXT,
    content_hash VARCHAR(64) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### `web_cache`
API response caching with cryptographic checksums and TTL enforcement.
```sql
CREATE TABLE web_cache (
    cache_key VARCHAR(128) PRIMARY KEY,
    url TEXT NOT NULL,
    response_json JSONB NOT NULL,
    response_hash VARCHAR(64) NOT NULL,
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ttl_seconds INTEGER DEFAULT 86400
);
```

### `operational_status`
Real-time notices, temporary closures, and special event schedules.
```sql
CREATE TABLE operational_status (
    id SERIAL PRIMARY KEY,
    entity_id INTEGER REFERENCES entities(id),
    is_open BOOLEAN NOT NULL DEFAULT TRUE,
    status_note TEXT,
    hours_schedule JSONB,
    source_citation TEXT NOT NULL,
    valid_from TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    valid_until TIMESTAMP
);
```

---

## 3. Vector Similarity Function
The vector store leverages dense unit-normalized semantic embeddings matching pgvector semantics:
$$\text{Cosine Similarity}(u, v) = \frac{u \cdot v}{\|u\|_2 \|v\|_2} = \sum_{i=1}^{384} u_i \cdot v_i$$
When vector indexes are queried, candidates are scoped by `city_id` and gated against cross-destination contamination.
