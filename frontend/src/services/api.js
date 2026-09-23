const API_BASE = '/api';

export const apiService = {
  async getHealth() {
    const res = await fetch(API_BASE + '/health');
    return res.json();
  },

  async getCities() {
    const res = await fetch(API_BASE + '/cities');
    return res.json();
  },

  async resolveGeoContext(destinationNameOrId, coords = null, query = null) {
    const res = await fetch(API_BASE + '/geocontext/resolve', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        destination_id: destinationNameOrId,
        lat: coords?.lat,
        lng: coords?.lng,
        query: query
      })
    });
    return res.json();
  },

  async getKnowledgePackStatus(destId = 1) {
    const res = await fetch(API_BASE + '/knowledge-packs/' + destId + '/status');
    return res.json();
  },

  async buildKnowledgePack(destId = 1, forceRefresh = false) {
    const res = await fetch(API_BASE + '/knowledge-packs/build', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ destination_id: destId, force_refresh: forceRefresh })
    });
    return res.json();
  },

  async getNowContext(cityId = 1, userId = 1, lang = 'en', coords = null) {
    let url = API_BASE + '/context/now?user_id=' + userId + '&lang=' + lang;
    if (cityId) url += '&city_id=' + cityId;
    if (coords) url += '&lat=' + coords.lat + '&lng=' + coords.lng;
    const res = await fetch(url);
    return res.json();
  },

  async getCopilotNextAction(cityId = 1) {
    const res = await fetch(API_BASE + '/copilot/next-action?city_id=' + cityId);
    return res.json();
  },

  async getNearby(cityId = 1, category = 'all', search = '', stepFree = false, hiddenGems = false, userLocation = null) {
    let url = API_BASE + '/nearby?city_id=' + cityId + '&category=' + category;
    if (search) url += '&search=' + encodeURIComponent(search);
    if (stepFree) url += '&step_free=true';
    if (hiddenGems) url += '&hidden_gems=true';
    if (userLocation) url += '&user_lat=' + userLocation.lat + '&user_lng=' + userLocation.lng;
    const res = await fetch(url);
    return res.json();
  },

  async getPlaceEvidence(poiId) {
    const res = await fetch(API_BASE + '/places/' + poiId + '/evidence');
    return res.json();
  },

  async getPlan(durationType = 'full_day', optimizationFilter = 'balanced', cityId = 1, userId = 1, naturalInstruction = null) {
    const res = await fetch(API_BASE + '/plan', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        duration_type: durationType,
        optimization_filter: optimizationFilter,
        city_id: cityId,
        user_id: userId,
        natural_language_instruction: naturalInstruction
      })
    });
    return res.json();
  },

  async askQuery(query, language = 'en', cityId = 1, coords = null) {
    const res = await fetch(API_BASE + '/ask', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query: query,
        language: language,
        city_id: cityId,
        user_lat: coords?.lat,
        user_lng: coords?.lng,
        accuracy_m: coords?.accuracy || 10.0,
        location_source: coords ? 'gps' : 'ambient'
      })
    });
    return res.json();
  },

  async identifyPlace(hint, cityId = 1) {
    const res = await fetch(API_BASE + '/vision/identify', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        landmark_hint: hint,
        city_id: cityId
      })
    });
    return res.json();
  },

  async getProfile(userId = 1) {
    const res = await fetch(API_BASE + '/profile?user_id=' + userId);
    return res.json();
  },

  async updateProfile(updates, userId = 1) {
    const res = await fetch(API_BASE + '/profile?user_id=' + userId, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(updates)
    });
    return res.json();
  },

  async toggleBookmark(poiId, user_id = 1) {
    const res = await fetch(API_BASE + '/bookmarks/' + poiId + '?user_id=' + user_id, {
      method: 'POST'
    });
    return res.json();
  },

  async simulateSignal(signalType) {
    const res = await fetch(API_BASE + '/simulate/signal', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ signal_type: signalType })
    });
    return res.json();
  }
};
