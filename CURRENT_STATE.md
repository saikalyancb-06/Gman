# CURRENT_STATE.md - GeoGuide Architecture & System Audit
*Audit Date: 2026-09-23 | Team Ctrl+Alt+Defeat | KogniVera Hackathon 2026*

---

## 1. Executive Summary
GeoGuide is a location-aware, context-intelligent AI travel companion designed around the philosophy:
**"Know where you are. Know what matters. Know what to do next."**

This audit reviews the current implementation against the strict specifications in `Ctrl_Alt_Defeat_GeoGuide_Design(1).pdf`.

---

## 2. Component-by-Component Assessment

| Subsystem | Current State | Strengths | Technical Debt / Needs Upgrade |
|---|---|---|---|
| **Database (PS-13)** | Operational (19 Tables + 2 Extension Tables) | Fully seeded with Hampi & Bengaluru, clean foreign keys, correct schemas for POIs, KB, Itineraries | Needs rich vector embedding store, explicit SQL query parameterization safeguards, performance indexes |
| **Context Intelligence Engine** | Operational | Calculates live GPS distance, daylight remaining, sunrise/sunset, live weather integration | Needs a centralized canonical `GeoContext` schema shared across all endpoints, proactive "Live Copilot" and "Don't Miss" engine |
| **Recommendation Engine** | Basic Heuristic Ranking | Multi-objective sorting by budget, carbon, walking | Needs formal explainable multi-factor scoring formula with configurable weights, returning raw & normalized feature contributions and Precision@5 evaluation |
| **Itinerary Optimizer** | Operational Heuristic Solver | Generates 2h, 4h, full-day plans with live metrics (cost, walk, CO₂e) | Needs robust mathematical constraint solver (OR-Tools / MILP / Branch & Bound), live adaptive plan re-evaluator (PlanMonitor), and animated plan diffing |
| **RAG & Knowledge Retrieval** | Keyword-based with template fallback | Provenance citations to ASI and Tourism records | Upgrade to true Vector/Semantic RAG + Grounding Firewall with strict claim-level verification and zero unverified hallucination |
| **Voice & Speech** | Web Speech API | Working browser STT and TTS read-aloud | Needs conversational state persistence (context memory across multiple dialogue turns) |
| **Vision AI / Scan Place** | Missing | Spec calls for "Scan This Place" | Implement Camera recognition pipeline with visual identification → candidate POI matching → grounded RAG explanation |
| **Offline-First & Caching** | Memory Cache | PWA service worker capable | Implement full local persistence (IndexedDB / LocalStorage cache) with offline banner and Last-Updated timestamps |
| **Mobile Application** | Web / PWA setup | Mobile-responsive touch UI | Integrate Capacitor Android project with Native GPS, Camera, Mic, and build workflow |
| **Testing & Evaluation** | Ad-hoc test script | `test_live.py` passes | Build formal evaluation suite (`recommendation_report.md`, `rag_report.md`, `itinerary_report.md`, pytest suite) |

---

## 3. Systematic Upgrade Roadmap

1. **Backend & Data Layer**:
   - Centralize canonical `GeoContext` engine.
   - Upgrade RAG service with TF-IDF / cosine-similarity semantic vector index over `place_kb` and `poi_facts_kb` with a strict Grounding Firewall.
   - Implement explainable Recommendation Engine 2.0 with auditable feature weights.
   - Implement Itinerary Optimizer 2.0 with mathematical constraint solver, PlanMonitor, and reactive re-planning.
   - Implement Vision AI endpoint (`/api/vision/identify`) linking visual landmarks to grounded RAG.
   - Implement Persistent Conversational Context in `/api/ask` for stateful multi-turn replanning.
   - Implement Live Copilot (`/api/copilot/next-action`) and Don't-Miss opportunity detector.

2. **Frontend & Mobile UI**:
   - Modernize Now, Plan, Nearby, Ask, and Profile with Plan Diff animations, Evidence Drawer, and Camera Scanner.
   - Add offline state indicators and IndexedDB caching.
   - Setup Capacitor configuration and native wrappers.

3. **Evaluation & Verification**:
   - Automated Pytest suite covering all RAG, ranking, and optimizer constraints.
   - Rigorous evaluation reports measuring Precision@5, groundedness, and constraint satisfaction.
