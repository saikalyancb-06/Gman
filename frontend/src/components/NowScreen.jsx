import React, { useState } from 'react';
import { 
  Volume2, Share2, Sun, CloudSun, AlertTriangle, 
  Clock, Calendar, ShieldCheck, ChevronRight, Sparkles,
  MapPin, CheckCircle2, Info, Compass, Zap, ArrowRight, Eye
} from 'lucide-react';

export default function NowScreen({ data, onSelectPlace, onTabChange, onAskQuestion, onSimulateCondition }) {
  const [ttsPlaying, setTtsPlaying] = useState(false);

  if (!data) {
    return (
      <div className="p-6 flex items-center justify-center min-h-[60vh] text-neutral-400">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#F8D348] mr-3"></div>
        Loading grounded place context...
      </div>
    );
  }

  const handleSpeech = () => {
    if ('speechSynthesis' in window) {
      if (ttsPlaying) {
        window.speechSynthesis.cancel();
        setTtsPlaying(false);
      } else {
        const text = (data.grounded_briefing?.title || 'Place Briefing') + '. ' + (data.grounded_briefing?.text || '');
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = 0.95;
        utterance.onend = () => setTtsPlaying(false);
        setTtsPlaying(true);
        window.speechSynthesis.speak(utterance);
      }
    }
  };

  const copilot = data.copilot_next_action;

  return (
    <div className="space-y-6 pb-24 max-w-md mx-auto animate-fade-in">
      
      {/* Top Bar Location & Status */}
      <div className="flex items-center justify-between text-xs text-neutral-400 pt-1">
        <div className="flex items-center space-x-1.5 bg-[#2C2C2E]/60 px-3 py-1 rounded-full border border-neutral-700/40">
          <span className="w-2 h-2 rounded-full bg-[#30D158] animate-pulse" />
          <span className="text-neutral-200 font-medium">Located · {data.location?.accuracy || '12m accuracy'}</span>
        </div>
        <div className="flex items-center space-x-2">
          <button 
            onClick={handleSpeech}
            className={'p-2 rounded-full transition-colors ' + (ttsPlaying ? 'bg-[#F8D348] text-black' : 'bg-[#2C2C2E]/70 text-neutral-300 hover:text-white')}
            title="Listen to place briefing"
          >
            <Volume2 size={16} />
          </button>
          <button 
            onClick={() => {
              if (navigator.share) {
                navigator.share({ title: 'GeoGuide Hampi', text: data.grounded_briefing?.text, url: window.location.href });
              }
            }}
            className="p-2 rounded-full bg-[#2C2C2E]/70 text-neutral-300 hover:text-white transition-colors"
          >
            <Share2 size={16} />
          </button>
        </div>
      </div>

      {/* Hero Header with Background Gradient */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-b from-[#252528] to-[#1C1C1E] border border-[#2C2C2E] p-6 text-white shadow-xl">
        <div className="absolute -right-8 -top-8 w-40 h-40 bg-[#F8D348]/10 rounded-full blur-3xl pointer-events-none" />
        
        <p className="text-sm text-neutral-400 font-medium">Good morning, {data.user_name || 'Aarav'}</p>
        <h1 className="text-4xl font-black tracking-tight text-white mt-1">
          {data.location?.city || 'Hampi'}
        </h1>
        <p className="text-xs text-neutral-400 mt-1 flex items-center space-x-1">
          <span>{data.location?.state}, {data.location?.country}</span>
          <span>•</span>
          <span>{data.location?.datetime_label || 'Mon, 31 Aug, 2026 • 10:56 IST'}</span>
        </p>

        {/* Weather and Daylight Metrics Card */}
        <div className="mt-5 bg-[#141416]/80 backdrop-blur rounded-2xl p-4 border border-neutral-800/80 space-y-4">
          <div className="flex items-center justify-between border-b border-neutral-800 pb-3">
            <div>
              <div className="text-3xl font-bold tracking-tight text-white">
                {data.weather?.temp_c}°C
              </div>
              <div className="text-xs text-neutral-400">
                Feels like {data.weather?.feels_like_c}°
              </div>
            </div>
            <div className="text-right">
              <div className="text-sm font-semibold text-neutral-200 flex items-center justify-end space-x-1">
                <CloudSun size={18} className="text-[#F8D348]" />
                <span>{data.weather?.condition}</span>
              </div>
              <div className="text-xs text-neutral-400 mt-0.5">
                Humidity {data.weather?.humidity_pct}%
              </div>
            </div>
          </div>

          {/* Sunrise / Sunset / Daylight metrics */}
          <div className="grid grid-cols-3 gap-2 text-center text-xs">
            <div className="bg-neutral-900/60 p-2 rounded-xl border border-neutral-800/50">
              <p className="text-neutral-400 text-[10px]">Sunrise</p>
              <p className="font-semibold text-neutral-200 mt-0.5">{data.weather?.sunrise || '06:14'}</p>
            </div>
            <div className="bg-neutral-900/60 p-2 rounded-xl border border-neutral-800/50">
              <p className="text-neutral-400 text-[10px]">Sunset</p>
              <p className="font-semibold text-neutral-200 mt-0.5">{data.weather?.sunset || '18:41'}</p>
            </div>
            <div className="bg-neutral-900/60 p-2 rounded-xl border border-neutral-800/50">
              <p className="text-neutral-400 text-[10px]">Daylight</p>
              <p className="font-semibold text-[#F8D348] mt-0.5">{data.weather?.daylight_left || '7h 45 left'}</p>
            </div>
          </div>

          {/* Season Guidance Note */}
          <div className="bg-[#232014] p-3 rounded-xl border border-[#4A3E16]/40 text-xs space-y-1">
            <p className="font-medium text-[#F8D348]">{data.weather?.season_summary}</p>
            <p className="text-neutral-300 leading-relaxed text-[11px]">
              {data.weather?.advice}
            </p>
          </div>
        </div>
      </div>

      {/* PROACTIVE LIVE COPILOT CARD */}
      {copilot && (
        <div className="bg-gradient-to-r from-[#201D13] to-[#1C1C1E] rounded-3xl p-5 border border-[#F8D348]/40 shadow-xl space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Zap size={18} className="text-[#F8D348]" />
              <span className="text-xs font-bold uppercase tracking-wider text-[#F8D348]">
                GeoGuide Copilot • Next Action
              </span>
            </div>
            <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${copilot.urgency === 'HIGH' ? 'bg-red-500/20 text-red-400 border border-red-500/30' : 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30'}`}>
              {copilot.urgency} Urgency
            </span>
          </div>

          <div>
            <h4 className="text-lg font-bold text-white">{copilot.poi_name}</h4>
            <p className="text-xs text-neutral-300 mt-1 leading-relaxed">{copilot.reason}</p>
          </div>

          <div className="space-y-1 bg-black/30 p-2.5 rounded-xl border border-neutral-800 text-[11px]">
            {copilot.why_it_fits?.map((reason, i) => (
              <div key={i} className="flex items-center space-x-1.5 text-neutral-300">
                <CheckCircle2 size={12} className="text-[#F8D348] flex-shrink-0" />
                <span>{reason}</span>
              </div>
            ))}
          </div>

          <div className="flex items-center space-x-2 pt-1">
            <button 
              onClick={() => onTabChange('plan')}
              className="flex-1 py-2.5 px-4 bg-[#F8D348] hover:bg-[#E5C13D] text-black font-semibold text-xs rounded-xl flex items-center justify-center space-x-1.5 transition-colors"
            >
              <span>Add to My Plan</span>
              <ArrowRight size={14} />
            </button>
            <button 
              onClick={() => onAskQuestion(`Why do you recommend ${copilot.poi_name}?`)}
              className="py-2.5 px-4 bg-[#2C2C2E] hover:bg-[#3A3A3C] text-neutral-200 text-xs font-medium rounded-xl transition-colors"
            >
              Why?
            </button>
          </div>
        </div>
      )}

      {/* Grounded Place Briefing ("What is special here") */}
      <div className="bg-[#1C1C1E] rounded-3xl p-5 border border-[#2C2C2E] shadow-md space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Sparkles size={18} className="text-[#F8D348]" />
            <h3 className="text-lg font-bold text-white tracking-tight">
              {data.grounded_briefing?.title || 'What is special here'}
            </h3>
          </div>
          <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-[#30D158]/10 text-[#30D158] border border-[#30D158]/20">
            <ShieldCheck size={12} />
            <span>Verified Source</span>
          </span>
        </div>

        <p className="text-sm text-neutral-300 leading-relaxed font-sans">
          {data.grounded_briefing?.text}
        </p>

        <div className="pt-2 border-t border-neutral-800/80 flex items-center justify-between text-xs text-neutral-400">
          <span className="truncate max-w-[240px] text-[11px]">
            Source: {data.grounded_briefing?.source}
          </span>
          <button 
            onClick={() => onAskQuestion('Tell me about the history and significance of this monument')}
            className="text-[#F8D348] hover:underline flex items-center space-x-1 text-xs font-medium"
          >
            <span>Ask more</span>
            <ChevronRight size={14} />
          </button>
        </div>
      </div>

      {/* Real-time Advisories ("What matters today") */}
      <div className="space-y-3">
        <h3 className="text-xs font-bold uppercase tracking-wider text-neutral-400 px-1">
          What matters today
        </h3>
        
        <div className="space-y-2.5">
          {data.what_matters_today?.map((item, idx) => {
            const isWarning = item.severity === 'warning';
            const isInfo = item.severity === 'info';
            const isEvent = item.severity === 'event';

            return (
              <div 
                key={idx}
                className={`p-4 rounded-2xl border flex items-start space-x-3 transition-all ${
                  isWarning 
                    ? 'bg-[#2A1818]/60 border-[#FF453A]/40 text-neutral-200'
                    : isEvent 
                    ? 'bg-[#1C1F2A]/60 border-[#0A84FF]/40 text-neutral-200'
                    : 'bg-[#222017]/60 border-[#F8D348]/30 text-neutral-200'
                }`}
              >
                <div className="mt-0.5 flex-shrink-0">
                  {isWarning && <AlertTriangle size={18} className="text-[#FF453A]" />}
                  {isEvent && <Calendar size={18} className="text-[#0A84FF]" />}
                  {isInfo && <Clock size={18} className="text-[#F8D348]" />}
                </div>
                <div className="flex-1 space-y-1">
                  <div className="flex items-center justify-between">
                    <h4 className="text-sm font-semibold text-white">{item.title}</h4>
                  </div>
                  <p className="text-xs text-neutral-300 leading-relaxed font-sans">
                    {item.description}
                  </p>
                  {item.detour_advice && (
                    <p className="text-[11px] font-medium text-[#F8D348] pt-1">
                      💡 Detour advice: {item.detour_advice}
                    </p>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* "Do not miss" highlights */}
      <div className="space-y-3 pt-2">
        <div className="flex items-center justify-between px-1">
          <h3 className="text-xs font-bold uppercase tracking-wider text-neutral-400">
            Do not miss
          </h3>
          <button 
            onClick={() => onTabChange('nearby')}
            className="text-xs text-[#F8D348] hover:underline flex items-center space-x-1"
          >
            <span>See all nearby</span>
            <ChevronRight size={14} />
          </button>
        </div>

        <div className="grid grid-cols-2 gap-3">
          {data.do_not_miss?.map((poi) => (
            <div 
              key={poi.id}
              onClick={() => onSelectPlace(poi)}
              className="bg-[#1C1C1E] border border-[#2C2C2E] rounded-2xl overflow-hidden hover:border-[#F8D348]/50 transition-all cursor-pointer group flex flex-col justify-between"
            >
              <div className="relative h-28 w-full bg-neutral-900 overflow-hidden">
                <img 
                  src={poi.image_url || 'https://images.unsplash.com/photo-1589182373726-e4f658ab50f0?w=600'} 
                  alt={poi.name} 
                  className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                />
                <span className="absolute top-2 left-2 bg-black/60 backdrop-blur text-[10px] font-medium px-2 py-0.5 rounded-full text-white">
                  {poi.tag_badge || 'Highlight'}
                </span>
              </div>
              <div className="p-3 space-y-1">
                <h4 className="text-xs font-bold text-white group-hover:text-[#F8D348] line-clamp-1">
                  {poi.name}
                </h4>
                <p className="text-[10px] text-neutral-400 line-clamp-2 leading-tight">
                  {poi.short_desc}
                </p>
                <div className="flex items-center justify-between text-[10px] text-neutral-400 pt-1">
                  <span>{poi.distance_km} km</span>
                  <span className="text-[#30D158] font-medium">
                    {poi.entry_fee_inr === 0 ? 'Free' : `₹${poi.entry_fee_inr}`}
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
