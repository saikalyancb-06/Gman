import React, { useState, useEffect } from 'react';
import { 
  X, Clock, MapPin, Ticket, ShieldCheck, Footprints, 
  Volume2, Plus, Sparkles, Heart, ThumbsUp, ThumbsDown, 
  Check, FileText, ChevronDown, ChevronUp, AlertCircle 
} from 'lucide-react';
import { apiService } from '../services/api';

export default function PlaceDetailModal({ place, onClose, onAddToPlan, onAskAbout, onBookmarkToggle }) {
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);
  const [feedback, setFeedback] = useState(null);
  const [isSaved, setIsSaved] = useState(place?.is_bookmarked || false);
  const [evidenceData, setEvidenceData] = useState(null);
  const [showEvidence, setShowEvidence] = useState(false);

  useEffect(() => {
    if (place?.id) {
      apiService.getPlaceEvidence(place.id)
        .then(setEvidenceData)
        .catch(console.error);
    }
  }, [place?.id]);

  if (!place) return null;

  const handleAudioPlay = () => {
    if ('speechSynthesis' in window) {
      if (isPlayingAudio) {
        window.speechSynthesis.cancel();
        setIsPlayingAudio(false);
      } else {
        const text = place.name + '. ' + (place.full_desc || place.short_desc) + '. ' + (place.ticket_policy || '');
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = 0.95;
        utterance.onend = () => setIsPlayingAudio(false);
        setIsPlayingAudio(true);
        window.speechSynthesis.speak(utterance);
      }
    }
  };

  const handleFeedback = async (type) => {
    setFeedback(type);
    try {
      if (apiService.submitFeedback) {
        await apiService.submitFeedback(place.id, type);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleBookmark = async () => {
    const nextState = !isSaved;
    setIsSaved(nextState);
    if (onBookmarkToggle) onBookmarkToggle(place.id, nextState);
    try {
      await apiService.toggleBookmark(place.id);
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-black/80 backdrop-blur-sm p-0 sm:p-4 animate-fade-in">
      <div 
        className="bg-[#1C1C1E] text-[#F2F2F7] w-full max-w-lg rounded-t-3xl sm:rounded-3xl max-h-[90vh] overflow-y-auto border border-[#2C2C2E] shadow-2xl relative flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header Image */}
        <div className="relative h-56 w-full bg-neutral-800">
          <img 
            src={place.image_url || "https://images.unsplash.com/photo-1600100397608-f010e42f9b1c?w=600"} 
            alt={place.name} 
            className="w-full h-full object-cover"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-[#1C1C1E] via-transparent to-black/60" />
          
          <div className="absolute top-4 right-4 flex items-center space-x-2">
            <button 
              onClick={handleBookmark}
              className={'p-2 rounded-full backdrop-blur transition-all ' + (isSaved ? 'bg-red-500/80 text-white' : 'bg-black/60 text-white hover:bg-black/90')}
              title={isSaved ? "Saved to favorites" : "Save place"}
            >
              <Heart size={18} fill={isSaved ? "white" : "none"} />
            </button>
            <button 
              onClick={onClose}
              className="p-2 rounded-full bg-black/60 text-white hover:bg-black/90 transition-colors"
            >
              <X size={18} />
            </button>
          </div>

          <div className="absolute bottom-4 left-4 right-4">
            {place.tag_badge && (
              <span className="inline-block px-2.5 py-0.5 rounded-full text-xs font-semibold bg-[#F8D348] text-black mb-2">
                {place.tag_badge}
              </span>
            )}
            <h2 className="text-2xl font-bold tracking-tight text-white">{place.name}</h2>
            <p className="text-sm text-neutral-300 line-clamp-1">{place.short_desc}</p>
          </div>
        </div>

        {/* Content Body */}
        <div className="p-5 space-y-5">
          
          {/* Quick Stats Grid */}
          <div className="grid grid-cols-3 gap-2 text-center text-xs">
            <div className="bg-[#2C2C2E]/60 p-3 rounded-xl border border-neutral-800">
              <span className="text-neutral-400 block text-[10px] uppercase font-medium">Distance</span>
              <span className="font-bold text-white mt-0.5 block">{place.distance_km} km ({place.travel_time_mins || 5} min)</span>
            </div>
            <div className="bg-[#2C2C2E]/60 p-3 rounded-xl border border-neutral-800">
              <span className="text-neutral-400 block text-[10px] uppercase font-medium">Entry Fee</span>
              <span className="font-bold text-[#30D158] mt-0.5 block">{place.entry_fee_inr === 0 ? 'Free' : `₹${place.entry_fee_inr}`}</span>
            </div>
            <div className="bg-[#2C2C2E]/60 p-3 rounded-xl border border-neutral-800">
              <span className="text-neutral-400 block text-[10px] uppercase font-medium">Access</span>
              <span className="font-bold text-white mt-0.5 block">{place.is_step_free ? 'Step-Free' : 'Steps/Rocks'}</span>
            </div>
          </div>

          {/* Description */}
          <div>
            <h4 className="text-xs font-semibold text-neutral-400 uppercase tracking-wider mb-1">Grounded Place Overview</h4>
            <p className="text-sm leading-relaxed text-neutral-200">
              {place.full_desc || place.short_desc}
            </p>
          </div>

          {/* Why GeoGuide Recommends This */}
          <div className="bg-[#242426] p-4 rounded-2xl border border-[#3A3A3C] space-y-2.5">
            <div className="flex items-center space-x-2">
              <Sparkles size={16} className="text-[#F8D348]" />
              <h5 className="text-xs font-bold text-[#F8D348] uppercase tracking-wider">
                Why GeoGuide Recommends This
              </h5>
            </div>

            <div className="space-y-1.5 text-xs text-neutral-300">
              {place.score_reasons && place.score_reasons.length > 0 ? (
                place.score_reasons.map((r, i) => (
                  <div key={i} className="flex items-center space-x-2">
                    <Check size={14} className="text-[#30D158] shrink-0" />
                    <span>{r}</span>
                  </div>
                ))
              ) : (
                <div className="flex items-center space-x-2">
                  <Check size={14} className="text-[#30D158] shrink-0" />
                  <span>Matches your history & architecture profile within budget.</span>
                </div>
              )}
            </div>
          </div>

          {/* EVIDENCE / TRUST DRAWER */}
          <div className="bg-[#18181A] rounded-2xl border border-neutral-800 overflow-hidden">
            <button 
              onClick={() => setShowEvidence(!showEvidence)}
              className="w-full p-3.5 flex items-center justify-between text-xs text-neutral-300 hover:text-white transition-colors"
            >
              <div className="flex items-center space-x-2">
                <FileText size={15} className="text-[#F8D348]" />
                <span className="font-semibold">Evidence & Verification Sources</span>
                <span className="px-1.5 py-0.5 bg-[#30D158]/20 text-[#30D158] text-[10px] rounded font-bold">
                  VERIFIED
                </span>
              </div>
              {showEvidence ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
            </button>

            {showEvidence && evidenceData && (
              <div className="p-4 pt-0 space-y-2 border-t border-neutral-800 text-xs text-neutral-300">
                <p className="text-[11px] text-neutral-400">
                  Every factual statement is backed by official registry sources:
                </p>
                {evidenceData.sources?.map((s, idx) => (
                  <div key={idx} className="bg-neutral-900/60 p-2.5 rounded-xl border border-neutral-800/80 space-y-1">
                    <p className="font-medium text-white">{s.claim}</p>
                    <p className="text-[10px] text-neutral-400">Source: {s.source}</p>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Action Buttons */}
          <div className="flex items-center space-x-3 pt-2">
            <button 
              onClick={() => {
                onAddToPlan(place);
                onClose();
              }}
              className="flex-1 bg-[#F8D348] text-black font-semibold py-3 px-4 rounded-xl flex items-center justify-center space-x-2 hover:bg-[#ffe066] active:scale-[0.98] transition-all"
            >
              <Plus size={18} />
              <span>Add to plan</span>
            </button>

            <button 
              onClick={handleAudioPlay}
              className={'py-3 px-4 rounded-xl flex items-center space-x-2 transition-all ' + (isPlayingAudio ? 'bg-[#F8D348] text-black font-bold' : 'bg-[#2C2C2E] hover:bg-[#3A3A3C] text-white font-medium')}
              title="Listen to audio overview"
            >
              <Volume2 size={18} />
              <span>{isPlayingAudio ? 'Pause' : 'Audio Guide'}</span>
            </button>

            <button 
              onClick={() => {
                onAskAbout('Tell me more about ' + place.name + ' and tips for visiting');
                onClose();
              }}
              className="bg-[#2C2C2E] hover:bg-[#3A3A3C] text-white font-medium py-3 px-3 rounded-xl flex items-center transition-all"
              title="Ask AI about this stop"
            >
              <Sparkles size={18} className="text-[#F8D348]" />
            </button>
          </div>

        </div>
      </div>
    </div>
  );
}
