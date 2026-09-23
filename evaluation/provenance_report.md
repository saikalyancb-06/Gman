# Verified Provenance & Grounding Firewall Report
*System: GeoGuide Source Attribution & Provenance Validation Engine*  
*Date: 2026-09-23 | Team Ctrl+Alt+Defeat | KogniVera Hackathon 2026*

---

## 1. Provenance Integrity Policy

GeoGuide strictly enforces real source attribution. **Decorative or fake source badges are completely prohibited**.

Every answer generated and presented to the user contains verifiable metadata:
- **`source`**: Actual source monograph, official circular, meteorological API, or encyclopedia entry.
- **`source_tag`**: High-level provenance category (e.g., `Verified Grounded Evidence • place_kb`, `Live Weather API`, `Verified External Source • institutional_encyclopedia`).
- **`verified`**: Boolean flag indicating verified evidence backing.
- **`support_status`**: `SUPPORTED`, `PARTIALLY_SUPPORTED`, or `UNSUPPORTED`.
- **`evidence_snippets`**: Array of actual evidence chunks used during synthesis.

---

## 2. Provenance Mapping

| Domain / Query Type | Backend Retrieval Path | UI Provenance Attribution |
|---|---|---|
| **ASI Monuments (Hampi)** | `activities_poi` & `place_kb` | `ASI Monograph & Official Tourism Registry` |
| **Micro-Facts (Pillars, Optics)** | `poi_facts_kb` | `ASI Research` / `Virupaksha Temple Records` |
| **River & Safety Advisories** | `safety_advisories` | `Karnataka River Police & Tungabhadra Board Advisory` |
| **Live Weather** | Open-Meteo REST API | `Open-Meteo Live Meteorological API` |
| **External Non-Local Entities** | `WebRetriever` | `Wikipedia Institutional Knowledge` |
| **Unverified / Missing Evidence** | `RelevanceGate` Abstention | `None (Verification Gate Abstention)` |
