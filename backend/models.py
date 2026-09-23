from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class GeoLocation(BaseModel):
    latitude: float
    longitude: float
    accuracy: str = "Live GPS • 8m accuracy"
    source: str = "gps" # "gps", "manual", "simulated"
    timestamp: Optional[str] = None
    city: str = "Hampi"
    state: str = "Karnataka"
    country: str = "India"

class WeatherMetrics(BaseModel):
    temp_c: int
    feels_like_c: int
    condition: str
    humidity_pct: int
    sunrise: str
    sunset: str
    daylight_hours: str
    uv_index: int = 7
    season_summary: str
    advice_text: str
    is_live: bool = False

class GeoContext(BaseModel):
    user_id: int = 1
    session_id: str = "default_session"
    location: GeoLocation
    destination_id: int = 1
    destination_name: str = "Hampi"
    local_time: str
    weather: WeatherMetrics
    events: List[Dict[str, Any]] = []
    advisories: List[Dict[str, Any]] = []
    user_preferences: Dict[str, Any] = {}
    network_status: str = "online"
    active_plan: Optional[Dict[str, Any]] = None

class UserPreferenceUpdate(BaseModel):
    interests: Optional[List[str]] = None
    budget_tier: Optional[str] = None
    pace: Optional[str] = None
    step_free_only: Optional[bool] = None
    max_walking_km: Optional[float] = None
    avoid_midday_sun: Optional[bool] = None
    language: Optional[str] = None
    voice_output: Optional[bool] = None

class PlanRequest(BaseModel):
    duration_type: str = "full_day" # "2_hours", "4_hours", "full_day", "custom"
    optimization_filter: str = "balanced" # "balanced", "cheaper", "greener", "less_walking", "more_history", "more_food"
    user_id: int = 1
    city_id: int = 1
    start_time: str = "13:00"
    user_lat: Optional[float] = None
    user_lng: Optional[float] = None
    natural_language_instruction: Optional[str] = None

class AskRequest(BaseModel):
    query: str
    language: str = "en"
    user_id: int = 1
    city_id: int = 1
    session_id: Optional[str] = "default"
    user_lat: Optional[float] = None
    user_lng: Optional[float] = None
    accuracy_m: Optional[float] = None
    location_source: Optional[str] = None

class LiveSignalRequest(BaseModel):
    signal_type: str
    itinerary_id: Optional[int] = None
    details: Optional[Dict[str, Any]] = None

class VisionIdentifyRequest(BaseModel):
    image_base64: Optional[str] = None
    landmark_hint: Optional[str] = None
    city_id: int = 1
    user_lat: Optional[float] = None
    user_lng: Optional[float] = None

class NextActionResponse(BaseModel):
    action: str
    poi_id: Optional[int] = None
    poi_name: str
    urgency: str # "HIGH", "MEDIUM", "LOW"
    reason: str
    why_it_fits: List[str]
    time_window: str
    recommended_action_type: str # "ADD_TO_PLAN", "VISIT_NOW", "TAKE_SHELTER"

class Opportunity(BaseModel):
    type: str # "CLOSING_SOON", "SUNSET_OPPORTUNITY", "WEATHER_WINDOW", "HIDDEN_GEM", "RAIN_ALTERNATIVE"
    priority: float
    title: str
    reason: str
    poi_id: Optional[int] = None
    poi_name: Optional[str] = None
    action_text: str = "Add to plan"
    expires_at: Optional[str] = None
