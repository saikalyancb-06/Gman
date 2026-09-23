# DATA SOURCE POLICY & GOVERNANCE
**GeoGuide Knowledge Provenance & Verification Standards**

---

## 1. Approved External Data Providers

| Source Class | Provider / API | Permitted Domain | Freshness / TTL | Verification Standard |
| :--- | :--- | :--- | :--- | :--- |
| **Institutional Heritage & History** | Wikipedia API | Monument history, UNESCO heritage details, dynastic architecture | STATIC (30 Days) | Official academic/encyclopedic citation required |
| **Local Businesses & Eateries** | OpenStreetMap (Nominatim / Overpass) | Local restaurants, darshinis, bakeries, cafes, lodging | SLOW (3 Days) | Valid OSM Node/Way ID + latitude/longitude coordinates |
| **Demographics & Population** | Census Records / Wikipedia Demographics | City population figures, urban agglomeration statistics | STATIC (30 Days) | Must contain explicit census reference year and figure |
| **Atmospheric & Weather** | Open-Meteo Meteorological API | Real-time temperature, precipitation, humidity, forecast | LIVE (10 Minutes) | Live GPS query with fallbacks to station observations |
| **Monuments & Ticketing** | ASI (Archaeological Survey of India) | Ticket policy, entry fees, photography guidelines | SLOW (3 Days) | State/National official tariff schedule |
| **Civic Advisories & Safety** | State & City Police / Horticulture Dept | Park closures, water levels, traffic detours | DYNAMIC (4 Hours) | Published departmental advisory notice |

---

## 2. Ingestion & Provenance Criteria
Every external fact ingested into GeoGuide PostgreSQL must satisfy the following provenance invariants:
1. **Source Citation**: Must record the publishing authority (e.g. `Wikipedia Institutional Knowledge`, `OpenStreetMap Local Places Registry`, `Open-Meteo`).
2. **Source URL / URI**: Must store the canonical HTTP link to the verified online resource.
3. **Cryptographic Deduplication**: Every chunk text is hashed with SHA-256 (`content_hash`). Duplicate chunks are rejected at insert.
4. **Geographic Scoping**: Every fact is stamped with a foreign key to `cities(id)`. Cross-city leakage is blocked by database constraints and the Relevance Gate.

---

## 3. Disallowed Practices (Strict Rejections)
- **Zero Static Mock Dictionaries**: No hardcoded query-answer mappings are allowed in source code.
- **No Ungrounded Fallbacks**: If external retrieval fails to find verifiable facts, the system MUST emit `answerable: false` and abstain cleanly.
- **Zero Hallucination Tolerance**: LLM synthesis is strictly bounded by retrieved external evidence snippets. Prompt instructions explicitly prohibit introducing unverified external knowledge.
