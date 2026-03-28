"""amre/__init__.py — ATOM-KARL Adaptive Memory & Reinforcement Learning Engine"""
from .trajectory import Trajectory, TrajectoryStep, TrajectoryMetrics
from .similarity import (
    compute_trajectory_similarity,
    is_similar_regime,
    market_state_hash,
    get_similar_trajectories,
    similarity_cache,
)
from .reward import compute_reward, RewardConfig, RewardResult
from .replay_buffer import ReplayBuffer, DEFAULT_BUFFER
from .self_questioning import SelfQuestioningEngine, SQResult
from .grounding import GroundingEngine, check_grounding, MarketContext
from .uncertainty import (
    UncertaintyEngine,
    DisagreementUncertainty,
    EpisodicUncertainty,
    compute_uncertainty,
)
from .hierarchical_policy import HierarchicalPolicy, detect_regime
from .oap_optimizer import OAPOptimizer, OptimizerConfig
from .counterfactual import CounterfactualEngine, CounterfactualResult
from .ensemble_selection import ensemble_select, ensemble_select_from_buffer

AMRE_ENABLED = True
__all__ = [
    "Trajectory", "TrajectoryStep", "TrajectoryMetrics",
    "compute_trajectory_similarity", "is_similar_regime", "market_state_hash",
    "get_similar_trajectories", "similarity_cache",
    "compute_reward", "RewardConfig", "RewardResult",
    "ReplayBuffer", "DEFAULT_BUFFER",
    "SelfQuestioningEngine", "SQResult",
    "GroundingEngine", "check_grounding", "MarketContext",
    "UncertaintyEngine", "DisagreementUncertainty", "EpisodicUncertainty", "compute_uncertaincy",
    "HierarchicalPolicy", "detect_regime",
    "OAPOptimizer", "OptimizerConfig",
    "CounterfactualEngine", "CounterfactualResult",
    "ensemble_select", "ensemble_select_from_buffer",
]
