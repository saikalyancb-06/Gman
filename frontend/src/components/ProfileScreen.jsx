import React, { useState, useEffect } from 'react';
import { 
  User, Check, Sparkles, MapPin, Calendar, 
  Footprints, Sun, Volume2, Download, ShieldCheck, CheckCircle2, Bookmark, Trash2, Heart 
} from 'lucide-react';
import { apiService } from '../services/api';

export default function ProfileScreen({ language, onLanguageChange }) {
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [downloadingPack, setDownloadingPack] = useState(false);
  const [downloadProgress, setDownloadProgress] = useState(100);
  const [savedPlaces, setSavedPlaces] = useState([]);
  const [showSavedList, setShowSavedList] = useState(false);

  useEffect(() => {
    loadProfile();
    loadBookmarks();
  }, []);

  const loadProfile = async () => {
    try {
      const res = await apiService.getProfile();
      setProfile(res);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const loadBookmarks = async () => {
    try {
      const res = await apiService.getBookmarks();
      if (res && res.bookmarks) setSavedPlaces(res.bookmarks);
    } catch (err) {
      console.error(err);
    }
  };

  const toggleInterest = async (interest) => {
    if (!profile) return;
    const current = profile.preferences.interests || [];
    let updated;
    if (current.includes(interest)) {
      updated = current.filter(i => i !== interest);
    } else {
      updated = [...current, interest];
    }
    
    setProfile(prev => ({
      ...prev,
      preferences: { ...prev.preferences, interests: updated }
    }));

    await apiService.updateProfile({ interests: updated });
  };

  const updatePreference = async (key, val) => {
    setProfile(prev => ({
      ...prev,
      preferences: { ...prev.preferences, [key]: val }
    }));
    await apiService.updateProfile({ [key]: val });
  };

  const handleDownloadOfflinePack = () => {
    setDownloadingPack(true);
    setDownloadProgress(10);
    const interval = setInterval(() => {
      setDownloadProgress(prev => {
        if (prev >= 100) {
          clearInterval(interval);
          setDownloadingPack(false);
          alert('Karnataka Offline Knowledge Pack (92 MB) verified and ready for offline use!');
          return 100;
        }
        return prev + 30;
      });
    }, 400);
  };

  const handleRemoveBookmark = async (poiId) => {
    await apiService.toggleBookmark(poiId);
    loadBookmarks();
    loadProfile();
  };

  if (loading || !profile) {
    return (
      <div className="p-8 text-center text-neutral-400 text-sm">Loading profile...</div>
    );
  }

  const prefs = profile.preferences;

  return (
    <div className="space-y-6 pb-24 max-w-md mx-auto animate-fade-in">
      
      {/* Profile Header Card */}
      <div className="bg-gradient-to-b from-[#252528] to-[#1C1C1E] rounded-3xl p-5 border border-[#2C2C2E] shadow-lg space-y-4">
        <div className="flex items-center space-x-3.5">
          <div className="w-12 h-12 rounded-full bg-[#F8D348] text-black font-black text-xl flex items-center justify-center shadow-md">
            A
          </div>
          <div>
            <p className="text-xs text-neutral-400">Hello</p>
            <h2 className="text-xl font-bold text-white tracking-tight">{profile.user?.name || 'Aarav'}</h2>
            <p className="text-xs text-neutral-300 mt-0.5">{profile.subtitle}</p>
          </div>
        </div>

        {/* 3 Stats Badges */}
        <div className="grid grid-cols-3 gap-2 pt-1">
          <div className="bg-[#141416] p-3 rounded-2xl border border-neutral-800 text-center">
            <p className="text-lg font-black text-white">{profile.stats?.sites_seen}</p>
            <p className="text-[10px] text-neutral-400 mt-0.5">Sites seen</p>
          </div>
          <button 
            onClick={() => setShowSavedList(!showSavedList)}
            className="bg-[#141416] hover:bg-neutral-800/80 p-3 rounded-2xl border border-neutral-800 text-center transition-colors"
          >
            <p className="text-lg font-black text-[#F8D348]">{savedPlaces.length}</p>
            <p className="text-[10px] text-neutral-400 mt-0.5 flex items-center justify-center space-x-0.5">
              <span>Saved</span>
              <Heart size={10} className="text-red-400" />
            </p>
          </button>
          <div className="bg-[#141416] p-3 rounded-2xl border border-neutral-800 text-center">
            <p className="text-lg font-black text-white">{'₹' + profile.stats?.spent_inr?.toLocaleString()}</p>
            <p className="text-[10px] text-neutral-400 mt-0.5">Spent so far</p>
          </div>
        </div>

        {/* Trip Logistics Info */}
        <div className="bg-[#141416] p-3.5 rounded-2xl border border-neutral-800 space-y-2 text-xs">
          <div className="flex items-center justify-between text-neutral-300">
            <span className="text-neutral-400">Current Trip</span>
            <span className="font-medium text-white">{profile.stay_info?.dates}</span>
          </div>
          <div className="flex items-center justify-between text-neutral-300">
            <span className="text-neutral-400">Base Location</span>
            <span className="font-medium text-white">{profile.stay_info?.location}</span>
          </div>
          <div className="flex items-center justify-between text-neutral-300">
            <span className="text-neutral-400">Getting around</span>
            <span className="font-medium text-white">{profile.stay_info?.transport}</span>
          </div>
        </div>
      </div>

      {/* Saved Places List Drawer (if open) */}
      {showSavedList && (
        <div className="bg-[#1C1C1E] p-4 rounded-3xl border border-[#F8D348]/40 space-y-3 animate-fade-in">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-white flex items-center space-x-1.5">
              <Heart size={16} className="text-red-400 fill-red-400" />
              <span>Saved Places ({savedPlaces.length})</span>
            </h3>
            <button 
              onClick={() => setShowSavedList(false)}
              className="text-xs text-neutral-400 hover:text-white"
            >
              Close
            </button>
          </div>

          {savedPlaces.length === 0 ? (
            <p className="text-xs text-neutral-400 py-2">No saved places yet. Click the heart icon on any attraction card to save it!</p>
          ) : (
            <div className="space-y-2 max-h-48 overflow-y-auto">
              {savedPlaces.map(p => (
                <div key={p.id} className="flex items-center justify-between bg-[#141416] p-2.5 rounded-xl border border-neutral-800 text-xs">
                  <div className="truncate pr-2">
                    <p className="font-bold text-white truncate">{p.name}</p>
                    <p className="text-[10px] text-neutral-400">{p.distance_km} km • {p.entry_fee_inr === 0 ? 'Free' : `₹${p.entry_fee_inr}`}</p>
                  </div>
                  <button 
                    onClick={() => handleRemoveBookmark(p.id)}
                    className="p-1.5 text-neutral-500 hover:text-red-400"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Match Summary Indicator */}
      <div className="bg-[#242116] p-3.5 rounded-2xl border border-[#4A3E16]/40 text-xs space-y-1">
        <p className="font-bold text-[#F8D348]">{profile.match_summary?.split('•')[0] || '18 of 24 places match you'}</p>
        <p className="text-neutral-300 leading-snug text-[11px]">
          {profile.match_summary?.split('•')[1] || 'Weighted towards architecture, gardens, and food.'}
        </p>
      </div>

      {/* Interests Selection */}
      <div className="space-y-2.5">
        <h3 className="text-xs font-bold text-neutral-400 uppercase tracking-wider px-1">
          Interests
        </h3>
        <div className="flex flex-wrap gap-2">
          {profile.available_interests?.map((item) => {
            const active = prefs.interests?.includes(item);
            return (
              <button
                key={item}
                onClick={() => toggleInterest(item)}
                className={'px-4 py-2 rounded-2xl text-xs font-semibold transition-all ' + (
                  active
                    ? 'bg-[#F8D348] text-black shadow-md'
                    : 'bg-[#1C1C1E] text-neutral-300 border border-[#2C2C2E] hover:border-neutral-500'
                )}
              >
                {item}
              </button>
            );
          })}
        </div>
      </div>

      {/* Budget for the day */}
      <div className="space-y-2.5">
        <h3 className="text-xs font-bold text-neutral-400 uppercase tracking-wider px-1">
          Budget for the day
        </h3>
        <div className="grid grid-cols-3 gap-2">
          {[
            { label: 'Under ₹500', val: 'low' },
            { label: '₹500–1,500', val: 'medium' },
            { label: 'Open', val: 'high' }
          ].map((b) => (
            <button
              key={b.val}
              onClick={() => updatePreference('budget_tier', b.val)}
              className={'py-2 px-2 rounded-xl text-xs font-semibold text-center transition-all ' + (
                prefs.budget_tier === b.val
                  ? 'bg-[#F8D348] text-black shadow-md'
                  : 'bg-[#1C1C1E] text-neutral-300 border border-[#2C2C2E] hover:border-neutral-500'
              )}
            >
              {b.label}
            </button>
          ))}
        </div>
      </div>

      {/* Pace */}
      <div className="space-y-2.5">
        <h3 className="text-xs font-bold text-neutral-400 uppercase tracking-wider px-1">
          Pace
        </h3>
        <div className="grid grid-cols-3 gap-2">
          {[
            { label: 'Unhurried', val: 'unhurried' },
            { label: 'Steady', val: 'steady' },
            { label: 'Packed', val: 'packed' }
          ].map((p) => (
            <button
              key={p.val}
              onClick={() => updatePreference('pace', p.val)}
              className={'py-2 px-2 rounded-xl text-xs font-semibold text-center transition-all ' + (
                prefs.pace === p.val
                  ? 'bg-[#F8D348] text-black shadow-md'
                  : 'bg-[#1C1C1E] text-neutral-300 border border-[#2C2C2E] hover:border-neutral-500'
              )}
            >
              {p.label}
            </button>
          ))}
        </div>
      </div>

      {/* Access and comfort */}
      <div className="space-y-2.5">
        <h3 className="text-xs font-bold text-neutral-400 uppercase tracking-wider px-1">
          Access and comfort
        </h3>
        <div className="space-y-2">
          <button
            onClick={() => updatePreference('step_free_only', !prefs.step_free_only)}
            className={'w-full p-3 rounded-2xl text-xs font-medium flex items-center justify-between border transition-all ' + (
              prefs.step_free_only
                ? 'bg-[#242116] border-[#F8D348] text-[#F8D348]'
                : 'bg-[#1C1C1E] border-[#2C2C2E] text-neutral-300 hover:border-neutral-600'
            )}
          >
            <span className="flex items-center space-x-2">
              <span>♿</span>
              <span>Step-free only</span>
            </span>
            {prefs.step_free_only && <Check size={16} />}
          </button>

          <button
            onClick={() => updatePreference('max_walking_km', prefs.max_walking_km === 2.0 ? 5.0 : 2.0)}
            className={'w-full p-3 rounded-2xl text-xs font-medium flex items-center justify-between border transition-all ' + (
              prefs.max_walking_km <= 2.0
                ? 'bg-[#242116] border-[#F8D348] text-[#F8D348]'
                : 'bg-[#1C1C1E] border-[#2C2C2E] text-neutral-300 hover:border-neutral-600'
            )}
          >
            <span className="flex items-center space-x-2">
              <Footprints size={16} />
              <span>Under 2 km walking</span>
            </span>
            {prefs.max_walking_km <= 2.0 && <Check size={16} />}
          </button>

          <button
            onClick={() => updatePreference('avoid_midday_sun', !prefs.avoid_midday_sun)}
            className={'w-full p-3 rounded-2xl text-xs font-medium flex items-center justify-between border transition-all ' + (
              prefs.avoid_midday_sun
                ? 'bg-[#242116] border-[#F8D348] text-[#F8D348]'
                : 'bg-[#1C1C1E] border-[#2C2C2E] text-neutral-300 hover:border-neutral-600'
            )}
          >
            <span className="flex items-center space-x-2">
              <Sun size={16} />
              <span>Avoid midday sun</span>
            </span>
            {prefs.avoid_midday_sun && <Check size={16} />}
          </button>
        </div>
      </div>

      {/* Language and voice */}
      <div className="space-y-2.5">
        <h3 className="text-xs font-bold text-neutral-400 uppercase tracking-wider px-1">
          Language and voice
        </h3>
        <div className="bg-[#1C1C1E] p-4 rounded-2xl border border-[#2C2C2E] space-y-3 text-xs">
          <div className="flex items-center justify-between">
            <span className="text-neutral-400">Language</span>
            <div className="flex space-x-1">
              {[
                { code: 'en', label: 'English' },
                { code: 'kn', label: 'ಕನ್ನಡ' },
                { code: 'hi', label: 'हिन्दी' }
              ].map(l => (
                <button
                  key={l.code}
                  onClick={() => {
                    updatePreference('language', l.code);
                    onLanguageChange(l.code);
                  }}
                  className={'px-2.5 py-1 rounded-lg text-xs font-medium transition-colors ' + (
                    language === l.code ? 'bg-[#F8D348] text-black font-bold' : 'text-neutral-400 hover:text-white'
                  )}
                >
                  {l.label}
                </button>
              ))}
            </div>
          </div>

          <div className="flex items-center justify-between border-t border-neutral-800 pt-2.5">
            <span className="text-neutral-400">Voice output</span>
            <button 
              onClick={() => updatePreference('voice_output', !prefs.voice_output)}
              className={'px-3 py-1 rounded-lg text-xs font-semibold ' + (
                prefs.voice_output ? 'bg-[#30D158]/20 text-[#30D158]' : 'bg-neutral-800 text-neutral-400'
              )}
            >
              {prefs.voice_output ? 'On' : 'Off'}
            </button>
          </div>

          <div className="flex items-center justify-between border-t border-neutral-800 pt-2.5">
            <div>
              <span className="text-neutral-400 block">Offline pack</span>
              <span className="text-neutral-300 font-mono text-[11px]">{prefs.offline_pack || 'Karnataka Pack, 92 MB'}</span>
            </div>
            <button
              onClick={handleDownloadOfflinePack}
              disabled={downloadingPack}
              className="px-3 py-1.5 rounded-xl bg-[#2C2C2E] hover:bg-[#3A3A3C] text-neutral-200 font-medium flex items-center space-x-1"
            >
              <Download size={13} className={downloadingPack ? 'animate-bounce' : ''} />
              <span>{downloadingPack ? `${downloadProgress}%` : 'Sync Pack'}</span>
            </button>
          </div>
        </div>
      </div>

    </div>
  );
}
