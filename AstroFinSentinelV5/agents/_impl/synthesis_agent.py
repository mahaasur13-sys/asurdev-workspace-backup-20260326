"""AstroFin Sentinel V5 - Synthesis Agent with KARL-AMRE Control Loop"""

import json, os, yaml
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

try:
    from agents.base_agent import AgentResponse, SignalDirection
    _BASE_OK = True
except ImportError:
    _BASE_OK = False

try:
    from agents._impl.amre import (
        AMRE_ENABLED, _ReplayBuffer, TrajectoryStep,
        MarketState, TrajectoryMetrics, Trajectory,
        compute_trajectory_reward, compute_reward_from_outcome,
        estimate_q_star, is_similar_trajectory,
        SelfQuestioningEngine, validate_with_grounding,
        estimate_uncertainty, HierarchicalPolicy,
        CounterfactualEngine, select_ensemble,
        _select_best_trajectory, get_default_buffer,
    )
    _AMRE_AVAILABLE = True
except ImportError as e:
    _AMRE_AVAILABLE = False

MIN_AGENTS_FALLBACK = 2
CATEGORY_WEIGHTS = {
    "astro": 0.22, "fundamental": 0.15, "macro": 0.15,
    "quant": 0.18, "options": 0.12, "sentiment": 0.09,
    "technical": 0.09,
}
AGENT_WEIGHTS = {
    "FundamentalAgent": 0.20, "QuantAgent": 0.20,
    "MacroAgent": 0.15, "OptionsFlowAgent": 0.15,
    "SentimentAgent": 0.10, "TechnicalAgent": 0.10,
    "BullResearcher": 0.05, "BearResearcher": 0.05,
}
MAX_CONFIDENCE = 92; MIN_CONFIDENCE = 30
ASTRO_REDUCTION = 0.30; FUNDAMENTAL_BOOST = 0.18; QUANT_BOOST = 0.12

def _mk_response(agent_name, signal, confidence, reasoning, sources, metadata):
    if _BASE_OK:
        sig_val = signal if isinstance(signal, str) else signal.value if hasattr(signal, "value") else str(signal)
        return AgentResponse(agent_name=agent_name, signal=sig_val, confidence=confidence, reasoning=reasoning, sources=sources or [], metadata=metadata or {})
    return {"agent_name": agent_name, "signal": str(signal), "confidence": confidence, "reasoning": reasoning, "sources": sources or [], "metadata": metadata or {}}

class SynthesisAgent:
    def __init__(self): self.name = "SynthesisAgent"
    async def run(self, state: dict) -> dict:
        all_signals = state.get("all_signals", [])
        thompson_selections = state.get("thompson_selections", {})
        symbol = state.get("symbol", "BTCUSDT")
        current_price = state.get("current_price", 50000)
        timeframe = state.get("timeframe_requested", "SWING")
        session_id = state.get("session_id", "unknown")
        _insufficient = len(all_signals) < MIN_AGENTS_FALLBACK
        if _insufficient:
            reason = f"Fallback: {len(all_signals)}/{MIN_AGENTS_FALLBACK} agents. Signals: {[s.get("agent_name","?") for s in all_signals]}"
            return _mk_response("SynthesisAgent", "NEUTRAL", 30, reason, [], {"symbol": symbol, "timeframe": timeframe, "current_price": current_price, "fallback": True, "amre": {"enabled": False}})
        _cats = _group_by_category(all_signals)
        _conflicts = _detect_conflicts(_cats)
        _dir, _conf, _reason = _synthesize(_cats, _conflicts, symbol)
        _breakdown = _format_breakdown(_cats)
        _amre = _run_amre(state, all_signals, _cats, symbol, current_price, timeframe, session_id)
        return _mk_response("SynthesisAgent", _dir, _conf, _reason, [], {"symbol": symbol, "timeframe": timeframe, "current_price": current_price, "breakdown": _breakdown, "amre": _amre, "thompson_selections": thompson_selections})

def _run_amre(state, all_signals, categories, symbol, price, timeframe, session_id):
    if not (_AMRE_AVAILABLE and AMRE_ENABLED): return {"enabled": False, "reason": "not_available"}
    try:
        _policy = HierarchicalPolicy()
        _counterfactual = CounterfactualEngine()
        _sq_engine = SelfQuestioningEngine()
        _ms = {"symbol": symbol, "price": price, "timeframe": timeframe, "n_signals": len(all_signals), "session_id": session_id, "timestamp": datetime.now().isoformat()}
        _regime = _policy.detect_regime(_ms)
        _ms["regime"] = _regime
        _cf = _counterfactual.check(_ms, all_signals)
        _cf_passed = _cf.get("passed", True) if isinstance(_cf, dict) else True
        _ms["counterfactual"] = _cf
        if len(all_signals) >= 2:
            _ens = select_ensemble(all_signals)
            _ms["ensemble_diversity"] = len(_ens)
            all_signals = _ens
        _traj_r = compute_trajectory_reward(_ms, all_signals)
        _qs = estimate_q_star(_traj_r)
        _ms["trajectory"] = {"reward": _traj_r, "q_star": _qs}
        _sq = _sq_engine.ask(all_signals, _ms)
        _sq_passed = _sq.passed if hasattr(_sq, "passed") else True
        _ms["self_question"] = dict(_sq) if hasattr(_sq, "_asdict") else str(_sq)
        _gr = validate_with_grounding(_ms, all_signals)
        _gr_passed = _gr.get("passed", True) if isinstance(_gr, dict) else True
        _ms["grounding"] = _gr
        _unc = estimate_uncertainty(all_signals)
        _ms["uncertainty"] = _unc
        return {"enabled": True, "regime": _regime, "counterfactual_passed": _cf_passed, "self_question_passed": _sq_passed, "grounding_passed": _gr_passed, "ensemble_diversity": len(all_signals), "q_star": _qs, "uncertainty": _unc, "trajectory_reward": _traj_r, "n_signals_used": len(all_signals)}
    except Exception as e:
        return {"enabled": False, "error": str(e)}

def _group_by_category(signals):
    _cm = {"AstroCouncil": "astro", "BradleyAgent": "astro", "ElectoralAgent": "astro", "TimeWindowAgent": "astro", "GannAgent": "astro", "CycleAgent": "astro", "MuhurtaAgent": "astro", "ElectionAgent": "astro", "FundamentalAgent": "fundamental", "InsiderAgent": "fundamental", "MacroAgent": "macro", "QuantAgent": "quant", "MLPredictorAgent": "quant", "OptionsFlowAgent": "options", "BullResearcher": "sentiment", "BearResearcher": "sentiment", "SentimentAgent": "sentiment", "TechnicalAgent": "technical", "MarketAnalyst": "technical"}
    _cats = {v: [] for v in set(_cm.values())}
    for _s in signals:
        _n = _s.get("agent_name", "?") if isinstance(_s, dict) else getattr(_s, "agent_name", "?")
        _c = _cm.get(_n, "other")
        if _c in _cats: _cats[_c].append(_s)
    return _cats

def _detect_conflicts(cats):
    def _dv(sigs):
        if not sigs: return "NEUTRAL"
        _v = [s.get("signal", "NEUTRAL").upper() if isinstance(s, dict) else getattr(s, "signal", "NEUTRAL").upper() for s in sigs]
        return "LONG" if _v.count("LONG") + _v.count("BUY") > _v.count("SHORT") + _v.count("SELL") else "SHORT" if _v.count("SHORT") + _v.count("SELL") > _v.count("LONG") + _v.count("BUY") else "NEUTRAL"
    _a = _dv(cats.get("astro", [])); _f = _dv(cats.get("fundamental", [])); _q = _dv(cats.get("quant", []))
    if _a != "NEUTRAL" and _f != "NEUTRAL" and _q != "NEUTRAL" and _a != _f:
        return [{"type": "astro_vs_fundamental_quant", "resolution": "reduce_astro"}]
    return []

def _synthesize(cats, conflicts, symbol):
    _eff = dict(CATEGORY_WEIGHTS)
    for _c in conflicts:
        if _c.get("type") == "astro_vs_fundamental_quant":
            _eff["astro"] = _eff.get("astro", 0.22) * (1 - ASTRO_REDUCTION)
            _eff["fundamental"] = _eff.get("fundamental", 0.15) * (1 + FUNDAMENTAL_BOOST)
            _eff["quant"] = _eff.get("quant", 0.18) * (1 + QUANT_BOOST)
    return _vote(cats, _eff)

def _vote(cats, eff):
    _lw = _sw = _nw = 0.0
    for _cat, _sigs in cats.items():
        if not _sigs: continue
        _w = eff.get(_cat, 0.10)
        for _s in _sigs:
            _c = _s.get("confidence", 50) if isinstance(_s, dict) else getattr(_s, "confidence", 50)
            _d = _s.get("signal", "NEUTRAL").upper() if isinstance(_s, dict) else getattr(_s, "signal", "NEUTRAL").upper()
            if _d in ("LONG", "BUY", "STRONG_BUY"): _lw += _c * _w
            elif _d in ("SHORT", "SELL", "STRONG_SELL"): _sw += _c * _w
            else: _nw += _c * _w
    _tot = _lw + _sw + _nw
    if _tot > 0: _lp = _lw / _tot; _sp = _sw / _tot
    else: _lp = _sp = 0.5
    if _lp > 0.55: return "LONG", min(MAX_CONFIDENCE, 50 + int(_lp * 40)), f"Long consensus: {_lp*100:.0f}%"
    elif _sp > 0.55: return "SHORT", min(MAX_CONFIDENCE, 50 + int(_sp * 40)), f"Short consensus: {_sp*100:.0f}%"
    else: return "NEUTRAL", 50, f"No consensus: Long {_lp*100:.0f}% | Short {_sp*100:.0f}%"

def _format_breakdown(cats):
    lines = []
    for _cat, _sigs in cats.items():
        _w = CATEGORY_WEIGHTS.get(_cat, 0.0)
        if not _sigs: lines.append(f"  [{_cat.upper():12s}] NEUTRAL    [..........]   0.0% w={_w:.2f} (no signals)"); continue
        _avg = sum(s.get("confidence", 50) if isinstance(s, dict) else getattr(s, "confidence", 50) for s in _sigs) / len(_sigs)
        _v = [s.get("signal", "NEUTRAL").upper() if isinstance(s, dict) else getattr(s, "signal", "NEUTRAL").upper() for s in _sigs]
        _lv = _v.count("LONG") + _v.count("BUY"); _sv = _v.count("SHORT") + _v.count("SELL")
        _d = "LONG" if _lv > _sv else "SHORT" if _sv > _lv else "NEUTRAL"
        _bar = chr(9608) * int(_avg / 10) + chr(9617) * (10 - int(_avg / 10))
        lines.append(f"  [{_cat.upper():12s}] {_d:12s} [{_bar}] {_avg:5.1f}% w={_w:.2f}")
    return chr(10).join(lines)

async def run_synthesis_agent(state: dict) -> dict:
    agent = SynthesisAgent()
    result = await agent.run(state)
    if hasattr(result, "to_dict"): return result.to_dict()
    return result

CATEGORY_WEIGHTS_AGENTS = AGENT_WEIGHTS
