import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { apiService } from '../services/api';

/**
 * Canonical Location Context for GeoGuide.
 * Unifies:
 * 1. Physical User Location (UserGeoContext: live GPS, accuracy, permission state)
 * 2. Active Query/Destination Location (QueryDestinationContext: selected destination or query-specified target)
 * 
 * Strict architectural rule: Physical user GPS and Destination context are distinct concepts.
 * GPS failure or missing GPS NEVER silently defaults destination to a random city.
 */

const LocationContext = createContext(null);

export const ResolutionStatus = {
  UNRESOLVED: 'UNRESOLVED',
  EXACT_COORDINATES: 'EXACT_COORDINATES',
  GEOCODED_PROXIMITY: 'GEOCODED_PROXIMITY',
  ADMINISTRATIVE_MATCH: 'ADMINISTRATIVE_MATCH',
  EXPLICIT_NAME: 'EXPLICIT_NAME',
  FALLBACK_REFERENCE: 'FALLBACK_REFERENCE'
};

export const PermissionState = {
  UNKNOWN: 'UNKNOWN',
  REQUESTING: 'REQUESTING',
  AVAILABLE: 'AVAILABLE',
  DENIED: 'DENIED',
  UNAVAILABLE: 'UNAVAILABLE'
};

export function LocationProvider({ children }) {
  // 1. Physical Device Geolocation State
  const [userGeo, setUserGeo] = useState({
    latitude: null,
    longitude: null,
    accuracyMeters: null,
    permissionState: PermissionState.UNKNOWN,
    source: null,
    timestamp: null
  });

  // 2. Active Query / Destination Context
  const [destination, setDestination] = useState({
    id: 1,
    name: 'Hampi',
    state: 'Karnataka',
    latitude: 15.3350,
    longitude: 76.4600,
    radiusMeters: 15000,
    resolutionStatus: ResolutionStatus.FALLBACK_REFERENCE
  });

  const [availableCities, setAvailableCities] = useState([]);
  const [isLocating, setIsLocating] = useState(false);

  // Fetch available registered destinations
  useEffect(() => {
    apiService.getCities()
      .then(res => {
        if (res && res.cities) {
          setAvailableCities(res.cities);
        }
      })
      .catch(err => console.warn('[LocationContext] getCities:', err));
  }, []);

  // Request high-accuracy live GPS
  const requestUserLocation = useCallback(() => {
    if (!navigator.geolocation) {
      setUserGeo(prev => ({
        ...prev,
        permissionState: PermissionState.UNAVAILABLE
      }));
      return Promise.reject(new Error('Geolocation not supported'));
    }

    setIsLocating(true);
    setUserGeo(prev => ({ ...prev, permissionState: PermissionState.REQUESTING }));

    return new Promise((resolve, reject) => {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          const userCoords = {
            latitude: pos.coords.latitude,
            longitude: pos.coords.longitude,
            accuracyMeters: pos.coords.accuracy,
            permissionState: PermissionState.AVAILABLE,
            source: 'GPS',
            timestamp: pos.timestamp || Date.now()
          };
          setUserGeo(userCoords);
          setIsLocating(false);
          resolve(userCoords);
        },
        (err) => {
          console.warn('[LocationContext] GPS error:', err.message);
          setUserGeo(prev => ({
            ...prev,
            permissionState: err.code === 1 ? PermissionState.DENIED : PermissionState.UNAVAILABLE
          }));
          setIsLocating(false);
          reject(err);
        },
        { enableHighAccuracy: true, timeout: 8000, maximumAge: 30000 }
      );
    });
  }, []);

  // Set explicit destination
  const selectDestination = useCallback((cityIdOrName) => {
    const target = availableCities.find(
      c => c.id === Number(cityIdOrName) || c.name.toLowerCase() === String(cityIdOrName).toLowerCase()
    );

    if (target) {
      setDestination({
        id: target.id,
        name: target.name,
        state: target.state || 'Karnataka',
        latitude: target.lat || target.latitude,
        longitude: target.lng || target.longitude,
        radiusMeters: target.name === 'Hampi' ? 15000 : 25000,
        resolutionStatus: ResolutionStatus.EXPLICIT_NAME
      });
    }
  }, [availableCities]);

  // Initial GPS check on mount (non-blocking)
  useEffect(() => {
    requestUserLocation().catch(() => {
      // Graceful non-blocking degradation
    });
  }, [requestUserLocation]);

  const value = {
    userGeo,
    destination,
    availableCities,
    isLocating,
    requestUserLocation,
    selectDestination,
    // Convenience getters
    userCoords: userGeo.latitude ? { lat: userGeo.latitude, lng: userGeo.longitude, accuracy: userGeo.accuracyMeters } : null,
    destinationId: destination.id,
    destinationName: destination.name
  };

  return (
    <LocationContext.Provider value={value}>
      {children}
    </LocationContext.Provider>
  );
}

export function useLocationContext() {
  const ctx = useContext(LocationContext);
  if (!ctx) {
    throw new Error('useLocationContext must be used within a LocationProvider');
  }
  return ctx;
}
