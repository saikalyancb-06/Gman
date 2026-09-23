# GeoGuide - Location-Aware AI Place Companion
**KogniVera Hackathon 2026**  
*Team Ctrl+Alt+Defeat*

---

## 🌟 Overview
GeoGuide helps travellers make the most of where they are right now. It transitions the traveller from *"I have arrived here"* to *"I understand this place and know what I should do next."*

Instead of forcing users to switch between Google Maps, weather apps, Wikipedia articles, and tourism blogs, GeoGuide delivers a **grounded, context-aware, personalized place briefing, nearby discovery, constraint-optimized day plans, and multilingual voice Q&A**.

---

## 📱 Implemented Core App Screens (Pixel-accurate to Spec PDF)

1. **Screen 4.1: Now (Home Screen)**
   - Live location accuracy, audio read-aloud toggle, weather metrics (Temp, Feels like, Humidity, Sunrise/Sunset, Daylight left).
   - Season guidance (monsoon alerts, river status, best walking windows).
   - Grounded Place Briefing (*"What is special here"*) with verified source badges.
   - Real-time advisories (*"What matters today"*): river coracle suspensions, high UV warning, ticket cutoff countdown, festival notices.
   - *"Do not miss"* highlights carousel.

2. **Screen 4.2: Nearby Screen**
   - Search with instant filtering by categories: *All, Monuments, Hidden gems, Step-free, Nature & Sunsets*.
   - Ranked POI cards with live tags (*Top pick, Open now, Step-free, Steep*), travel time, distance, and shared ticket notes.
   - *"Eat local"* Karnataka delicacies (Jolada rotti with ennegayi, Thatte idli).
   - *"Stay nearby"* boutique resorts & guesthouses with flood/transport advisories.

3. **Screen 4.3: Plan Screen (Constraint-Based Optimizer)**
   - 2-hour, 4-hour, and Full-day trip schedule duration toggles.
   - Dynamic Re-planning filters: *Balanced, Cheaper, Greener, Less walking*.
   - Live KPI metrics: Total duration, estimated cost (₹), walking distance (km), and carbon emissions (kg CO₂e).
   - Live demo reactive signal: Automatically adapts itinerary when entry windows close or river crossings are unavailable.
   - Schedule timeline with step-free badges, transport modes, and *"Left out on purpose"* transparency.

4. **Screen 4.4: Ask GeoGuide (Grounded Multilingual Q&A + Speech & TTS)**
   - Voice STT input via Web Speech API and text queries.
   - Grounded RAG with strict citations referencing official ASI schedules, Karnataka Tourism guidelines, and flood bulletins.
   - Multilingual support for **English**, **Kannada (ಕನ್ನಡ)**, and **Hindi (हिन्दी)** with native audio read-aloud.

5. **Screen 4.5: Profile Screen**
   - User trip statistics (Sites seen, Saved places, Budget spent so far).
   - Interactive interest tag preferences (*History, Architecture, Photography, Landscape, Food, Living ritual*).
   - Budget tiers, walking pace, and accessibility toggles (*♿ Step-free only, 🚶 Under 2 km walking, ☀️ Avoid midday sun*).

---

## 🏗️ Architecture & Tech Stack

- **Backend**: FastAPI (Python), SQLite PS-13 Database (19 Relational Tables).
- **RAG & Knowledge Engine**: Grounded semantic retrieval over `place_kb` and `poi_facts_kb` with provenance tracking.
- **Optimization Layer**: Multi-objective constraint solver balancing time, cost, walking distance, and carbon emissions.
- **Frontend**: Modern React, Tailwind CSS, Lucide Icons, Web Speech API.
- **Data Model (19 Tables)**: `countries`, `cities`, `users`, `user_devices`, `user_preferences`, `categories`, `activities_poi`, `hotels`, `weather_daily`, `events_festivals`, `safety_advisories`, `place_kb`, `poi_facts_kb`, `trips`, `itineraries`, `itinerary_items`, `optimizer_weights`, `languages`, `currencies`.

---

## 🚀 Quick Start & How to Run

### Run the App:
```bash
python run.py
```
This automatically starts the FastAPI server at `http://127.0.0.1:8000` and launches GeoGuide in your default browser.

### Run Verification Test Suite:
```bash
python test_geoguide.py
```
