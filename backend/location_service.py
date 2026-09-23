import time
import math
import json
import urllib.request
import urllib.parse
from typing import Optional, Dict, Any, List, Tuple
from backend.geo_context import GeoContext, LocationPermissionState
from backend.pg_database import get_pg_connection

REVERSE_GEOCODE_CACHE: Dict[str, Dict[str, Any]] = {}

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Haversine distance in meters."""
    R = 6371000.0  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * (math.sin(delta_lambda / 2.0) ** 2))
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c

class LocationService:
    """
    Hierarchical Location & Spatial Proximity Service for GeoGuide.
    Features:
    - PostGIS / earthdistance spatial search with adaptive radius expansion
    - Reverse geocoding with spatial tolerance caching
    - Canonical GeoContext resolution
    """
    ADAPTIVE_RADII_METERS = [1000, 3000, 5000, 10000]

    @staticmethod
    def reverse_geocode(lat: float, lon: float) -> Dict[str, Any]:
        """
        Reverse geocodes (lat, lon) with spatial tolerance cache (~50m).
        Returns hierarchy: neighborhood, locality, city, district, state, country.
        """
        # 1. Check in-memory tolerance cache
        for cache_key, val in REVERSE_GEOCODE_CACHE.items():
            c_lat, c_lon = map(float, cache_key.split(","))
            if haversine_distance(lat, lon, c_lat, c_lon) < 75.0:
                return val

        # 2. Check PostgreSQL web_cache
        cache_db_key = f"revgeo::{round(lat, 4)}::{round(lon, 4)}"
        try:
            conn = get_pg_connection()
            with conn.cursor() as cur:
                cur.execute("SELECT payload_json FROM web_cache WHERE cache_key = %s AND expires_at > CURRENT_TIMESTAMP;", (cache_db_key,))
                row = cur.fetchone()
                if row:
                    conn.close()
                    REVERSE_GEOCODE_CACHE[f"{lat},{lon}"] = row[0]
                    return row[0]
            conn.close()
        except Exception:
            pass

        # 3. Call OpenStreetMap Nominatim reverse endpoint
        result = {
            "street": None,
            "neighborhood": None,
            "locality": None,
            "city": "Bengaluru",
            "state": "Karnataka",
            "country": "India",
            "display_name": f"{lat:.4f}, {lon:.4f}"
        }

        try:
            url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json&addressdetails=1"
            req = urllib.request.Request(url, headers={'User-Agent': 'GeoGuide-Location-Intelligence/2.0 (contact@geoguide.ai)'})
            with urllib.request.urlopen(req, timeout=4) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                addr = data.get("address", {})
                result["street"] = addr.get("road")
                result["neighborhood"] = addr.get("neighbourhood") or addr.get("suburb") or addr.get("residential")
                result["locality"] = addr.get("city_district") or addr.get("suburb") or addr.get("neighbourhood")
                result["city"] = addr.get("city") or addr.get("town") or addr.get("municipality") or "Bengaluru"
                result["state"] = addr.get("state") or "Karnataka"
                result["country"] = addr.get("country") or "India"
                result["display_name"] = data.get("display_name", "")

                # Cache in PostgreSQL
                conn = get_pg_connection()
                with conn.cursor() as cur:
                    cur.execute("""
                    INSERT INTO web_cache (cache_key, query, entity_name, destination_name, payload_json, source_name, expires_at)
                    VALUES (%s, %s, 'ReverseGeocode', %s, %s, 'Nominatim Reverse', CURRENT_TIMESTAMP + INTERVAL '30 days')
                    ON CONFLICT (cache_key) DO UPDATE SET payload_json = EXCLUDED.payload_json;
                    """, (cache_db_key, f"{lat},{lon}", result["city"], json.dumps(result)))
                conn.close()

        except Exception as e:
            # Fallback based on known coordinate centers
            if haversine_distance(lat, lon, 12.9431, 77.5741) < 2500:
                result["neighborhood"] = "Gandhi Bazaar"
                result["locality"] = "Basavanagudi"
                result["city"] = "Bengaluru"
            elif haversine_distance(lat, lon, 12.9352, 77.5348) < 2500:
                result["neighborhood"] = "Girinagar"
                result["locality"] = "Banashankari"
                result["city"] = "Bengaluru"
            elif haversine_distance(lat, lon, 15.3350, 76.4600) < 5000:
                result["neighborhood"] = "Hampi Bazaar"
                result["city"] = "Hampi"

        REVERSE_GEOCODE_CACHE[f"{lat},{lon}"] = result
        return result

    @staticmethod
    def resolve_context(
        lat: Optional[float] = None,
        lon: Optional[float] = None,
        accuracy_m: Optional[float] = None,
        explicit_query: Optional[str] = None,
        session_city_id: int = 2
    ) -> GeoContext:
        """
        Builds a canonical GeoContext from coordinates or ambient session.
        Explicit query overrides take highest precedence for target destination,
        while device coordinates represent the physical user position.
        """
        if lat is not None and lon is not None:
            rev = LocationService.reverse_geocode(lat, lon)
            city_name = rev.get("city", "Bengaluru")
            
            # Map city_name to city_id
            city_id = 2
            if "hampi" in city_name.lower():
                city_id = 1
            elif "mys" in city_name.lower():
                city_id = 3

            ctx = GeoContext(
                latitude=lat,
                longitude=lon,
                accuracy_m=accuracy_m or 10.0,
                timestamp=time.time(),
                source="GPS",
                permission_state=LocationPermissionState.LOCATION_AVAILABLE,
                street=rev.get("street"),
                neighborhood=rev.get("neighborhood"),
                locality=rev.get("locality"),
                city=city_name,
                state=rev.get("state", "Karnataka"),
                country=rev.get("country", "India"),
                geocoded_address=rev.get("display_name"),
                city_id=city_id,
                destination_id=city_id,
                destination_name=city_name
            )
            return ctx

        # Fallback when coordinates are unavailable
        city_id = session_city_id or 2
        city_name = "Hampi" if city_id == 1 else ("Mysuru" if city_id == 3 else "Bengaluru")
        default_coords = {
            1: (15.3350, 76.4600),
            2: (12.9716, 77.5946),
            3: (12.2958, 76.6394)
        }.get(city_id, (12.9716, 77.5946))

        return GeoContext(
            latitude=default_coords[0],
            longitude=default_coords[1],
            accuracy_m=1000.0,
            timestamp=time.time(),
            source="fallback_destination",
            permission_state=LocationPermissionState.LOCATION_UNAVAILABLE,
            city=city_name,
            city_id=city_id,
            destination_id=city_id,
            destination_name=city_name
        )

    @staticmethod
    def search_nearby_places(
        lat: float,
        lon: float,
        category_slug: Optional[str] = None,
        keywords: Optional[List[str]] = None,
        max_radius_m: int = 5000,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Executes PostGIS / earthdistance spatial search across PostgreSQL `activities_poi` and `entities`.
        Expands radius adaptively if results are insufficient.
        """
        conn = get_pg_connection()
        found_places = []

        with conn.cursor() as cur:
            for radius_m in LocationService.ADAPTIVE_RADII_METERS:
                if radius_m > max_radius_m and found_places:
                    break

                # 1. Search in activities_poi using earthdistance
                query = """
                SELECT id, name, tag_badge, short_desc, full_desc, lat, lng,
                       category_id, open_time, close_time, entry_fee_inr, is_step_free,
                       rating, review_count,
                       earth_distance(ll_to_earth(%s, %s), ll_to_earth(lat, lng)) AS distance_m
                FROM activities_poi
                WHERE earth_box(ll_to_earth(%s, %s), %s) @> ll_to_earth(lat, lng)
                  AND earth_distance(ll_to_earth(%s, %s), ll_to_earth(lat, lng)) <= %s
                ORDER BY distance_m ASC
                LIMIT %s;
                """
                cur.execute(query, (lat, lon, lat, lon, radius_m, lat, lon, radius_m, limit))
                rows = cur.fetchall()

                for r in rows:
                    dist_m = float(r[14])
                    p = {
                        "id": r[0],
                        "name": r[1],
                        "tag_badge": r[2],
                        "short_desc": r[3],
                        "full_desc": r[4],
                        "lat": r[5],
                        "lng": r[6],
                        "category_id": r[7],
                        "open_time": r[8],
                        "close_time": r[9],
                        "entry_fee_inr": r[10],
                        "is_step_free": bool(r[11]),
                        "rating": r[12],
                        "review_count": r[13],
                        "distance_m": round(dist_m, 1),
                        "distance_km": round(dist_m / 1000.0, 2),
                        "walk_time_mins": max(1, int(dist_m / 80.0)), # ~4.8 km/h walk speed
                        "source": "PostgreSQL PostGIS / Spatial Index"
                    }
                    if not any(x["name"] == p["name"] for x in found_places):
                        found_places.append(p)

                # 2. Also search in entities table for local businesses and parks
                query_ent = """
                SELECT id, name, category, address, latitude, longitude,
                       earth_distance(ll_to_earth(%s, %s), ll_to_earth(latitude, longitude)) AS distance_m
                FROM entities
                WHERE latitude IS NOT NULL AND longitude IS NOT NULL
                  AND earth_box(ll_to_earth(%s, %s), %s) @> ll_to_earth(latitude, longitude)
                  AND earth_distance(ll_to_earth(%s, %s), ll_to_earth(latitude, longitude)) <= %s
                ORDER BY distance_m ASC
                LIMIT %s;
                """
                cur.execute(query_ent, (lat, lon, lat, lon, radius_m, lat, lon, radius_m, limit))
                for er in cur.fetchall():
                    dist_m = float(er[6])
                    ent_item = {
                        "id": er[0],
                        "name": er[1],
                        "category": er[2],
                        "address": er[3],
                        "lat": er[4],
                        "lng": er[5],
                        "short_desc": f"{er[1]} ({er[2]}) located at {er[3] or 'nearby'}",
                        "distance_m": round(dist_m, 1),
                        "distance_km": round(dist_m / 1000.0, 2),
                        "walk_time_mins": max(1, int(dist_m / 80.0)),
                        "source": "OpenStreetMap Local Places Spatial Index"
                    }
                    if not any(x["name"].lower() == ent_item["name"].lower() for x in found_places):
                        found_places.append(ent_item)

                if len(found_places) >= 3:
                    break

        conn.close()
        found_places.sort(key=lambda x: x["distance_m"])
        return found_places[:limit]
