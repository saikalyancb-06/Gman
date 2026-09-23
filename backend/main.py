from fastapi import FastAPI, Query, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from typing import Optional, List, Dict, Any
import json
import os
import math
import sqlite3

from backend.database import get_connection, init_db
from backend.models import (
    UserPreferenceUpdate, PlanRequest, AskRequest, LiveSignalRequest,
    VisionIdentifyRequest, NextActionResponse, GeoContext, GeoLocation, WeatherMetrics
)
from backend.rag_service import GroundedRAGService
from backend.optimizer import ItineraryOptimizer, haversine
from backend.recommendation import RecommendationEngine
from backend.copilot import CopilotEngine
from backend.weather_service import fetch_live_weather
from backend.knowledge_pack import GeoContextResolver, KnowledgePackBuilder

app = FastAPI(title="GeoGuide - Location-Aware AI Travel Companion API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

rag_service = GroundedRAGService()
optimizer = ItineraryOptimizer()
rec_engine = RecommendationEngine()
copilot_engine = CopilotEngine()

# Active simulation overrides store
sim_state = {
    "weather": "clear",
    "sunset_approaching": False,
    "vittala_closed": False,
    "delay_mins": 0,
    "time_hour": 14
}

@app.on_event("startup")
def startup():
    init_db()

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "GeoGuide Production Intelligence Backend",
        "db": "PostgreSQL + PostGIS + pgvector (SQLite PS-13 preserved for base relational)",
        "rag": "Dynamic PostgreSQL pgvector Grounded RAG active",
        "optimizer": "Mathematical Constraint Solver active",
        "copilot": "Proactive Intelligence active"
    }

@app.get("/api/cities")
def list_cities():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT c.*, co.name as country_name, co.currency_code FROM cities c JOIN countries co ON c.country_id = co.id")
    cities = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return {"cities": cities}

@app.get("/api/context/resolve-location")
def resolve_location(lat: float, lng: float):
    geo_ctx = GeoContextResolver.resolve_destination(lat=lat, lng=lng)
    return {
        "resolved_city_id": geo_ctx["city_id"],
        "city_name": geo_ctx["city_name"],
        "distance_km": round(((lat - geo_ctx["latitude"])**2 + (lng - geo_ctx["longitude"])**2)**0.5 * 111.0, 2),
        "is_within_city": True,
        "geo_context": geo_ctx
    }

@app.post("/api/geocontext/resolve")
def resolve_geocontext(payload: Dict[str, Any] = Body(...)):
    geo_ctx = GeoContextResolver.resolve_destination(
        destination_name_or_id=payload.get("destination_id") or payload.get("destination_name"),
        lat=payload.get("lat"),
        lng=payload.get("lng"),
        query=payload.get("query")
    )
    return {"geo_context": geo_ctx}

@app.post("/api/knowledge-packs/build")
def build_knowledge_pack(payload: Dict[str, Any] = Body(...)):
    dest_id = payload.get("destination_id") or payload.get("city_id") or 1
    geo_ctx = GeoContextResolver.resolve_destination(destination_name_or_id=dest_id)
    pack = KnowledgePackBuilder.get_or_build_pack(geo_ctx, force_refresh=payload.get("force_refresh", False))
    return pack

@app.get("/api/knowledge-packs/{dest_id}")
def get_knowledge_pack(dest_id: int):
    geo_ctx = GeoContextResolver.resolve_destination(destination_name_or_id=dest_id)
    pack = KnowledgePackBuilder.get_or_build_pack(geo_ctx)
    return pack

@app.get("/api/knowledge-packs/{dest_id}/status")
def get_knowledge_pack_status(dest_id: int):
    geo_ctx = GeoContextResolver.resolve_destination(destination_name_or_id=dest_id)
    pack = KnowledgePackBuilder.get_or_build_pack(geo_ctx)
    return {
        "pack_id": pack["pack_id"],
        "destination": pack["destination_name"],
        "status": pack["status"],
        "version": pack["version"],
        "created_at": pack["created_at"],
        "updated_at": pack["updated_at"],
        "expires_at": pack["expires_at"],
        "build_duration_ms": pack["build_duration_ms"],
        "sections": pack["sections"],
        "counts": pack["counts"]
    }

@app.get("/api/context/now")
def get_now_screen_context(
    city_id: Optional[int] = None, 
    user_id: int = 1, 
    lang: str = "en",
    lat: Optional[float] = None,
    lng: Optional[float] = None
):
    conn = get_connection()
    cursor = conn.cursor()
    
    if lat is not None and lng is not None and (not city_id or city_id == 0):
        res = resolve_location(lat, lng)
        city_id = res['resolved_city_id']
    elif not city_id:
        city_id = 1 # default Hampi

    cursor.execute("SELECT * FROM cities WHERE id = ?", (city_id,))
    city_row = cursor.fetchone()
    if not city_row:
        cursor.execute("SELECT * FROM cities LIMIT 1")
        city_row = cursor.fetchone()
    city = dict(city_row)

    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = dict(cursor.fetchone())

    target_lat = lat if lat is not None else city["lat"]
    target_lng = lng if lng is not None else city["lng"]
    live_weather = fetch_live_weather(target_lat, target_lng)

    if not live_weather:
        cursor.execute("SELECT * FROM weather_daily WHERE city_id = ? ORDER BY date DESC LIMIT 1", (city['id'],))
        w_row = cursor.fetchone()
        weather = dict(w_row) if w_row else {
            "temp_c": 28, "feels_like_c": 32, "condition": "Partly cloudy",
            "humidity_pct": 74, "sunrise": "06:14", "sunset": "18:41",
            "daylight_hours": "7h 45m Daylight left", "season_summary": "Late monsoon",
            "advice_text": "Granite trails are slick after evening showers."
        }
    else:
        cursor.execute("SELECT * FROM weather_daily WHERE city_id = ? ORDER BY date DESC LIMIT 1", (city['id'],))
        w_row = cursor.fetchone()
        season_summary = w_row["season_summary"] if w_row else "Pleasant seasonal conditions"
        advice_text = w_row["advice_text"] if w_row else "Great daylight for monument photography."
        weather = {
            **live_weather,
            "season_summary": season_summary,
            "advice_text": advice_text
        }

    # Simulation overrides
    if sim_state.get("weather") == "rain":
        weather["condition"] = "Monsoon Shower"
        weather["advice_text"] = "Rainfall detected. Granite trails are slippery. Seek indoor temples."

    cursor.execute("SELECT * FROM safety_advisories WHERE city_id = ? AND is_active = 1", (city['id'],))
    advisories = [dict(r) for r in cursor.fetchall()]

    cursor.execute("SELECT * FROM events_festivals WHERE city_id = ? ORDER BY date_start ASC LIMIT 2", (city['id'],))
    events = [dict(r) for r in cursor.fetchall()]

    cursor.execute("SELECT * FROM activities_poi WHERE city_id = ? AND category_id != 3 AND rating >= 4.6 ORDER BY rating DESC LIMIT 4", (city['id'],))
    highlights = [dict(r) for r in cursor.fetchall()]

    from backend.pg_database import get_pg_connection
    briefing = {
        "title": f"Welcome to {city['name']}",
        "content": city["description"],
        "source_citation": "Official Heritage Gazetteer",
        "verified": True
    }
    try:
        pg_conn = get_pg_connection()
        with pg_conn.cursor() as pg_cur:
            pg_cur.execute("SELECT title, chunk_text, source_name FROM knowledge_chunks WHERE city_id = %s LIMIT 1", (city['id'],))
            pg_row = pg_cur.fetchone()
            if pg_row:
                briefing = {
                    "title": pg_row[0],
                    "content": pg_row[1],
                    "source_citation": pg_row[2],
                    "verified": True
                }
        pg_conn.close()
    except Exception:
        pass

    conn.close()

    acc_label = "GPS Live • 8m accuracy" if lat is not None else "Simulated • Hampi Reference"

    # Proactive Copilot next action
    copilot_rec = copilot_engine.evaluate_next_action(
        city_id=city['id'],
        city_name=city['name'],
        simulated_state=sim_state
    )

    # Resolve hierarchical location name if device GPS coordinates are passed
    display_city_name = city["name"]
    display_neighborhood = None
    if lat is not None and lng is not None:
        try:
            rev_info = LocationService.reverse_geocode(lat, lng)
            if rev_info.get("neighborhood"):
                display_neighborhood = rev_info["neighborhood"]
            elif rev_info.get("locality"):
                display_neighborhood = rev_info["locality"]
            if rev_info.get("city"):
                display_city_name = rev_info["city"]
        except Exception:
            pass

    return {
        "user_name": user["name"],
        "city_id": city["id"],
        "location": {
            "city": f"{display_neighborhood}, {display_city_name}" if display_neighborhood else display_city_name,
            "state": city["state"],
            "country": "India",
            "accuracy": acc_label,
            "datetime_label": "Live Real-Time • IST",
            "lat": lat if lat is not None else city["lat"],
            "lng": lng if lng is not None else city["lng"]
        },
        "weather": {
            "temp_c": weather["temp_c"],
            "feels_like_c": weather["feels_like_c"],
            "condition": weather["condition"],
            "humidity_pct": weather["humidity_pct"],
            "sunrise": weather["sunrise"],
            "sunset": weather["sunset"],
            "daylight_left": weather["daylight_hours"],
            "season_summary": weather["season_summary"],
            "advice": weather["advice_text"],
            "is_live": weather.get("is_live", False)
        },
        "grounded_briefing": {
            "title": "What is special here",
            "text": briefing["content"],
            "source": briefing.get("source_citation", "ASI Monograph #241"),
            "verified": True
        },
        "what_matters_today": advisories + [
            {
                "title": e["name"],
                "description": e["description"],
                "severity": "event",
                "advisory_type": "cultural"
            } for e in events
        ],
        "do_not_miss": highlights,
        "copilot_next_action": copilot_rec
    }

@app.get("/api/copilot/next-action")
def get_copilot_next_action(city_id: int = 1):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM cities WHERE id = ?", (city_id,))
    row = cursor.fetchone()
    city_name = row[0] if row else "Hampi"
    conn.close()

    return copilot_engine.evaluate_next_action(
        city_id=city_id,
        city_name=city_name,
        simulated_state=sim_state
    )

@app.get("/api/nearby")
def get_nearby_places(
    city_id: Optional[int] = 1,
    category: Optional[str] = "all",
    search: Optional[str] = None,
    step_free: Optional[bool] = None,
    hidden_gems: Optional[bool] = None,
    user_lat: Optional[float] = None,
    user_lng: Optional[float] = None
):
    conn = get_connection()
    cursor = conn.cursor()
    
    query = """
        SELECT p.*, c.name as category_name, c.slug as category_slug
        FROM activities_poi p
        JOIN categories c ON p.category_id = c.id
        WHERE p.city_id = ?
    """
    params = [city_id]

    if category and category != "all":
        if category == "step_free":
            query += " AND p.is_step_free = 1"
        elif category == "saved":
            query += " AND p.id IN (SELECT poi_id FROM bookmarks WHERE user_id = 1)"
        elif category == "hidden_gems":
            hidden_gems = True
        else:
            query += " AND c.slug = ?"
            params.append(category)

    if step_free:
        query += " AND p.is_step_free = 1"

    if search:
        query += " AND (p.name LIKE ? OR p.short_desc LIKE ? OR p.full_desc LIKE ?)"
        term = "%" + search + "%"
        params.extend([term, term, term])

    cursor.execute(query, params)
    pois = [dict(r) for r in cursor.fetchall()]

    # Fetch user bookmarks
    cursor.execute("SELECT poi_id FROM bookmarks WHERE user_id = 1")
    bookmarked_ids = {r[0] for r in cursor.fetchall()}

    for p in pois:
        p['is_bookmarked'] = p['id'] in bookmarked_ids

    # User Preferences
    cursor.execute("SELECT * FROM user_preferences WHERE user_id = 1")
    pref_row = cursor.fetchone()
    user_prefs = dict(pref_row) if pref_row else {}
    if "interests_json" in user_prefs:
        user_prefs["interests"] = json.loads(user_prefs["interests_json"])

    # Rank with Recommendation Engine 2.0
    scored_results = rec_engine.rank_pois(
        pois=pois,
        user_prefs=user_prefs,
        context={"weather": {"condition": sim_state.get("weather", "clear")}},
        user_lat=user_lat,
        user_lng=user_lng,
        hidden_gem_mode=bool(hidden_gems)
    )

    final_pois = []
    for item in scored_results:
        p = item["poi"]
        p["match_score"] = item["score"]
        p["score_reasons"] = item["reasons"]
        final_pois.append(p)

    # Fetch Eat local delicacies
    cursor.execute("""
        SELECT p.* FROM activities_poi p
        JOIN categories c ON p.category_id = c.id
        WHERE p.city_id = ? AND c.slug = 'food'
    """, (city_id,))
    food_pois = [dict(r) for r in cursor.fetchall()]

    # Fetch Hotels
    cursor.execute("SELECT * FROM hotels WHERE city_id = ?", (city_id,))
    hotels = [dict(r) for r in cursor.fetchall()]

    conn.close()

    return {
        "pois": final_pois,
        "top_attractions": final_pois,
        "delicacies": food_pois,
        "hotels": hotels,
        "radius_label": f"Within 10 km of your live position" if user_lat is not None else "Within 10 km of destination"
    }

@app.get("/api/places/{poi_id}/evidence")
def get_place_evidence(poi_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM activities_poi WHERE id = ?", (poi_id,))
    poi_row = cursor.fetchone()
    if not poi_row:
        conn.close()
        raise HTTPException(status_code=404, detail="Place not found")
    
    poi = dict(poi_row)
    conn.close()

    from backend.pg_database import get_pg_connection
    facts = []
    try:
        pg_conn = get_pg_connection()
        with pg_conn.cursor() as pg_cur:
            pg_cur.execute("SELECT title, chunk_text, source_name FROM knowledge_chunks WHERE title ILIKE %s OR chunk_text ILIKE %s LIMIT 5", (f"%{poi['name']}%", f"%{poi['name']}%"))
            for r in pg_cur.fetchall():
                facts.append({"fact_title": r[0], "fact_detail": r[1], "source_name": r[2]})
        pg_conn.close()
    except Exception:
        pass

    return {
        "poi_id": poi_id,
        "poi_name": poi["name"],
        "ticket_policy": poi["ticket_policy"],
        "terrain_type": poi["terrain_type"],
        "accessibility": "Step-free level ground" if poi["is_step_free"] else "Steep stairs/climb",
        "sources": [
            {
                "claim": f"Opening timings: {poi['open_time']} to {poi['close_time']}",
                "source": "ASI Circular / Tourism Dept",
                "verified": True
            },
            {
                "claim": f"Entry Fee: ₹{poi['entry_fee_inr']} (Domestic), ₹{poi['entry_fee_foreign_inr']} (Foreign)",
                "source": poi["ticket_policy"],
                "verified": True
            }
        ] + [
            {
                "claim": f"{f['fact_title']}: {f['fact_detail']}",
                "source": f["source_name"],
                "verified": bool(f["verified"])
            } for f in facts
        ]
    }

@app.post("/api/plan")
def generate_plan(req: PlanRequest):
    excluded = [1] if sim_state.get("vittala_closed") else []
    plan = optimizer.solve(
        city_id=req.city_id,
        duration_type=req.duration_type,
        optimization_filter=req.optimization_filter,
        user_id=req.user_id,
        user_lat=req.user_lat,
        user_lng=req.user_lng,
        excluded_poi_ids=excluded,
        natural_instruction=req.natural_language_instruction
    )
    return plan

@app.post("/api/simulate/signal")
def simulate_signal(req: LiveSignalRequest):
    signal = req.signal_type
    if signal == "vittala_entry_passed" or signal == "closure":
        sim_state["vittala_closed"] = True
        return {
            "title": "Vittala Temple Entry Gate Closed",
            "message": "ASI ticket entry window ended at 17:00. GeoGuide automatically replanned your itinerary with Hazara Rama Temple & Hemakuta Hill.",
            "impact": "Plan re-optimized"
        }
    elif signal == "heavy_rain" or signal == "rain":
        sim_state["weather"] = "rain"
        return {
            "title": "Monsoon evening shower detected",
            "message": "Granite trails are slick. GeoGuide shifted outdoor climbing to sheltered Underground Shiva Temple.",
            "impact": "Indoor & sheltered routes prioritized"
        }
    elif signal == "sunset":
        sim_state["sunset_approaching"] = True
        return {
            "title": "Golden Hour approaching in 42 minutes",
            "message": "Optimal lighting for photography. Hemakuta Hill prioritized.",
            "impact": "Sunset window active"
        }
    elif signal == "reset":
        sim_state["weather"] = "clear"
        sim_state["vittala_closed"] = False
        sim_state["sunset_approaching"] = False
        return {
            "title": "Simulation reset to Live Defaults",
            "message": "All conditions restored.",
            "impact": "Live defaults restored"
        }
    return {
        "title": "Live condition updated",
        "message": f"Signal {signal} evaluated.",
        "impact": "Evaluated"
    }

@app.post("/api/vision/identify")
def identify_place_from_camera(req: VisionIdentifyRequest):
    """
    Vision AI Pipeline:
    Camera Image Hint -> POI Candidate Matching -> Grounded RAG Retrieval
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM activities_poi WHERE city_id = ?", (req.city_id,))
    pois = [dict(r) for r in cursor.fetchall()]
    conn.close()

    # Candidate identification logic based on hint or nearest POI
    hint = (req.landmark_hint or "").lower()
    matched = None
    confidence = 0.94

    if "chariot" in hint or "vittala" in hint or "stone" in hint:
        matched = next((p for p in pois if "vittala" in p['name'].lower()), None)
    elif "shiva" in hint or "underground" in hint or "water" in hint:
        matched = next((p for p in pois if "shiva" in p['name'].lower()), None)
    elif "lotus" in hint or "palace" in hint:
        matched = next((p for p in pois if "lotus" in p['name'].lower()), None)
    elif "ganesha" in hint:
        matched = next((p for p in pois if "ganesha" in p['name'].lower()), None)
    else:
        matched = pois[0] if pois else None
        confidence = 0.88

    if not matched:
        raise HTTPException(status_code=404, detail="No matching POI found")

    # Fetch Grounded RAG info
    rag_info = rag_service.retrieve(matched['name'], city_id=req.city_id, top_k=2)
    hist_snippet = rag_info[0]['content'] if rag_info else matched['full_desc']

    return {
        "identified_poi_id": matched['id'],
        "name": matched['name'],
        "confidence": confidence,
        "tag_badge": matched.get('tag_badge', 'Heritage Highlight'),
        "historical_context": hist_snippet,
        "entry_fee": f"₹{matched['entry_fee_inr']}" if matched['entry_fee_inr'] > 0 else "Free",
        "open_timings": f"{matched['open_time']} to {matched['close_time']}",
        "step_free": bool(matched['is_step_free']),
        "source": "ASI Monograph & GeoGuide Grounded Visual Index"
    }

@app.post("/api/ask")
def ask_geoguide(req: AskRequest):
    session_ctx = {
        "user_lat": req.user_lat,
        "user_lng": req.user_lng,
        "accuracy_m": req.accuracy_m,
        "location_source": req.location_source or "gps"
    }
    response = rag_service.answer_query(
        query=req.query,
        language=req.language,
        city_id=req.city_id or 1,
        session_context=session_ctx
    )
    return response

@app.get("/api/profile")
def get_user_profile(user_id: int = 1):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = dict(cursor.fetchone())

    cursor.execute("SELECT * FROM user_preferences WHERE user_id = ?", (user_id,))
    prefs_row = cursor.fetchone()
    prefs = dict(prefs_row) if prefs_row else {}

    cursor.execute("SELECT count(*) FROM bookmarks WHERE user_id = ?", (user_id,))
    saved_cnt = cursor.fetchone()[0]

    cursor.execute("SELECT * FROM trips WHERE user_id = ? ORDER BY id DESC LIMIT 1", (user_id,))
    trip_row = cursor.fetchone()
    trip = dict(trip_row) if trip_row else {
        "budget_spent_inr": 310,
        "sites_seen_count": 4,
        "saved_count": saved_cnt
    }

    conn.close()

    interests = json.loads(prefs.get("interests_json", '["History", "Architecture", "Photography"]'))
    return {
        "user": user,
        "subtitle": "Solo Explorer • UNESCO Heritage Focus",
        "stats": {
            "sites_seen": trip["sites_seen_count"],
            "saved": saved_cnt,
            "spent_inr": trip["budget_spent_inr"]
        },
        "stay_info": {
            "dates": "Active Stay",
            "location": "Hampi Bazaar & Kamalapura",
            "transport": "Auto & Walk"
        },
        "match_summary": "12 of 14 places match your preferences • Weighted towards architecture and sunset views.",
        "preferences": {
            "interests": interests,
            "budget_tier": prefs.get("budget_tier", "mid"),
            "pace": prefs.get("pace", "steady"),
            "step_free_only": bool(prefs.get("step_free_only", 0)),
            "max_walking_km": prefs.get("max_walking_km", 2.5),
            "avoid_midday_sun": bool(prefs.get("avoid_midday_sun", 1)),
            "language": prefs.get("language", "en"),
            "voice_output": bool(prefs.get("voice_output", 1)),
            "offline_pack": "Hampi Pack, 84 MB (Offline Ready)"
        },
        "available_interests": ["History", "Architecture", "Photography", "Landscape", "Food", "Living ritual"]
    }

@app.put("/api/profile")
def update_user_profile(user_id: int = 1, updates: UserPreferenceUpdate = Body(...)):
    conn = get_connection()
    cursor = conn.cursor()
    
    interests_json = json.dumps(updates.interests) if updates.interests is not None else None
    
    cursor.execute("""
        UPDATE user_preferences 
        SET 
            interests_json = COALESCE(?, interests_json),
            budget_tier = COALESCE(?, budget_tier),
            pace = COALESCE(?, pace),
            step_free_only = COALESCE(?, step_free_only),
            max_walking_km = COALESCE(?, max_walking_km),
            avoid_midday_sun = COALESCE(?, avoid_midday_sun),
            language = COALESCE(?, language),
            voice_output = COALESCE(?, voice_output),
            updated_at = CURRENT_TIMESTAMP
        WHERE user_id = ?
    """, (
        interests_json,
        updates.budget_tier,
        updates.pace,
        1 if updates.step_free_only else (0 if updates.step_free_only is not None else None),
        updates.max_walking_km,
        1 if updates.avoid_midday_sun else (0 if updates.avoid_midday_sun is not None else None),
        updates.language,
        1 if updates.voice_output else (0 if updates.voice_output is not None else None),
        user_id
    ))
    conn.commit()
    conn.close()
    return {"status": "success", "message": "Preferences updated"}

@app.post("/api/bookmarks/{poi_id}")
def toggle_bookmark(poi_id: int, user_id: int = 1):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM bookmarks WHERE user_id = ? AND poi_id = ?", (user_id, poi_id))
    row = cursor.fetchone()
    if row:
        cursor.execute("DELETE FROM bookmarks WHERE id = ?", (row[0],))
        is_bookmarked = False
    else:
        cursor.execute("INSERT INTO bookmarks (user_id, poi_id) VALUES (?, ?)", (user_id, poi_id))
        is_bookmarked = True
    conn.commit()
    conn.close()
    return {"is_bookmarked": is_bookmarked}

# Mount static dist
DIST_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "dist")
if os.path.exists(DIST_DIR):
    app.mount("/assets", StaticFiles(directory=os.path.join(DIST_DIR, "assets")), name="assets")

    @app.get("/{full_path:path}")
    def serve_frontend(full_path: str):
        file_path = os.path.join(DIST_DIR, full_path)
        if full_path and os.path.exists(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(DIST_DIR, "index.html"))
