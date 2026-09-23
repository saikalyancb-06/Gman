import React, { useState, useEffect } from 'react';
import { 
  Search, MapPin, Clock, Footprints, Filter, 
  Utensils, Hotel, Sparkles, Navigation, Heart, ChevronRight, AlertCircle, Plus 
} from 'lucide-react';
import { apiService } from '../services/api';

export default function NearbyScreen({ cityId = 2, userLocation, onSelectPlace, onAskQuestion }) {
  const [data, setData] = useState(null);
  const [activeCategory, setActiveCategory] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadNearbyData();
  }, [cityId, activeCategory]);

  const loadNearbyData = async () => {
    setLoading(true);
    try {
      const res = await apiService.getNearby(cityId, activeCategory, searchQuery, false, userLocation);
      setData(res);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSearchChange = (e) => {
    const val = e.target.value;
    setSearchQuery(val);
    apiService.getNearby(cityId, activeCategory, val, false, userLocation)
      .then(res => setData(res))
      .catch(console.error);
  };

  const handleToggleBookmark = async (e, poiId) => {
    e.stopPropagation();
    try {
      const res = await apiService.toggleBookmark(poiId);
      setData(prev => {
        if (!prev) return prev;
        const updated = prev.top_attractions.map(p => 
          p.id === poiId ? { ...p, is_bookmarked: res.is_bookmarked } : p
        );
        return { ...prev, top_attractions: updated };
      });
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="space-y-6 pb-24 max-w-md mx-auto animate-fade-in">
      
      {/* Header & Subtitle */}
      <div>
        <span className="text-xs font-semibold text-neutral-400 uppercase tracking-wider">
          {data?.radius_label || 'Within 10 km of you'}
        </span>
        <h1 className="text-3xl font-black tracking-tight text-white mt-0.5">Nearby</h1>
      </div>

      {/* Search Input Bar */}
      <div className="relative">
        <Search size={18} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-neutral-400" />
        <input 
          type="text"
          value={searchQuery}
          onChange={handleSearchChange}
          placeholder="Search temples, parks, food, stays..."
          className="w-full bg-[#1C1C1E] text-sm text-white placeholder-neutral-500 pl-10 pr-4 py-3 rounded-2xl border border-[#2C2C2E] focus:outline-none focus:border-[#F8D348] transition-colors"
        />
      </div>

      {/* Category Pills Filter */}
      <div className="flex space-x-2 overflow-x-auto no-scrollbar pb-1">
        {[
          { name: 'All', slug: 'all' },
          { name: 'Monuments', slug: 'monuments' },
          { name: 'Hidden gems', slug: 'hidden_gems' },
          { name: 'Step-free', slug: 'step_free' },
          { name: 'Nature & Sunsets', slug: 'nature' },
          { name: 'Saved', slug: 'saved' }
        ].map((cat) => (
          <button
            key={cat.slug}
            onClick={() => setActiveCategory(cat.slug)}
            className={'px-4 py-2 rounded-full text-xs font-semibold whitespace-nowrap transition-all ' + (
              activeCategory === cat.slug
                ? 'bg-[#F8D348] text-black shadow-md'
                : 'bg-[#1C1C1E] text-neutral-300 border border-[#2C2C2E] hover:border-neutral-500'
            )}
          >
            {cat.name}
          </button>
        ))}
      </div>

      {/* Top Attractions List */}
      <div className="space-y-3">
        <h3 className="text-lg font-bold text-white tracking-tight px-1 flex items-center justify-between">
          <span>Top attractions</span>
          <span className="text-xs font-normal text-neutral-400">
            {data?.top_attractions?.length || 0} places found
          </span>
        </h3>

        {loading ? (
          <div className="p-8 text-center text-neutral-400 text-sm">Finding nearby places...</div>
        ) : (
          <div className="space-y-3">
            {data?.top_attractions?.map((poi) => (
              <div
                key={poi.id}
                onClick={() => onSelectPlace(poi)}
                className="bg-[#1C1C1E] p-3.5 rounded-2xl border border-[#2C2C2E] hover:border-neutral-600 transition-all flex space-x-3.5 cursor-pointer shadow-sm group relative"
              >
                <div className="w-24 h-24 rounded-xl overflow-hidden bg-neutral-800 shrink-0 relative">
                  <img 
                    src={poi.image_url} 
                    alt={poi.name} 
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                  />
                  {poi.tag_badge && (
                    <span className="absolute top-1.5 left-1.5 px-1.5 py-0.5 rounded text-[9px] font-bold bg-[#F8D348] text-black">
                      {poi.tag_badge}
                    </span>
                  )}
                  <button
                    onClick={(e) => handleToggleBookmark(e, poi.id)}
                    className={'absolute bottom-1.5 right-1.5 p-1.5 rounded-full backdrop-blur transition-all ' + (poi.is_bookmarked ? 'bg-red-500 text-white' : 'bg-black/60 text-neutral-300 hover:text-white')}
                    title="Save bookmark"
                  >
                    <Heart size={13} fill={poi.is_bookmarked ? "white" : "none"} />
                  </button>
                </div>

                <div className="flex-1 min-w-0 flex flex-col justify-between py-0.5">
                  <div>
                    <div className="flex items-center justify-between">
                      <h4 className="font-bold text-white text-sm truncate pr-2">{poi.name}</h4>
                      {poi.tag_badge && (
                        <span className="text-[10px] font-medium text-neutral-400 bg-neutral-800/80 px-2 py-0.5 rounded-full shrink-0">
                          {poi.tag_badge}
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-neutral-300 line-clamp-2 mt-1 leading-snug font-sans">
                      {poi.short_desc}
                    </p>
                  </div>

                  <div className="text-[11px] text-neutral-400 flex items-center space-x-2 pt-1 border-t border-neutral-800/60">
                    <span>{poi.distance_km} km</span>
                    <span>•</span>
                    <span>{poi.travel_time_mins} min {poi.travel_mode || 'auto'}</span>
                    <span>•</span>
                    <span className="text-white font-medium">{poi.entry_fee_inr === 0 ? 'Free' : ('₹' + poi.entry_fee_inr)}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Eat Local Section */}
      <div className="space-y-3 pt-2">
        <div className="flex items-center justify-between px-1">
          <h3 className="text-lg font-bold text-white tracking-tight flex items-center space-x-2">
            <Utensils size={18} className="text-[#F8D348]" />
            <span>Eat local</span>
          </h3>
        </div>

        <div className="space-y-3">
          {data?.eat_local?.map((food) => (
            <div 
              key={food.id}
              onClick={() => onSelectPlace(food)}
              className="bg-[#1C1C1E] p-4 rounded-2xl border border-[#2C2C2E] space-y-2 cursor-pointer hover:border-neutral-600 transition-all"
            >
              <div className="flex items-center justify-between">
                <h4 className="font-bold text-white text-sm">{food.name}</h4>
                <span className="text-[10px] font-semibold text-[#F8D348] bg-[#F8D348]/10 px-2 py-0.5 rounded-full">
                  {food.tag_badge || 'Local special'}
                </span>
              </div>
              <p className="text-xs text-neutral-300 leading-relaxed">
                {food.short_desc}
              </p>
              <div className="text-[11px] text-neutral-400 pt-1 border-t border-neutral-800 flex items-center justify-between">
                <span>{food.full_desc?.split('. ')[1] || 'Local Karnataka Delicacy'}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Stay Nearby Section */}
      <div className="space-y-3 pt-2">
        <div className="flex items-center justify-between px-1">
          <h3 className="text-lg font-bold text-white tracking-tight flex items-center space-x-2">
            <Hotel size={18} className="text-[#F8D348]" />
            <span>Stay nearby</span>
          </h3>
        </div>

        <div className="grid grid-cols-2 gap-3">
          {data?.stay_nearby?.map((hotel) => (
            <div 
              key={hotel.id}
              className="bg-[#1C1C1E] rounded-2xl border border-[#2C2C2E] overflow-hidden group shadow-sm"
            >
              <div className="h-24 w-full relative bg-neutral-800">
                <img 
                  src={hotel.image_url} 
                  alt={hotel.name} 
                  className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                />
              </div>
              <div className="p-3 space-y-1">
                <h4 className="font-bold text-white text-xs truncate">{hotel.name}</h4>
                <div className="flex items-center justify-between text-xs pt-1">
                  <span className="font-semibold text-white">{'₹' + hotel.price_per_night?.toLocaleString()}</span>
                  <span className="text-[#F8D348] text-[11px] font-semibold flex items-center">
                    ★ {hotel.rating}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

    </div>
  );
}
