"""amre/__init__.py - ATOM-KARL AMRE Control Loop"""
from .trajectory import (
    MarketState, Trajectory, TrajectoryStep, TrajectoryMetrics,
    market_state_hash, trajectory_from_state, compute_trajectory_metrics,
    trajectory_to_dict, trajectory_from_dict
)
from .similarity import (
    trajectory_distance, is_similar_trajectory, jensen_shannon_divergence,
    estimate_q_star, select_top_k_trajectories, knn_q_star
)
from .reward import (
    compute_trajectory_reward, compute_reward_from_outcome,
    get_default_buffer, get_global_buffer, set_global_buffer,
    RewardCalibrator, CalibrationMetrics,
    FalseCorrelationDetector, CorrelationPenalty,
    DrawdownTracker, DrawdownState,
    get_calibrator, get_dd_tracker, get_reward_diagnostics,
)
from .grounding import validate_with_grounding
from .uncertainty import estimate_uncertainty
from .self_question import SelfQuestioningEngine, SQResult
from .hierarchical_policy import HierarchicalPolicy
from .counterfactual import CounterfactualEngine
from .ensemble_selection import select_ensemble, ensemble_diversity_score, select_ensemble_by_confidence
from .oap_optimizer import OAPOptimizer, OAPConfig, OptimizationStatus, ValidationState, get_oap_optimizer
from .replay_buffer import ReplayBuffer, BufferEntry, get_default_buffer, _select_best_trajectory
from .audit import AuditLog, DecisionRecord, get_audit_log, record_decision, build_decision_record
from .backtest_loop import ContinuousBacktest, BacktestRegime, create_backtest_runner, run_backtest_on_bars
from .karl_integration import (
    process_amre,
    check_delisted_fallback,
    apply_fallback,
    get_karl_diagnostics,
    DelistFallback,
    AMREOutput,
)

AMRE_ENABLED = True
__all__ = [
    "AMRE_ENABLED", "MarketState", "Trajectory", "TrajectoryStep", "TrajectoryMetrics",
    "market_state_hash", "trajectory_from_state", "compute_trajectory_metrics",
    "trajectory_to_dict", "trajectory_from_dict",
    "trajectory_distance", "is_similar_trajectory", "jensen_shannon_divergence",
    "estimate_q_star", "select_top_k_trajectories", "knn_q_star",
    "compute_trajectory_reward", "compute_reward_from_outcome",
    "get_default_buffer", "get_global_buffer", "set_global_buffer",
    "validate_with_grounding", "estimate_uncertainty",
    "SelfQuestioningEngine", "SQResult",
    "HierarchicalPolicy",
    "CounterfactualEngine",
    "select_ensemble", "ensemble_diversity_score", "select_ensemble_by_confidence",
    "OAPOptimizer", "OAPConfig", "OptimizationStatus", "ValidationState",
    "ReplayBuffer", "BufferEntry", "_select_best_trajectory",
    "AuditLog", "DecisionRecord", "get_audit_log", "record_decision",
    "ContinuousBacktest", "BacktestRegime", "create_backtest_runner", "run_backtest_on_bars",
    # KARL-010 Integration
    "process_amre", "check_delisted_fallback", "apply_fallback", "get_karl_diagnostics",
    "DelistFallback", "AMREOutput",
]
