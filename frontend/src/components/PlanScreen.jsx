import React, { useState, useEffect } from 'react';
import { 
  Clock, DollarSign, Footprints, Leaf, Sparkles, 
  CheckCircle2, AlertTriangle, MessageSquare, RotateCcw, 
  ChevronRight, Car, Compass, Trash2, Share2, Play,
  Send, ArrowDownUp, ShieldCheck
} from 'lucide-react';
import { apiService } from '../services/api';

export default function PlanScreen({ cityId = 1, userLocation, onSelectPlace, onAskQuestion }) {
  const [durationType, setDurationType] = useState('full_day');
  const [optimizationFilter, setOptimizationFilter] = useState('balanced');
  const [naturalInstruction, setNaturalInstruction] = useState('');
  const [plan, setPlan] = useState(null);
  const [previousPlan, setPreviousPlan] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showPlanDiff, setShowPlanDiff] = useState(false);
  const [showLiveSignal, setShowLiveSignal] = useState(true);
  const [simulatedSignal, setSimulatedSignal] = useState(null);

  useEffect(() => {
    loadPlan();
  }, [cityId, durationType, optimizationFilter]);

  const loadPlan = async (instruction = null) => {
    setLoading(true);
    try {
      const res = await apiService.getPlan(durationType, optimizationFilter, cityId, 1, instruction);
      if (plan && plan.items) {
        setPreviousPlan(plan);
        setShowPlanDiff(true);
      }
      setPlan(res);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleNaturalSubmit = (e) => {
    e.preventDefault();
    if (!naturalInstruction.trim()) return;
    loadPlan(naturalInstruction);
    setNaturalInstruction('');
  };

  const handleRestoreOriginal = () => {
    setShowLiveSignal(false);
    setSimulatedSignal(null);
    setOptimizationFilter('balanced');
    setShowPlanDiff(false);
    apiService.simulateSignal('reset');
  };

  const handleSimulateSignal = async (type) => {
    try {
      const res = await apiService.simulateSignal(type);
      setSimulatedSignal(res);
      setShowLiveSignal(true);
      if (type === 'vittala_entry_passed') {
        setOptimizationFilter('less_walking');
      } else if (type === 'heavy_rain') {
        setOptimizationFilter('cheaper');
      } else if (type === 'sunset') {
        setOptimizationFilter('balanced');
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleRemoveStop = (idx) => {
    if (!plan) return;
    const updated = plan.items.filter((_, i) => i !== idx);
    setPlan({
      ...plan,
      items: updated,
      banner_update: `Stop removed. Total stops: ${updated.length}`
    });
  };

  const handleSharePlan = () => {
    const summary = `My GeoGuide Plan: ${plan?.schedule_header}\nStops: ${plan?.items?.map(i => i.title).join(' -> ')}`;
    if (navigator.share) {
      navigator.share({ title: 'GeoGuide Plan', text: summary });
    } else {
      navigator.clipboard.writeText(summary);
      alert('Plan copied to clipboard!');
    }
  };

  return (
    <div className="space-y-6 pb-24 max-w-md mx-auto animate-fade-in">
      
      {/* Header & Subtitle */}
      <div className="flex items-start justify-between">
        <div>
          <span className="text-xs font-semibold text-neutral-400 uppercase tracking-wider">
            {plan?.schedule_header || 'Day Schedule • Active Plan'}
          </span>
          <h1 className="text-3xl font-black tracking-tight text-white mt-0.5">Your plan</h1>
        </div>

        <button
          onClick={handleSharePlan}
          className="p-2.5 rounded-xl bg-[#1C1C1E] border border-[#2C2C2E] text-neutral-300 hover:text-white transition-colors"
          title="Share / Export Plan"
        >
          <Share2 size={16} />
        </button>
      </div>

      {/* Natural Language Replanner Input */}
      <form onSubmit={handleNaturalSubmit} className="relative">
        <input 
          type="text"
          value={naturalInstruction}
          onChange={(e) => setNaturalInstruction(e.target.value)}
          placeholder="E.g. 'Less walking and keep it cheap' or '2 hours'"
          className="w-full bg-[#1C1C1E] text-white placeholder-neutral-500 text-xs px-4 py-3 rounded-2xl border border-neutral-700/60 focus:outline-none focus:border-[#F8D348] pr-10"
        />
        <button 
          type="submit"
          className="absolute right-2 top-2 p-1.5 bg-[#F8D348] text-black rounded-xl hover:bg-[#E5C13D] transition-colors"
        >
          <Send size={14} />
        </button>
      </form>

      {/* Duration Selectors (2 hours, 4 hours, Full day) */}
      <div className="grid grid-cols-3 gap-2">
        {[
          { label: '2 hours', val: '2_hours' },
          { label: '4 hours', val: '4_hours' },
          { label: 'Full day', val: 'full_day' }
        ].map((item) => (
          <button
            key={item.val}
            onClick={() => { setDurationType(item.val); setShowPlanDiff(false); }}
            className={'py-2.5 px-3 rounded-2xl text-xs font-semibold flex items-center justify-center space-x-1.5 transition-all ' + (
              durationType === item.val
                ? 'bg-[#F8D348] text-black shadow-md'
                : 'bg-[#1C1C1E] text-neutral-300 border border-[#2C2C2E] hover:border-neutral-500'
            )}
          >
            <Clock size={14} />
            <span>{item.label}</span>
          </button>
        ))}
      </div>

      {/* KPI Summary Cards Grid */}
      <div className="grid grid-cols-2 gap-2.5">
        <div className="bg-[#1C1C1E] p-3.5 rounded-2xl border border-[#2C2C2E]">
          <p className="text-lg font-black text-white">{plan?.metrics?.total_time || '3 h 45 min'}</p>
          <p className="text-xs text-neutral-400 mt-0.5">Total time</p>
        </div>
        <div className="bg-[#1C1C1E] p-3.5 rounded-2xl border border-[#2C2C2E]">
          <p className="text-lg font-black text-white">{'₹' + (plan?.metrics?.cost_inr || 0)}</p>
          <p className="text-xs text-neutral-400 mt-0.5">Estimated cost</p>
        </div>
        <div className="bg-[#1C1C1E] p-3.5 rounded-2xl border border-[#2C2C2E]">
          <p className="text-lg font-black text-white">{(plan?.metrics?.walking_km || 1.8) + ' km'}</p>
          <p className="text-xs text-neutral-400 mt-0.5">On foot</p>
        </div>
        <div className="bg-[#1C1C1E] p-3.5 rounded-2xl border border-[#2C2C2E]">
          <p className="text-lg font-black text-white">{(plan?.metrics?.carbon_kg || 0.12) + ' kg'}</p>
          <p className="text-xs text-neutral-400 mt-0.5">Carbon (CO₂e)</p>
        </div>
      </div>

      {/* "Re-plan for" Filter Buttons */}
      <div className="space-y-2">
        <h3 className="text-xs font-bold text-neutral-400 uppercase tracking-wider px-1">
          Re-plan for
        </h3>
        <div className="grid grid-cols-2 gap-2">
          {[
            { label: 'Balanced', val: 'balanced' },
            { label: 'Cheaper', val: 'cheaper' },
            { label: 'Greener', val: 'greener' },
            { label: 'Less walking', val: 'less_walking' },
            { label: 'More History', val: 'more_history' },
            { label: 'More Food', val: 'more_food' }
          ].map((item) => (
            <button
              key={item.val}
              onClick={() => { setOptimizationFilter(item.val); setShowPlanDiff(false); }}
              className={'py-2 px-3 rounded-xl text-xs font-medium transition-all text-center ' + (
                optimizationFilter === item.val
                  ? 'bg-[#2C2C2E] border-2 border-[#F8D348] text-white font-semibold'
                  : 'bg-[#1C1C1E] text-neutral-300 border border-[#2C2C2E] hover:border-neutral-600'
              )}
            >
              {item.label}
            </button>
          ))}
        </div>
      </div>

      {/* PLAN DIFF MODAL / BANNER (Signature Feature) */}
      {showPlanDiff && previousPlan && (
        <div className="bg-gradient-to-b from-[#1C1C1E] to-[#252528] rounded-2xl p-4 border border-[#F8D348]/40 space-y-3 animate-fade-in">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2 text-[#F8D348] text-xs font-bold uppercase tracking-wider">
              <ArrowDownUp size={16} />
              <span>Itinerary Optimization Diff</span>
            </div>
            <button 
              onClick={() => setShowPlanDiff(false)}
              className="text-neutral-400 hover:text-white text-xs"
            >
              Dismiss
            </button>
          </div>

          <div className="grid grid-cols-2 gap-2 text-xs bg-black/40 p-3 rounded-xl border border-neutral-800">
            <div>
              <p className="text-[10px] text-neutral-500 uppercase">Previous Plan</p>
              <p className="text-neutral-300 font-medium">{previousPlan.metrics?.walking_km} km walk</p>
              <p className="text-neutral-400 text-[11px]">₹{previousPlan.metrics?.cost_inr} cost</p>
            </div>
            <div className="border-l border-neutral-800 pl-3">
              <p className="text-[10px] text-[#F8D348] uppercase">Optimized Plan</p>
              <p className="text-white font-bold">{plan?.metrics?.walking_km} km walk</p>
              <p className="text-[#30D158] font-bold text-[11px]">₹{plan?.metrics?.cost_inr} cost</p>
            </div>
          </div>
          <p className="text-[11px] text-neutral-300">
            {plan?.filter_description}
          </p>
        </div>
      )}

      {/* Live Signal Simulation Card */}
      {showLiveSignal && (
        <div className="bg-[#2A2312] border border-[#F8D348]/40 rounded-2xl p-4 space-y-3">
          <div className="flex items-start justify-between">
            <div className="flex items-center space-x-2 text-[#F8D348]">
              <Sparkles size={16} />
              <span className="text-xs font-bold uppercase tracking-wider">
                {simulatedSignal?.title || 'Live Context Engine Signal'}
              </span>
            </div>
            <button
              onClick={handleRestoreOriginal}
              className="text-xs text-neutral-400 hover:text-white flex items-center space-x-1"
            >
              <RotateCcw size={12} />
              <span>Reset</span>
            </button>
          </div>

          <p className="text-xs text-neutral-200 leading-relaxed font-sans">
            {simulatedSignal?.message || 'GeoGuide dynamically optimized stops considering daylight, travel distance, and entry fees.'}
          </p>

          <div className="flex items-center space-x-2 pt-1">
            <button
              onClick={() => handleSimulateSignal('vittala_entry_passed')}
              className="px-2.5 py-1.5 rounded-lg bg-[#3A3219] hover:bg-[#4E4322] text-[#F8D348] text-[10px] font-semibold border border-[#F8D348]/20"
            >
              Simulate Closure
            </button>
            <button
              onClick={() => handleSimulateSignal('heavy_rain')}
              className="px-2.5 py-1.5 rounded-lg bg-[#3A3219] hover:bg-[#4E4322] text-[#F8D348] text-[10px] font-semibold border border-[#F8D348]/20"
            >
              Simulate Rain
            </button>
            <button
              onClick={() => handleSimulateSignal('sunset')}
              className="px-2.5 py-1.5 rounded-lg bg-[#3A3219] hover:bg-[#4E4322] text-[#F8D348] text-[10px] font-semibold border border-[#F8D348]/20"
            >
              Simulate Sunset
            </button>
          </div>
        </div>
      )}

      {/* Schedule Timeline Items */}
      <div className="space-y-3 pt-2">
        <h3 className="text-xs font-bold text-neutral-400 uppercase tracking-wider px-1">
          Optimized Schedule Timeline
        </h3>

        {loading ? (
          <div className="py-8 text-center text-xs text-neutral-400">
            Solving mathematical constraints for itinerary...
          </div>
        ) : (
          <div className="space-y-3">
            {plan?.items?.map((item, idx) => (
              <div 
                key={idx}
                className="bg-[#1C1C1E] border border-[#2C2C2E] rounded-2xl p-4 hover:border-neutral-600 transition-all space-y-3"
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-center space-x-2">
                    <span className="w-6 h-6 rounded-full bg-[#F8D348] text-black font-bold text-xs flex items-center justify-center">
                      {item.stop_order}
                    </span>
                    <div>
                      <h4 className="text-sm font-bold text-white">{item.title}</h4>
                      <p className="text-[11px] text-neutral-400 font-mono">
                        {item.time} {item.end_time ? `— ${item.end_time}` : ''} • {item.duration}
                      </p>
                    </div>
                  </div>
                  <button 
                    onClick={() => handleRemoveStop(idx)}
                    className="text-neutral-500 hover:text-red-400 p-1"
                    title="Remove stop"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>

                <p className="text-xs text-neutral-300 font-sans">
                  {item.note}
                </p>

                <div className="flex items-center justify-between text-[11px] text-neutral-400 pt-2 border-t border-neutral-800">
                  <div className="flex items-center space-x-2">
                    <span className="bg-[#2C2C2E] px-2 py-0.5 rounded text-neutral-300 font-medium">
                      {item.travel_mode}
                    </span>
                    <span>{item.carbon}</span>
                  </div>
                  <span className="text-[#30D158] font-bold">
                    {item.cost}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Left out on purpose transparency note */}
      {plan?.left_out_on_purpose && (
        <div className="bg-[#18181A] p-3 rounded-xl border border-neutral-800 text-xs text-neutral-400 space-y-1">
          <p className="font-semibold text-neutral-300">Left out on purpose</p>
          <p className="text-[11px] leading-relaxed">
            {plan.left_out_on_purpose}
          </p>
        </div>
      )}

    </div>
  );
}
