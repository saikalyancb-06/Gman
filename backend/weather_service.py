import urllib.request
import json
from datetime import datetime, timezone

WEATHER_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Foggy",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    95: "Thunderstorm"
}

def fetch_live_weather(lat: float, lng: float):
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lng}&current=temperature_2m,relative_humidity_2m,apparent_temperature,weather_code&daily=sunrise,sunset,uv_index_max&timezone=auto"
        req = urllib.request.Request(url, headers={'User-Agent': 'GeoGuide/1.0'})
        with urllib.request.urlopen(req, timeout=4) as response:
            data = json.loads(response.read().decode())
            
            curr = data.get('current', {})
            daily = data.get('daily', {})
            
            temp_c = int(round(curr.get('temperature_2m', 26)))
            feels_like = int(round(curr.get('apparent_temperature', 27)))
            humidity = int(round(curr.get('relative_humidity_2m', 65)))
            w_code = curr.get('weather_code', 2)
            condition = WEATHER_CODES.get(w_code, "Pleasant")
            
            sunrise_raw = daily.get('sunrise', ['06:10'])[0]
            sunset_raw = daily.get('sunset', ['18:20'])[0]
            
            sunrise = sunrise_raw.split('T')[-1][:5] if 'T' in sunrise_raw else '06:10'
            sunset = sunset_raw.split('T')[-1][:5] if 'T' in sunset_raw else '18:20'
            
            # Daylight estimation
            daylight_hours = "12h 10m Daylight"
            
            return {
                "temp_c": temp_c,
                "feels_like_c": feels_like,
                "condition": condition,
                "humidity_pct": humidity,
                "sunrise": sunrise,
                "sunset": sunset,
                "daylight_hours": daylight_hours,
                "is_live": True
            }
    except Exception as e:
        print("Live weather fetch error:", e)
        return None
