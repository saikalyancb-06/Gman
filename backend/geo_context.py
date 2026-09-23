import time
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

class LocationPermissionState(str, Enum):
    LOCATION_AVAILABLE = "LOCATION_AVAILABLE"
    LOCATION_PERMISSION_REQUIRED = "LOCATION_PERMISSION_REQUIRED"
    LOCATION_PERMISSION_DENIED = "LOCATION_PERMISSION_DENIED"
    LOCATION_UNAVAILABLE = "LOCATION_UNAVAILABLE"
    LOCATION_STALE = "LOCATION_STALE"
    LOCATION_LOW_ACCURACY = "LOCATION_LOW_ACCURACY"
    MANUAL_LOCATION = "MANUAL_LOCATION"

class LocationFreshness(str, Enum):
    FRESH = "FRESH"       # < 2 minutes
    USABLE = "USABLE"     # 2 - 10 minutes
    STALE = "STALE"       # > 10 minutes

class GeoContext(BaseModel):
    """
    Canonical GeoContext used across GeoGuide.
    Ensures device coordinates, accuracy, reverse-geocoded hierarchy,
    and freshness are maintained consistently.
    """
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    accuracy_m: Optional[float] = None
    timestamp: float = Field(default_factory=lambda: time.time())
    source: str = "GPS"  # "GPS", "manual_pin", "searched_location", "fallback_destination"
    permission_state: LocationPermissionState = LocationPermissionState.LOCATION_AVAILABLE

    # Hierarchical Geographic Addressing
    street: Optional[str] = None
    neighborhood: Optional[str] = None
    locality: Optional[str] = None
    sublocality: Optional[str] = None
    city: str = "Bengaluru"
    district: Optional[str] = None
    state: str = "Karnataka"
    country: str = "India"
    geocoded_address: Optional[str] = None

    # Destination Scoping
    city_id: Optional[int] = 2
    destination_id: Optional[int] = 2
    destination_name: Optional[str] = "Bengaluru"

    def get_freshness(self) -> LocationFreshness:
        age_seconds = time.time() - self.timestamp
        if age_seconds < 120:
            return LocationFreshness.FRESH
        elif age_seconds < 600:
            return LocationFreshness.USABLE
        return LocationFreshness.STALE

    def is_precise(self) -> bool:
        """Returns True if valid GPS/manual coordinates exist and accuracy is acceptable."""
        if self.latitude is None or self.longitude is None:
            return False
        if self.permission_state in [
            LocationPermissionState.LOCATION_PERMISSION_DENIED,
            LocationPermissionState.LOCATION_UNAVAILABLE
        ]:
            return False
        if self.accuracy_m is not None and self.accuracy_m > 500:
            return False
        return True

    def get_display_location(self) -> str:
        parts = []
        if self.neighborhood:
            parts.append(self.neighborhood)
        elif self.locality:
            parts.append(self.locality)
        if self.city and self.city not in parts:
            parts.append(self.city)
        return ", ".join(parts) if parts else self.city or "Unknown Location"

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()

    @classmethod
    def from_coords(
        cls,
        lat: float,
        lng: float,
        accuracy_m: Optional[float] = 10.0,
        source: str = "GPS",
        city_id: Optional[int] = None,
        city_name: Optional[str] = None,
        neighborhood: Optional[str] = None,
        address: Optional[str] = None
    ) -> 'GeoContext':
        return cls(
            latitude=lat,
            longitude=lng,
            accuracy_m=accuracy_m,
            timestamp=time.time(),
            source=source,
            neighborhood=neighborhood,
            city=city_name or "Bengaluru",
            city_id=city_id or 2,
            destination_id=city_id or 2,
            destination_name=city_name or "Bengaluru",
            geocoded_address=address,
            permission_state=LocationPermissionState.LOCATION_AVAILABLE
        )

    @classmethod
    def fallback_destination(cls, city_id: int = 1, city_name: str = "Hampi", lat: float = 15.3350, lng: float = 76.4600) -> 'GeoContext':
        return cls(
            latitude=lat,
            longitude=lng,
            accuracy_m=1000.0,
            timestamp=time.time(),
            source="fallback_destination",
            city=city_name,
            city_id=city_id,
            destination_id=city_id,
            destination_name=city_name,
            permission_state=LocationPermissionState.LOCATION_UNAVAILABLE
        )
