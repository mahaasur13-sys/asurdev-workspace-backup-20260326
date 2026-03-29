"""agents/karl_synthesis.py — KARL-013: SynthesisAgent + AMRE Integration
Оборачивает SynthesisAgent в AMRE-контур:
  DecisionRecord → OAP update → Backtest sample → Sync audit

Использование:
    from agents.karl_synthesis import KARLSynthesisAgent
    result = await karl_agent.run(state)
"""
import uuid
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from agents.base_agent import AgentResponse, SignalDirection
from agents.synthesis_agent import SynthesisAgent
from agents._impl.amre import (
    # Uncertainty + Grounding
    estimate_uncertainty,
    validate_with_grounding,
    # Audit
    build_decision_record,
    get_audit_log,
    # Backtest
    ContinuousBacktest,
    BacktestRegime,
    create_backtest_runner,
    run_backtest_on_bars,
    # OAP
    get_oap_optimizer,
    OAPOptimizer,
    # Reward
    compute_trajectory_reward,
    RewardCalibrator,
    DrawdownTracker,
    get_calibrator,
    get_dd_tracker,
    get_reward_diagnostics,
    # AMRE output
    process_amre,
    get_karl_diagnostics,
    check_delisted_fallback,
    AMREOutput,
    # Self-questioning
    SelfQuestioningEngine,
    # Delisted fallback
    DelistFallback,
)
# ATOM-019: PostgreSQL integration
try:
    from db import (
        is_postgres_available,
        DecisionRecordRepository,
        AgentSignalRepository,
        AstroPositionRepository,
        get_all_stats,
    )
    PG_AVAILABLE = is_postgres_available()
except Exception:
    PG_AVAILABLE = False
    DecisionRecordRepository = None
    AgentSignalRepository = None
    AstroPositionRepository = None
from agents._impl.amre.trajectory import MarketState, market_state_hash, trajectory_from_state


# ─── KARL Synthesis Agent ───────────────────────────────────────────────────────

class KARLSynthesisAgent:
    """
    SynthesisAgent + Full AMRE/KARL Control Loop.
    
    Adds to SynthesisAgent:
    - DecisionRecord на каждое решение
    - OAPOptimizer.update_from_decision() после синтеза
    - ContinuousBacktest sample
    - Self-questioning engine (optional)
    - Periodic sync_with_audit()
    """

    def __init__(
        self,
        sync_interval: int = 10,
        enable_self_question: bool = False,
        enable_backtest: bool = True,
        backtest_horizon: int = 5,
    ):
        self.base_agent = SynthesisAgent()
        self.sync_interval = sync_interval  # Recalibrate every N decisions
        self.enable_self_question = enable_self_question
        self.enable_backtest = enable_backtest
        
        # Sub-systems
        self.decision_counter = 0
        self.self_questioner = SelfQuestioningEngine() if enable_self_question else None
        self.backtest = create_backtest_runner(horizon=backtest_horizon) if enable_backtest else None
        self.oap = get_oap_optimizer()
        self.calibrator = get_calibrator()
        self.dd_tracker = get_dd_tracker()

    async def run(self, state: dict) -> Dict[str, Any]:
        """
        Run synthesis + AMRE post-processing.
        
        Returns dict with:
          - synthesis_result: AgentResponse.to_dict()
          - amre_output: AMREOutput dataclass
          - decision_record: DecisionRecord.to_dict()
          - karl_diagnostics: get_karl_diagnostics()
        """
        # ── Step 1: Pre-AMRE checks ────────────────────────────────────────────
        symbol = state.get("symbol", "BTCUSDT")
        
        # Delisted ticker fallback
        delist_fb = check_delisted_fallback(symbol)
        if delist_fb:
            state = {**state, "symbol": delist_fb.fallback_symbol}

        # Build market state for audit
        price = state.get("current_price", 50000)
        regime = state.get("regime", "NORMAL")
        ms = MarketState(
            symbol=symbol,
            price=price,
            timeframe=state.get("timeframe_requested", "SWING"),
            n_signals=len(state.get("all_signals", [])),
            session_id=state.get("session_id", str(uuid.uuid4())[:8]),
            timestamp=datetime.now(timezone.utc).isoformat(),
            regime=regime,
        )
        ms_hash = market_state_hash(ms)

        # ── Step 2: Run base synthesis ─────────────────────────────────────────
        synthesis_result = await self.base_agent.run(state)
        
        # Convert to dict for consistent handling
        if isinstance(synthesis_result, AgentResponse):
            synth_dict = synthesis_result.to_dict()
        else:
            synth_dict = synthesis_result

        signal = synth_dict.get("signal", "NEUTRAL")
        confidence = synth_dict.get("confidence", 50)
        all_signals = state.get("all_signals", [])
        
        # ── Step 3: Self-questioning (optional) ───────────────────────────────
        if self.self_questioner:
            sq_result = self.self_questioner.ask(all_signals, state)
            if sq_result.confidence_adjustment != 0:
                confidence = max(30, min(92, confidence + sq_result.confidence_adjustment))
                synth_dict["reasoning"] = (
                    f"[SelfQ] {sq_result.question} → {sq_result.answer}. "
                    f"{synth_dict.get('reasoning', '')}"
                )

        # ── Step 4: Uncertainty + Grounding ──────────────────────────────────
        uncertainty = estimate_uncertainty(all_signals)
        grounding = validate_with_grounding(state, all_signals)

        if grounding.get("confidence_adjustment", 0) != 0:
            confidence = max(30, min(92, confidence + grounding["confidence_adjustment"]))

        # ── Step 5: Reward estimation ─────────────────────────────────────────
        reward = self._estimate_reward(state, all_signals, confidence, signal)

        # ── Step 6: Build state hash for record ──────────────────────────────
        state_hash = self._compute_state_hash(state, signal, confidence, regime)

        # ── Step 7: Build DecisionRecord ─────────────────────────────────────
        # Ensemble for record (s can be AgentResponse or dict)
        def _sig_get(s, key, default=None):
            if hasattr(s, key):
                return getattr(s, key)
            if isinstance(s, dict):
                return s.get(key, default)
            return default

        # Collect ensemble info from signals
        selected_ensemble = [
            {
                "name": _sig_get(s, "agent_name", "unknown"),
                "signal": _sig_get(s, "signal", "NEUTRAL"),
                "confidence": _sig_get(s, "confidence", 50),
                "weight": 0.0,
                "q_value": 0.0,
            }
            for s in all_signals
        ]

        # Trajectories (simplified — just current decision)
        top_trajectories = [
            {
                "id": f"traj_{self.decision_counter}",
                "depth": 0,
                "action": signal,
                "q_value": reward,
                "advantage": reward - 0.5,
                "uncertainty": uncertainty.get("total", 0.5),
                "confidence": confidence,
                "policy": "karl_synthesis",
            }
        ]

        # KPI snapshot from OAP
        oap_state = self.oap.kpi_state
        kpi_snapshot = {
            "oos_fail_rate": oap_state.oos_fail_rate,
            "entropy": oap_state.entropy_avg,
            "uncertainty": uncertainty.get("total", 0.5),
            "avg_confidence": confidence,
            "sharpe_ratio": 0.0,
            "win_rate": 0.0,
            "regime_stability": 1.0,
            "exploration_rate": oap_state.current_exploration_rate,
            "ttc_depth": oap_state.current_ttc_depth,
            "grounding_strength": oap_state.current_grounding_strength,
        }

        confidence_adjustments = []
        if grounding.get("confidence_adjustment", 0) != 0:
            confidence_adjustments.append(f"grounding:{grounding['confidence_adjustment']}")
        if self.self_questioner:
            sq_adj = self.self_questioner.ask(all_signals, state).confidence_adjustment
            if sq_adj != 0:
                confidence_adjustments.append(f"self_q:{sq_adj}")

        record = build_decision_record(
            decision_id=f"KARL_{self.decision_counter:04d}_{symbol}",
            session_id=state.get("session_id", "unknown"),
            symbol=symbol,
            price=price,
            timeframe=state.get("timeframe_requested", "SWING"),
            regime=regime,
            state_hash=state_hash,
            top_trajectories=top_trajectories,
            selected_ensemble=selected_ensemble,
            q_values=[reward],
            q_star=reward,
            uncertainty=uncertainty,
            confidence_raw=synth_dict.get("confidence", 50),
            confidence_final=confidence,
            confidence_adjustments=confidence_adjustments,
            final_action=signal,
            position_pct=synth_dict.get("metadata", {}).get("position_size", 0.02),
            kpi_snapshot=kpi_snapshot,
            metadata={
                "delist_fallback": delist_fb.reason if delist_fb else None,
                "uncertainty_aleatoric": uncertainty.get("aleatoric", 0.0),
                "uncertainty_epistemic": uncertainty.get("epistemic", 0.0),
                "grounding_passed": grounding.get("passed", True),
                "grounding_issues": grounding.get("issues", [])[:3],
            },
        )

        # ── Step 8: Record to audit log ──────────────────────────────────────
        audit_log = get_audit_log()
        audit_log.record(record)

        # ATOM-019: Save to PostgreSQL if available
        if PG_AVAILABLE and DecisionRecordRepository:
            try:
                DecisionRecordRepository.save(record.to_dict())
                # Save individual agent signals
                for s in all_signals:
                    if AgentSignalRepository:
                        AgentSignalRepository.save(
                            session_id=state.get("session_id", "unknown"),
                            agent_name=_sig_get(s, "agent_name", "unknown"),
                            signal=_sig_get(s, "signal", "NEUTRAL"),
                            confidence=_sig_get(s, "confidence", 50),
                            reasoning=_sig_get(s, "reasoning", "")[:500],
                            metadata=_sig_get(s, "metadata", {}),
                        )
            except Exception as e:
                print(f"[KARL] PostgreSQL save failed: {e}")

        # ── Step 8: Update OAP optimizer ─────────────────────────────────────────
        self.oap.sync_with_audit()

        # ── Step 10: Update calibrator + drawdown tracker ─────────────────────
        self.calibrator.add_sample(confidence, reward)
        self.dd_tracker.add_trade(reward)

        # ── Step 11: Backtest sample (if enabled) ──────────────────────────────
        if self.backtest and self.enable_backtest:
            try:
                self.backtest.add_sample(
                    state=ms,
                    decision=record,
                    reward=reward,
                    signals=all_signals,
                )
            except Exception:
                pass  # Non-fatal

        # ── Step 12: Periodic recalibration ───────────────────────────────────
        self.decision_counter += 1
        if self.decision_counter % self.sync_interval == 0:
            self._sync_and_recalibrate()

        # ── Step 13: Return enriched result ───────────────────────────────────
        synth_dict["confidence"] = confidence
        synth_dict["metadata"] = {
            **(synth_dict.get("metadata", {})),
            "karl_enabled": True,
            "decision_id": record.decision_id,
            "uncertainty": uncertainty,
            "grounding": grounding,
            "amre_passed": grounding.get("passed", True),
            "delist_fallback": delist_fb.reason if delist_fb else None,
            "kpi_snapshot": kpi_snapshot,
        }

        return {
            "synthesis_result": synth_dict,
            "amre_output": {
                "reward_estimate": round(reward, 4),
                "uncertainty": uncertainty,
                "grounding_passed": grounding.get("passed", True),
                "confidence_final": confidence,
            },
            "decision_record": record.to_dict(),
            "karl_diagnostics": get_karl_diagnostics(),
        }

    def _estimate_reward(
        self, state: dict, signals: list, confidence: int, signal: str
    ) -> float:
        """Estimate reward for current decision."""
        ms = MarketState(
            symbol=state.get("symbol", "BTC"),
            price=state.get("current_price", 50000),
            timeframe=state.get("timeframe_requested", "SWING"),
            n_signals=len(signals),
            session_id=state.get("session_id", ""),
            timestamp=datetime.now(timezone.utc).isoformat(),
            regime=state.get("regime", "NORMAL"),
            confidence=confidence,
        )
        return compute_trajectory_reward(ms, signals)

    def _compute_state_hash(
        self, state: dict, signal: str, confidence: int, regime: str
    ) -> str:
        """Compute reproducible state hash."""
        data = (
            f"{state.get('symbol', '')}:"
            f"{state.get('current_price', 0)}:"
            f"{state.get('timeframe_requested', 'SWING')}:"
            f"{len(state.get('all_signals', []))}:"
            f"{regime}:"
            f"{signal}:"
            f"{confidence}"
        )
        return hashlib.md5(data.encode()).hexdigest()[:12]

    def _sync_and_recalibrate(self):
        """Periodic self-assessment — calls sync_with_audit to update KPIs."""
        self.oap.sync_with_audit()

    def sync_with_audit(self) -> Dict[str, Any]:
        """
        Manual trigger: sync_with_audit().
        Periodic self-assessment — analyze drift, adjust KPIs.
        """
        audit_log = get_audit_log()
        drift = audit_log.analyze_drift()
        karl_diag = get_karl_diagnostics()

        # Force recalibration if drifting
        if drift.get("status") == "degrading":
            self._sync_and_recalibrate()

        return {
            "drift_analysis": drift,
            "karl_diagnostics": karl_diag,
            "calibrator_diagnostics": get_reward_diagnostics(),
            "decision_count": self.decision_counter,
        }

    def run_backtest_on_historical(
        self, bars: list, symbol: str = "BTCUSDT"
    ) -> Dict[str, Any]:
        """
        Run continuous backtest on historical bars.
        Returns backtest results.
        """
        if not self.backtest:
            return {"error": "backtest not enabled"}
        
        results = run_backtest_on_bars(
            agent_run_fn=lambda state: self.run(state),
            bars=bars,
            symbol=symbol,
        )
        return results

    def get_status(self) -> Dict[str, Any]:
        """Get KARL system status."""
        return {
            "decision_counter": self.decision_counter,
            "sync_interval": self.sync_interval,
            "self_question_enabled": self.enable_self_question,
            "backtest_enabled": self.enable_backtest,
            "karl_diagnostics": get_karl_diagnostics(),
            "drift_status": get_audit_log().analyze_drift(),
        }


# ─── Global singleton ─────────────────────────────────────────────────────────

_KARL_AGENT: Optional[ KARLSynthesisAgent] = None

def get_karl_agent() -> KARLSynthesisAgent:
    global _KARL_AGENT
    if _KARL_AGENT is None:
        _KARL_AGENT = KARLSynthesisAgent()
    return _KARL_AGENT
