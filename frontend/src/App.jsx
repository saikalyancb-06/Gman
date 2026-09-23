import React, { useState, useEffect } from 'react';
import { Home, Compass, Mic, Calendar, User, MapPin, Navigation, ChevronDown, WifiOff } from 'lucide-react';
import { apiService } from './services/api';
import NowScreen from './components/NowScreen';
import NearbyScreen from './components/NearbyScreen';
import PlanScreen from './components/PlanScreen';
import AskScreen from './components/AskScreen';
import ProfileScreen from './components/ProfileScreen';
import PlaceDetailModal from './components/PlaceDetailModal';

import { useLocationContext } from './context/LocationContext';

export default function App() {
  const { 
    userGeo, 
    userCoords, 
    destination, 
    destinationId, 
    destinationName, 
    availableCities, 
    selectDestination, 
    requestUserLocation 
  } = useLocationContext();

  const [currentTab, setCurrentTab] = useState('now');
  const [selectedPlace, setSelectedPlace] = useState(null);
  const [nowData, setNowData] = useState(null);
  const [language, setLanguage] = useState('en');
  const [askInitialQuery, setAskInitialQuery] = useState('');
  const [showCityPicker, setShowCityPicker] = useState(false);
  const [isOffline, setIsOffline] = useState(!navigator.onLine);

  useEffect(() => {
    // Network listeners for Offline-First mode
    const handleOnline = () => setIsOffline(false);
    const handleOffline = () => setIsOffline(true);
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    loadNowContext(destinationId, userCoords);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, [language, destinationId, userCoords]);

  const loadNowContext = async (cityId = 1, coords = null) => {
    try {
      const res = await apiService.getNowContext(cityId, 1, language, coords);
      setNowData(res);
      // Cache in localStorage for offline resiliency
      localStorage.setItem('geoguide_cached_now', JSON.stringify(res));
    } catch (err) {
      console.warn('Network issue, reading from local offline cache:', err);
      const cached = localStorage.getItem('geoguide_cached_now');
      if (cached) setNowData(JSON.parse(cached));
    }
  };

  const handleCitySelect = (cityId) => {
    selectDestination(cityId);
    setShowCityPicker(false);
  };

  const handleUseLiveGPS = async () => {
    setShowCityPicker(false);
    try {
      const coords = await requestUserLocation();
      loadNowContext(destinationId, { lat: coords.latitude, lng: coords.longitude });
    } catch (err) {
      console.log('GPS request completed with status:', err);
    }
  };

  const handleAddToPlan = (place) => {
    alert(`${place.name} added to your active trip plan!`);
    setCurrentTab('plan');
  };

  const handleAskQuestion = (question) => {
    setAskInitialQuery(question);
    setCurrentTab('ask');
  };

  return (
    <div className="min-h-screen bg-black text-white flex justify-center selection:bg-[#F8D348] selection:text-black font-sans">
      <div className="w-full max-w-md min-h-screen flex flex-col relative bg-[#0D0D0E] border-x border-[#1E1E20] shadow-2xl">
        
        {/* Offline Banner Indicator */}
        {isOffline && (
          <div className="bg-[#FF453A] text-black text-[11px] font-bold px-4 py-1.5 flex items-center justify-between z-50 animate-fade-in">
            <div className="flex items-center space-x-1.5">
              <WifiOff size={14} />
              <span>Offline Mode • Showing cached verified information</span>
            </div>
            <span className="text-[10px] uppercase font-mono">Last updated 14:32</span>
          </div>
        )}

        {/* Top Destination Selector Bar */}
        <div className="bg-[#161618] px-4 py-2.5 border-b border-[#2C2C2E] flex items-center justify-between z-30">
          <button 
            onClick={() => setShowCityPicker(!showCityPicker)}
            className="flex items-center space-x-1.5 bg-[#242426] hover:bg-[#2C2C2E] px-3 py-1.5 rounded-full border border-neutral-700 text-xs font-semibold text-neutral-200 transition-colors"
          >
            <MapPin size={14} className="text-[#F8D348]" />
            <span>{nowData?.location?.city || 'Hampi'}</span>
            <ChevronDown size={14} className="text-neutral-400" />
          </button>

          <button 
            onClick={handleUseLiveGPS}
            className="flex items-center space-x-1 text-[11px] text-[#30D158] bg-[#30D158]/10 px-2.5 py-1 rounded-full border border-[#30D158]/20 font-medium hover:bg-[#30D158]/20 transition-all"
            title="Update to current GPS location"
          >
            <Navigation size={12} className="animate-pulse" />
            <span>Live GPS</span>
          </button>
        </div>

        {/* City Picker Dropdown Modal */}
        {showCityPicker && (
          <div className="absolute top-12 left-4 right-4 bg-[#1C1C1E] border border-[#3A3A3C] rounded-2xl shadow-2xl p-2 z-50 animate-fade-in space-y-1 text-xs">
            <p className="px-3 py-1 text-[10px] uppercase font-bold text-neutral-400 tracking-wider">Select Destination</p>
            
            <button
              onClick={handleUseLiveGPS}
              className="w-full text-left px-3 py-2 rounded-xl hover:bg-[#2C2C2E] text-neutral-200 flex items-center justify-between"
            >
              <span className="flex items-center space-x-2">
                <Navigation size={14} className="text-[#30D158]" />
                <span className="font-semibold text-white">📍 Current Live Location (GPS)</span>
              </span>
            </button>

            {availableCities.map(c => (
              <button
                key={c.id}
                onClick={() => handleCitySelect(c.id)}
                className={'w-full text-left px-3 py-2 rounded-xl hover:bg-[#2C2C2E] flex items-center justify-between ' + (destinationId === c.id ? 'bg-[#242116] text-[#F8D348] font-bold' : 'text-neutral-300')}
              >
                <span>{c.name} ({c.state})</span>
                {destinationId === c.id && <span className="text-xs">✔</span>}
              </button>
            ))}
          </div>
        )}

        {/* Main Screen Content View */}
        <main className="flex-1 px-4 pt-4 overflow-y-auto pb-24">
          {currentTab === 'now' && (
            <NowScreen 
              data={nowData} 
              onSelectPlace={(p) => setSelectedPlace(p)}
              onTabChange={(tab) => setCurrentTab(tab)}
              onAskQuestion={handleAskQuestion}
            />
          )}

          {currentTab === 'nearby' && (
            <NearbyScreen 
              cityId={destinationId || 1}
              userLocation={userCoords}
              onSelectPlace={(p) => setSelectedPlace(p)}
              onAskQuestion={handleAskQuestion}
            />
          )}

          {currentTab === 'plan' && (
            <PlanScreen 
              cityId={destinationId || 1}
              userLocation={userCoords}
              onSelectPlace={(p) => setSelectedPlace(p)}
              onAskQuestion={handleAskQuestion}
            />
          )}

          {currentTab === 'ask' && (
            <AskScreen 
              cityId={destinationId || 1}
              cityName={destinationName || nowData?.location?.city || 'Hampi'}
              initialQuery={askInitialQuery}
              language={language}
              userLocation={userCoords}
              onLocationUpdate={requestUserLocation}
              onLanguageChange={(l) => setLanguage(l)}
              onSelectPlace={(p) => setSelectedPlace(p)}
            />
          )}

          {currentTab === 'profile' && (
            <ProfileScreen 
              language={language}
              onLanguageChange={(l) => setLanguage(l)}
            />
          )}
        </main>

        <PlaceDetailModal 
          place={selectedPlace}
          onClose={() => setSelectedPlace(null)}
          onAddToPlan={handleAddToPlan}
          onAskAbout={handleAskQuestion}
        />

        {/* Bottom Navigation Bar */}
        <nav className="fixed bottom-0 left-1/2 -translate-x-1/2 w-full max-w-md bg-[#161618]/95 backdrop-blur-md border-t border-[#2C2C2E] py-2 px-3 z-40 flex items-center justify-around">
          
          <button
            onClick={() => setCurrentTab('now')}
            className={'flex flex-col items-center justify-center py-1 px-2 rounded-xl transition-all ' + (currentTab === 'now' ? 'text-[#F8D348]' : 'text-neutral-400 hover:text-neutral-200')}
          >
            <Home size={20} strokeWidth={currentTab === 'now' ? 2.5 : 2} />
            <span className="text-[10px] font-medium mt-1">Now</span>
          </button>

          <button
            onClick={() => setCurrentTab('nearby')}
            className={'flex flex-col items-center justify-center py-1 px-2 rounded-xl transition-all ' + (currentTab === 'nearby' ? 'text-[#F8D348]' : 'text-neutral-400 hover:text-neutral-200')}
          >
            <Compass size={20} strokeWidth={currentTab === 'nearby' ? 2.5 : 2} />
            <span className="text-[10px] font-medium mt-1">Nearby</span>
          </button>

          <button
            onClick={() => {
              setAskInitialQuery('');
              setCurrentTab('ask');
            }}
            className={'-mt-5 p-3.5 rounded-full shadow-lg transition-all active:scale-90 ' + (currentTab === 'ask' ? 'bg-[#F8D348] text-black ring-4 ring-[#F8D348]/30' : 'bg-[#F8D348] text-black hover:bg-[#ffe066]')}
            title="Ask GeoGuide AI"
          >
            <Mic size={22} className="stroke-[2.5]" />
          </button>

          <button
            onClick={() => setCurrentTab('plan')}
            className={'flex flex-col items-center justify-center py-1 px-2 rounded-xl transition-all ' + (currentTab === 'plan' ? 'text-[#F8D348]' : 'text-neutral-400 hover:text-neutral-200')}
          >
            <Calendar size={20} strokeWidth={currentTab === 'plan' ? 2.5 : 2} />
            <span className="text-[10px] font-medium mt-1">Plan</span>
          </button>

          <button
            onClick={() => setCurrentTab('profile')}
            className={'flex flex-col items-center justify-center py-1 px-2 rounded-xl transition-all ' + (currentTab === 'profile' ? 'text-[#F8D348]' : 'text-neutral-400 hover:text-neutral-200')}
          >
            <User size={20} strokeWidth={currentTab === 'profile' ? 2.5 : 2} />
            <span className="text-[10px] font-medium mt-1">Profile</span>
          </button>

        </nav>

      </div>
    </div>
  );
}
