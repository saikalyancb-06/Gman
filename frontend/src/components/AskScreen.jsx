import React, { useState, useEffect } from 'react';
import { 
  Mic, MicOff, Send, Volume2, ShieldCheck, Sparkles, 
  ExternalLink, Globe, RotateCcw, Check, Trash2, Camera,
  FileText, ArrowRight, Zap, Database
} from 'lucide-react';
import { apiService } from '../services/api';

export default function AskScreen({ cityId = 1, cityName = 'Hampi', initialQuery, language = 'en', onLanguageChange, onSelectPlace, userLocation = null, onLocationUpdate = null }) {
  const [query, setQuery] = useState(initialQuery || '');
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [listening, setListening] = useState(false);
  const [playingAudio, setPlayingAudio] = useState(null);
  const [showCameraScanner, setShowCameraScanner] = useState(false);
  const [scannedResult, setScannedResult] = useState(null);
  const [packStatus, setPackStatus] = useState(null);

  const suggestedQuestions = cityName === 'Hampi' ? [
    "What can I actually see before sunset today?",
    "Do I need one ticket or many?",
    "How should I dress for the temples?",
    "Are coracle boat rides operating today?",
    "Which places in Hampi are step-free?",
    "Tell me about the Vijayanagara Empire"
  ] : [
    "Do I need one ticket for Lalbagh and palaces?",
    "Which places in Bengaluru are step-free?",
    "What are the iconic masale dose spots?",
    "What is open before sunset today?"
  ];

  useEffect(() => {
    // Reset conversation on destination change, leaving it empty for user query
    setMessages([]);

    // Preload / inspect knowledge pack
    apiService.getKnowledgePackStatus(cityId)
      .then(st => setPackStatus(st))
      .catch(() => {});
  }, [cityId, cityName]);


  useEffect(() => {
    if (initialQuery) {
      handleAsk(initialQuery);
    }
  }, [initialQuery]);

  const handleAsk = async (textToAsk) => {
    const q = textToAsk || query;
    if (!q.trim()) return;

    const userMsg = { type: 'user', text: q };
    setMessages(prev => [...prev, userMsg]);
    setQuery('');
    setLoading(true);

    let activeLocation = userLocation;
    // If asking a proximity query and userLocation hasn't been set yet, attempt a quick geolocation check
    if (!activeLocation && /(near me|nearby|around me|closest)/i.test(q) && navigator.geolocation) {
      try {
        const pos = await new Promise((resolve, reject) => {
          navigator.geolocation.getCurrentPosition(resolve, reject, { timeout: 2000, maximumAge: 60000 });
        });
        if (pos && pos.coords) {
          activeLocation = { lat: pos.coords.latitude, lng: pos.coords.longitude };
          if (onLocationUpdate) onLocationUpdate(activeLocation);
        }
      } catch (e) {
        // Permission denied or timed out; will seamlessly fall back to destination coordinates
      }
    }

    try {
      const res = await apiService.askQuery(q, language, cityId, activeLocation);
      const botMsg = {
        type: 'assistant',
        text: res.answer,
        source: res.source,
        source_tag: res.source_tag,
        verified: res.verified,
        evidence: res.evidence_snippets
      };
      setMessages(prev => [...prev, botMsg]);
    } catch (err) {
      setMessages(prev => [...prev, {
        type: 'assistant',
        text: 'Sorry, I could not retrieve grounded knowledge at this moment.',
        source: 'Error fallback'
      }]);
    } finally {
      setLoading(false);
    }
  };

  const handleVoiceInput = () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert('Speech recognition is not supported in this browser. Please use text input.');
      return;
    }

    if (listening) {
      setListening(false);
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = language === 'kn' ? 'kn-IN' : (language === 'hi' ? 'hi-IN' : 'en-IN');
    recognition.interimResults = false;

    recognition.onstart = () => setListening(true);
    recognition.onend = () => setListening(false);
    recognition.onerror = () => setListening(false);
    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      setQuery(transcript);
      handleAsk(transcript);
    };

    recognition.start();
  };

  const handleTTS = (text, idx) => {
    if ('speechSynthesis' in window) {
      if (playingAudio === idx) {
        window.speechSynthesis.cancel();
        setPlayingAudio(null);
      } else {
        window.speechSynthesis.cancel();
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.lang = language === 'kn' ? 'kn-IN' : (language === 'hi' ? 'hi-IN' : 'en-IN');
        utterance.rate = 0.95;
        utterance.onend = () => setPlayingAudio(null);
        setPlayingAudio(idx);
        window.speechSynthesis.speak(utterance);
      }
    }
  };

  const handleSimulatedCameraScan = async (landmarkHint) => {
    setLoading(true);
    try {
      const res = await apiService.identifyPlace(landmarkHint, cityId);
      setScannedResult(res);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-5 pb-24 max-w-md mx-auto animate-fade-in flex flex-col min-h-[80vh]">
      
      {/* Header & Language Switcher */}
      <div className="flex items-center justify-between">
        <div>
          <span className="text-xs font-semibold text-neutral-400 uppercase tracking-wider">
            Grounded Knowledge Assistant
          </span>
          <h1 className="text-3xl font-black tracking-tight text-white mt-0.5">Ask GeoGuide</h1>
        </div>

        <div className="flex items-center space-x-2">
          {/* Camera Scan Button */}
          <button 
            onClick={() => setShowCameraScanner(!showCameraScanner)}
            className="p-2 rounded-xl bg-[#2C2C2E] border border-neutral-700 text-[#F8D348] hover:bg-[#3A3A3C] transition-colors"
            title="Scan monument with Camera"
          >
            <Camera size={16} />
          </button>

          {/* Language Selector */}
          <div className="bg-[#1C1C1E] border border-[#2C2C2E] rounded-xl p-1 flex items-center space-x-1">
            {[
              { code: 'en', label: 'EN' },
              { code: 'kn', label: 'ಕನ್ನಡ' },
              { code: 'hi', label: 'हिंदी' }
            ].map(l => (
              <button
                key={l.code}
                onClick={() => onLanguageChange(l.code)}
                className={`px-2 py-1 rounded-lg text-xs font-semibold transition-all ${
                  language === l.code ? 'bg-[#F8D348] text-black shadow-sm' : 'text-neutral-400 hover:text-white'
                }`}
              >
                {l.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* GeoContext Knowledge Pack Preloaded Status */}
      {packStatus && packStatus.is_cached && (
        <div className="flex items-center justify-between px-3 py-1.5 bg-[#1C1C1E] border border-[#30D158]/30 rounded-xl text-[11px] text-neutral-300">
          <div className="flex items-center space-x-2">
            <span className="flex h-2 w-2 relative">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#30D158] opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-[#30D158]"></span>
            </span>
            <span className="font-semibold text-white">GeoContext Pack Loaded</span>
            <span className="text-neutral-400">• {packStatus.destination_name} ({packStatus.poi_count} POIs, {packStatus.kb_fact_count} Verified Facts)</span>
          </div>
          <span className="text-[10px] text-[#30D158] font-mono font-medium">Fast Pack-First</span>
        </div>
      )}

      {/* CAMERA SCANNER MODAL / DRAWER */}
      {showCameraScanner && (
        <div className="bg-gradient-to-b from-[#201E15] to-[#1C1C1E] p-4 rounded-3xl border border-[#F8D348]/40 space-y-3 animate-fade-in">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2 text-[#F8D348]">
              <Camera size={18} />
              <h4 className="text-sm font-bold">Scan This Place (Vision AI)</h4>
            </div>
            <button 
              onClick={() => { setShowCameraScanner(false); setScannedResult(null); }}
              className="text-xs text-neutral-400 hover:text-white"
            >
              Close
            </button>
          </div>

          <p className="text-xs text-neutral-300">
            Point your lens at any temple, stone carving, or monolith to identify it and retrieve verified ASI history:
          </p>

          <div className="grid grid-cols-2 gap-2">
            {[
              { label: 'Stone Chariot', hint: 'chariot' },
              { label: 'Underground Shiva', hint: 'shiva' },
              { label: 'Lotus Mahal', hint: 'lotus' },
              { label: 'Sasivekalu Ganesha', hint: 'ganesha' }
            ].map((mon) => (
              <button
                key={mon.hint}
                onClick={() => handleSimulatedCameraScan(mon.hint)}
                className="py-2 px-3 bg-[#2C2C2E] hover:bg-[#3A3A3C] text-xs font-semibold text-neutral-200 rounded-xl border border-neutral-700 transition-colors text-left"
              >
                📸 Scan {mon.label}
              </button>
            ))}
          </div>

          {scannedResult && (
            <div className="bg-black/50 p-3.5 rounded-2xl border border-[#F8D348]/40 space-y-2 mt-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-white">{scannedResult.name}</span>
                <span className="px-2 py-0.5 bg-[#30D158]/20 text-[#30D158] text-[10px] font-bold rounded-full">
                  {Math.round(scannedResult.confidence * 100)}% Confidence
                </span>
              </div>
              <p className="text-xs text-neutral-300 leading-relaxed font-sans">
                {scannedResult.historical_context}
              </p>
              <div className="flex items-center justify-between text-[11px] text-neutral-400 pt-1 border-t border-neutral-800">
                <span>Timings: {scannedResult.open_timings}</span>
                <span className="text-[#30D158] font-bold">{scannedResult.entry_fee}</span>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Suggested Questions Carousel */}
      <div className="space-y-1.5">
        <span className="text-[11px] font-medium text-neutral-400 px-1">Suggested for {cityName}:</span>
        <div className="flex space-x-2 overflow-x-auto no-scrollbar pb-1">
          {suggestedQuestions.map((q, idx) => (
            <button
              key={idx}
              onClick={() => handleAsk(q)}
              className="whitespace-nowrap px-3 py-1.5 rounded-full bg-[#1C1C1E] hover:bg-[#2C2C2E] text-xs text-neutral-300 border border-[#2C2C2E] transition-all flex-shrink-0"
            >
              {q}
            </button>
          ))}
        </div>
      </div>

      {/* Chat Messages Container */}
      <div className="flex-1 space-y-3 overflow-y-auto max-h-[50vh] pr-1">
        {messages.length === 0 && (
          <div className="p-5 rounded-2xl bg-[#1C1C1E] border border-neutral-800 text-center space-y-2 my-auto">
            <p className="text-sm font-semibold text-white">Ask anything about {cityName}</p>
            <p className="text-xs text-neutral-400">
              Answers are dynamically grounded on verified knowledge packs, official schedules, and live APIs. No canned responses.
            </p>
          </div>
        )}
        {messages.map((msg, idx) => {

          const isUser = msg.type === 'user';
          return (
            <div 
              key={idx}
              className={`flex flex-col ${isUser ? 'items-end' : 'items-start'} space-y-1`}
            >
              <div 
                className={`max-w-[90%] rounded-2xl p-4 text-xs leading-relaxed font-sans ${
                  isUser 
                    ? 'bg-[#F8D348] text-black font-medium' 
                    : 'bg-[#1C1C1E] text-neutral-200 border border-[#2C2C2E] shadow-md space-y-2.5'
                }`}
              >
                <div className="text-sm font-sans space-y-1.5 whitespace-pre-line">
                  {msg.text.split('\n').map((line, lIdx) => {
                    const linkMatch = line.match(/\[([^\]]+)\]\((https:\/\/www\.google\.com\/maps[^\)]+)\)/);
                    if (linkMatch) {
                      const prefix = line.substring(0, linkMatch.index);
                      const linkText = linkMatch[1];
                      const linkHref = linkMatch[2];
                      const suffix = line.substring(linkMatch.index + linkMatch[0].length);
                      return (
                        <p key={lIdx}>
                          {prefix}
                          <a 
                            href={linkHref} 
                            target="_blank" 
                            rel="noopener noreferrer" 
                            className="inline-flex items-center space-x-1 text-[#F8D348] hover:underline font-semibold bg-[#2C2C2E] px-2 py-0.5 rounded text-xs ml-1"
                          >
                            <span>{linkText}</span>
                            <ExternalLink size={12} className="inline ml-1" />
                          </a>
                          {suffix}
                        </p>
                      );
                    }
                    return <p key={lIdx}>{line}</p>;
                  })}
                </div>
                
                {!isUser && (
                  <div className="pt-2 border-t border-neutral-800/80 flex items-center justify-between text-[10px] text-neutral-400">
                    <div className="flex items-center space-x-1.5">
                      <ShieldCheck size={12} className="text-[#30D158]" />
                      <span className="truncate max-w-[200px]">{msg.source}</span>
                    </div>

                    <button 
                      onClick={() => handleTTS(msg.text, idx)}
                      className={`p-1 rounded-md transition-colors ${playingAudio === idx ? 'text-[#F8D348]' : 'text-neutral-400 hover:text-white'}`}
                      title="Read aloud"
                    >
                      <Volume2 size={14} />
                    </button>
                  </div>
                )}
              </div>
            </div>
          );
        })}

        {loading && (
          <div className="flex items-center space-x-2 text-xs text-neutral-400 p-2">
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-[#F8D348]"></div>
            <span>Grounding verified answer with RAG & ASI records...</span>
          </div>
        )}
      </div>

      {/* Input Form Bar with Mic & Send */}
      <div className="sticky bottom-0 bg-[#121214] pt-2 pb-1">
        <form onSubmit={(e) => { e.preventDefault(); handleAsk(); }} className="flex items-center space-x-2">
          <div className="relative flex-1">
            <input 
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={`Ask anything about ${cityName || 'this destination'}...`}
              className="w-full bg-[#1C1C1E] text-sm text-white placeholder-neutral-500 pl-4 pr-10 py-3.5 rounded-2xl border border-[#2C2C2E] focus:outline-none focus:border-[#F8D348] transition-colors"
            />
            <button
              type="button"
              onClick={handleVoiceInput}
              className={`absolute right-3 top-1/2 -translate-y-1/2 p-1.5 rounded-full transition-colors ${
                listening ? 'bg-red-500 text-white animate-pulse' : 'text-neutral-400 hover:text-white'
              }`}
              title="Voice Speech-to-Text"
            >
              {listening ? <MicOff size={16} /> : <Mic size={16} />}
            </button>
          </div>

          <button
            type="submit"
            disabled={!query.trim() || loading}
            className="p-3.5 bg-[#F8D348] hover:bg-[#ffe066] disabled:opacity-40 text-black rounded-2xl font-bold transition-all"
          >
            <Send size={18} />
          </button>
        </form>
      </div>

    </div>
  );
}
