# Destination Knowledge Pack Specification & GeoContext Preloading

## 1. Overview & Objective

The **Destination Knowledge Pack** (internally known as **GeoContext Preloading**) creates a compact, self-contained, location-scoped knowledge bundle for any active destination. Instead of executing cold multi-table joins or distant database queries for every user interaction, GeoGuide preloads structured POIs, verified semantic facts, safety advisories, and live weather conditions into an in-memory cached environment with section-level TTLs.

The existence of an item inside a Knowledge Pack does **NOT** grant permission to use it for unrelated questions. Retrieval strictly enforces:
```
ENTITY + INTENT + ATTRIBUTE + TEMPORAL REQUIREMENT
```

---

## 2. GeoContext Schema & Precedence

When a user interacts with GeoGuide, their active geographic context is resolved by `GeoContextResolver` according to a strict 4-tier precedence model:

```json
{
  "destination_id": 2,
  "destination_name": "Bengaluru",
  "city_id": 2,
  "city_name": "Bengaluru",
  "state": "Karnataka",
  "latitude": 12.9716,
  "longitude": 77.5946,
  "radius_meters": 25000,
  "detected_from": "explicit_poi_query",
  "confidence": 0.99,
  "resolved_poi": {
    "id": 12,
    "city_id": 2,
    "name": "Lalbagh Botanical Garden & Glass House"
  },
  "resolved_at": "2026-09-23T02:30:00Z"
}
```

### Precedence Hierarchy:
1. **`explicit_poi_query`** (Confidence: 0.99): If the query mentions a specific landmark/POI (e.g. *"Is Lalbagh open now?"*), the POI's parent city overrides the ambient session destination.
2. **`explicit_query`** (Confidence: 0.99): If the query mentions a city explicitly (e.g. *"What is the population of Bangalore?"*).
3. **`user_selection`** (Confidence: 0.95): The user explicitly switches destination tabs in the UI.
4. **`gps`** (Confidence: 0.92): Device GPS coordinates matching a destination within geographic radius.
5. **`fallback_default`** (Confidence: 0.70): Default fallback destination (Hampi).

---

## 3. Knowledge Pack Item Metadata & Semantic Attributes

Every item preloaded into a Knowledge Pack is decorated with comprehensive semantic metadata:

```json
{
  "pack_id": "geopack_2_34aef819bc",
  "entity_id": 12,
  "entity_name": "Lalbagh Botanical Garden & Glass House",
  "entity_type": "POI",
  "destination_id": 2,
  "city_id": 2,
  "content_type": "poi_detail",
  "intent_tags": ["OPENING_HOURS", "ENTRY_FEE", "ACCESSIBILITY", "POI_DETAIL"],
  "attribute_tags": ["opening_hours", "operational_status", "entry_fee", "ticket_policy", "step_free"],
  "source_type": "official_tourism_registry",
  "freshness_class": "SLOW",
  "retrieved_at": "2026-09-23T02:30:00Z",
  "expires_at": "2026-09-26T02:30:00Z"
}
```

### Semantic Attribute Classes:
- **`CITY`**: `population`, `history`, `geography`, `climate`, `city_overview`.
- **`POI`**: `opening_hours`, `operational_status`, `entry_fee`, `ticket_policy`, `architecture`, `step_free`, `etiquette`.
- **`WEATHER`**: `temperature`, `humidity`, `forecast`, `current_conditions`.
- **`SAFETY`**: `closure`, `warning`, `hazard`, `advisory`, `coracle_safety`, `open_status`.

---

## 4. Freshness TTL Configurations

| Section | TTL Duration | Policy Category | Description & Contents |
| :--- | :--- | :--- | :--- |
| **Monuments & History** | 30 Days (2,592,000s) | `STATIC` | Historical narratives, architecture styles, dynasties, site geography. |
| **POIs & Accessibility** | 3 Days (259,200s) | `SLOW` | Ticket pricing schedules, operating hours, wheelchair accessibility. |
| **Safety Advisories** | 4 Hours (14,400s) | `DYNAMIC` | River alerts, coracle safety, heat wave warnings, festival crowd alerts. |
| **Live Weather & Daylight**| 10 Minutes (600s) | `LIVE` | Current temperature, humidity, UV index, sunrise/sunset. |

---

## 5. Attribute-Aware & Scoped Retrieval Engine

```
QUERY
  ↓
QUERY UNDERSTANDING (QueryContext: Entity, Entity Type, Destination, Intent, Attribute, Temporal)
  ↓
DESTINATION & ENTITY CANDIDATE SCOPING (Filter to candidate pool belonging to requested destination)
  ↓
VECTOR SIMILARITY SEARCH
  ↓
ENTITY CONSISTENCY VALIDATION (Hard reject mismatched entities: e.g. Tungabhadra for Lalbagh)
  ↓
ATTRIBUTE CONSISTENCY VALIDATION (Hard reject generic overview for population queries)
  ↓
ANSWERABILITY GATE
  ↓ (If empty) → Targeted External Web / API Fallback
  ↓
GROUNDED ANSWER GENERATION WITH FULL TRACE
```

---

## 6. Developer Debug Trace Specification

Every Ask response provides complete internal trace visibility:

```json
{
  "query": "What is the population of Bangalore?",
  "resolved_entity": "Bengaluru",
  "resolved_entity_id": null,
  "destination": "Bengaluru",
  "destination_id": 2,
  "intent": "FACT_LOOKUP",
  "attribute": "POPULATION",
  "temporal_requirement": "NONE",
  "freshness_requirement": "STATIC",
  "pack_id": "geopack_2_34aef819bc",
  "candidates_evaluated": 25,
  "rejected_candidates": [
    {
      "doc_title": "Overview of Bengaluru",
      "score": 0.42,
      "reason": "ATTRIBUTE_MISMATCH_NO_POPULATION_DATA"
    }
  ],
  "selected_evidence": ["Bengaluru"],
  "answer": "As per the 2011 census, Bengaluru city had an official population of 8.4 million. The broader metropolitan area had a population of around 8.5 million...",
  "source": "Wikipedia Institutional Knowledge (Bengaluru)",
  "source_tag": "Verified External Source • Census",
  "retrieval_mode": "WEB_RETRIEVAL",
  "verified": true,
  "grounding_status": "SUPPORTED",
  "answerable": true,
  "evidence_count": 1
}
```
