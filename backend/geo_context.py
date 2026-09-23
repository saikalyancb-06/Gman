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
    FRESH = "FRESH"       # < 2 minutes (120s)
    USABLE = "USABLE"     # 2 - 10 minutes (600s)
    STALE = "STALE"       # > 10 minutes

class ResolutionStatus(str, Enum):
    EXACT = "EXACT"
    APPROXIMATE = "APPROXIMATE"
    STALE = "STALE"
    UNRESOLVED = "UNRESOLVED"
    UNAVAILABLE = "UNAVAILABLE"
    PERMISSION_DENIED = "PERMISSION_DENIED"

class UserGeoContext(BaseModel):
    """
    Authoritative physical user location context.
    Represents WHERE THE USER PHYSICALLY IS with explicit accuracy, freshness, and status.
    Never invents or falls back to an unrelated city if physical GPS is missing.
    """
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    accuracy_m: Optional[float] = None
    altitude_m: Optional[float] = None
    timestamp: float = Field(default_factory=lambda: time.time())
    source: str = "GPS"  # "GPS", "IP", "MANUAL", "UNSET"
    permission_state: LocationPermissionState = LocationPermissionState.LOCATION_AVAILABLE
    resolution_status: ResolutionStatus = ResolutionStatus.UNRESOLVED

    # Geocoded hierarchy of user's physical presence
    street: Optional[str] = None
    neighborhood: Optional[str] = None
    locality: Optional[str] = None
    sublocality: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    country: str = "India"
    geocoded_address: Optional[str] = None
    location_confidence: float = 0.0

    def get_freshness(self) -> LocationFreshness:
        age_seconds = time.time() - self.timestamp
        if age_seconds < 120:
            return LocationFreshness.FRESH
        elif age_seconds < 600:
            return LocationFreshness.USABLE
        return LocationFreshness.STALE

    def is_precise(self) -> bool:
        if self.latitude is None or self.longitude is None:
            return False
        if self.permission_state in [
            LocationPermissionState.LOCATION_PERMISSION_DENIED,
            LocationPermissionState.LOCATION_UNAVAILABLE,
            LocationPermissionState.LOCATION_PERMISSION_REQUIRED
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
        return ", ".join(parts) if parts else self.city or "Unknown physical location"

    @classmethod
    def create_unavailable(cls, reason: LocationPermissionState = LocationPermissionState.LOCATION_UNAVAILABLE) -> 'UserGeoContext':
        return cls(
            latitude=None,
            longitude=None,
            accuracy_m=None,
            source="UNSET",
            permission_state=reason,
            resolution_status=ResolutionStatus.UNAVAILABLE if reason != LocationPermissionState.LOCATION_PERMISSION_DENIED else ResolutionStatus.PERMISSION_DENIED,
            location_confidence=0.0
        )

class QueryDestinationContext(BaseModel):
    """
    Target destination context derived from query understanding or user selection.
    Represents WHAT PLACE THE USER IS ASKING ABOUT.
    Completely decoupled from physical GPS context.
    """
    destination_id: Optional[int] = None
    city_id: Optional[int] = None
    destination_name: Optional[str] = None
    city_name: Optional[str] = None
    neighborhood: Optional[str] = None
    landmark_or_poi: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    radius_m: int = 15000
    resolution_source: str = "EXPLICIT_QUERY"  # "EXPLICIT_QUERY", "POI_ENTITY", "USER_PICKER", "SESSION_DEFAULT"
    confidence: float = 0.85
    is_resolved: bool = True

class GeoContext(BaseModel):
    """
    Authoritative Unified GeoContext combining physical user context
    and target destination context.
    Maintains backward compatibility while enforcing strict separation.
    """
    # User physical location context
    user_location: Optional[UserGeoContext] = None

    # Destination context
    destination_context: Optional[QueryDestinationContext] = None

    # Flat properties preserved for existing schemas & clients
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    accuracy_m: Optional[float] = None
    timestamp: float = Field(default_factory=lambda: time.time())
    source: str = "GPS"
    permission_state: LocationPermissionState = LocationPermissionState.LOCATION_AVAILABLE

    street: Optional[str] = None
    neighborhood: Optional[str] = None
    locality: Optional[str] = None
    sublocality: Optional[str] = None
    city: str = "Bengaluru"
    district: Optional[str] = None
    state: str = "Karnataka"
    country: str = "India"
    geocoded_address: Optional[str] = None

    city_id: Optional[int] = 2
    destination_id: Optional[int] = 2
    destination_name: Optional[str] = "Bengaluru"
    location_confidence: float = 0.90
    resolution_status: ResolutionStatus = ResolutionStatus.EXACT

    def get_freshness(self) -> LocationFreshness:
        if self.user_location:
            return self.user_location.get_freshness()
        age_seconds = time.time() - self.timestamp
        if age_seconds < 120:
            return LocationFreshness.FRESH
        elif age_seconds < 600:
            return LocationFreshness.USABLE
        return LocationFreshness.STALE

    def is_precise(self) -> bool:
        if self.user_location:
            return self.user_location.is_precise()
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
        user_loc = UserGeoContext(
            latitude=lat,
            longitude=lng,
            accuracy_m=accuracy_m,
            source=source,
            neighborhood=neighborhood,
            city=city_name,
            geocoded_address=address,
            permission_state=LocationPermissionState.LOCATION_AVAILABLE,
            resolution_status=ResolutionStatus.EXACT,
            location_confidence=0.95
        )
        dest = QueryDestinationContext(
            city_id=city_id,
            destination_id=city_id,
            city_name=city_name,
            destination_name=city_name,
            latitude=lat,
            longitude=lng,
            confidence=0.95
        )
        return cls(
            user_location=user_loc,
            destination_context=dest,
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
            permission_state=LocationPermissionState.LOCATION_AVAILABLE,
            location_confidence=0.95,
            resolution_status=ResolutionStatus.EXACT
        )

    @classmethod
    def fallback_destination(cls, city_id: int = 1, city_name: str = "Hampi", lat: float = 15.3350, lng: float = 76.4600) -> 'GeoContext':
        dest = QueryDestinationContext(
            destination_id=city_id,
            city_id=city_id,
            destination_name=city_name,
            city_name=city_name,
            latitude=lat,
            longitude=lng,
            resolution_source="SESSION_DEFAULT",
            confidence=0.70
        )
        user_loc = UserGeoContext.create_unavailable()
        return cls(
            user_location=user_loc,
            destination_context=dest,
            latitude=lat,
            longitude=lng,
            accuracy_m=1000.0,
            timestamp=time.time(),
            source="fallback_destination",
            city=city_name,
            city_id=city_id,
            destination_id=city_id,
            destination_name=city_name,
            permission_state=LocationPermissionState.LOCATION_UNAVAILABLE,
            location_confidence=0.70,
            resolution_status=ResolutionStatus.APPROXIMATE
        )
