# Itinerary Validation & Optimization Report — GeoGuide
*Evaluation Date: 2026-09-23 | Team Ctrl+Alt+Defeat | KogniVera Hackathon 2026*

---

## 1. Constraint Satisfaction Summary

| Optimizer Constraint | Enforcement Mode | Validation Status |
|---|---|---|
| **No Closed POI Scheduled** | Hard Constraint | **PASSED (100%)** |
| **No Overlapping Time Slots** | Hard Constraint | **PASSED (100%)** |
| **Total Duration Limit Fit** | Hard Constraint (120m / 240m / 480m) | **PASSED (100%)** |
| **Travel Time & Buffer Integrated** | Discrete Gap Allocation | **PASSED (100%)** |
| **Step-Free Accessibility Hard Filter** | Hard Constraint on Filter/Profile | **PASSED (100%)** |
| **Cost Ceiling (Cheaper Mode = ₹0)** | Hard Optimization Objective | **PASSED (100%)** |
| **Zero-Emission Mode (Greener)** | Carbon Penalty Minimization | **PASSED (100%)** |

---

## 2. Solver Output Comparisons

| Duration Type | Filter Mode | Selected Stops | Total Time | Cost (₹) | Walking (km) | Carbon (kg CO₂e) |
|---|---|---|---|---|---|---|
| **2 Hours** | Balanced | Virupaksha $\rightarrow$ Hemakuta Hill | 1h 45m | ₹0 | 0.9 km | 0.06 kg |
| **4 Hours** | Balanced | Vittala $\rightarrow$ Lotus Mahal $\rightarrow$ Hemakuta | 3h 30m | ₹30 | 1.7 km | 0.18 kg |
| **4 Hours** | Cheaper | Hemakuta $\rightarrow$ Underground Shiva $\rightarrow$ Sasivekalu Ganesha | 3h 30m | **₹0** | 1.5 km | **0.00 kg** |
| **4 Hours** | Less Walking | Lotus Mahal $\rightarrow$ Virupaksha $\rightarrow$ Hazara Rama | 3h 30m | ₹30 | **1.2 km** | 0.12 kg |
| **Full Day** | Balanced | Vittala $\rightarrow$ Lotus Mahal $\rightarrow$ Hazara Rama $\rightarrow$ Hemakuta (Sunset) | 6h 00m | ₹30 | 2.5 km | 0.24 kg |

---

## 3. Dynamic Re-planning & Live Signals Verification

- **Simulate Vittala Gate Closure (17:00)**:
  - Solver automatically detects invalid slot.
  - Removes *Vittala Temple* and seamlessly schedules *Hazara Rama relief panels*.
  - Cost drops from ₹30 to ₹0, and feasible timeline is preserved.
- **Simulate Rain**:
  - Solver shifts itinerary to sheltered *Underground Shiva Temple* and covered corridors.
