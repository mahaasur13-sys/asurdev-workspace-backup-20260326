"""amre/oap_optimizer.py — ATOM-KARL OAP Optimizer with KPI-driven control"""
from dataclasses import dataclass, field
from typing import Optional, List
from .trajectory import Trajectory
from .hierarchical_policy import HierarchicalPolicy, detect_regime, dynamic_thresholds

@dataclass
class ValidationStatus:
    REJECTED = "REJECTED"
    ACCEPTED = "ACCEPTED"
    REVIEW = "REVIEW"

@dataclass
class OptimizerConfig:
    entropy_boost_threshold: float = 0.3
    ttc_gain_penalty_threshold: float = 0.0
    oos_stability_threshold: float = 0.5
    exploration_factor: float = 0.1

@dataclass
class KPIRecord:
    timestamp: str
    ttc_gain: float
    entropy: float
    oos_variance: float
    sharpe: float
    oos_stability: float
    uncertainty_mean: float

class OAPOptimizer:
    def __init__(self, config: Optional[OptimizerConfig] = None):
        self.config = config or OptimizerConfig()
        self.policy = HierarchicalPolicy()
        self.kpi_history: List[KPIRecord] = []
        self.thresholds = {"buy": 0.6, "sell": 0.6}

    def get_thresholds(self, kpi: dict) -> dict:
        self.thresholds = dynamic_thresholds(kpi)
        return self.thresholds

    def should_increase_exploration(self, kpi: dict) -> bool:
        return kpi.get("ttc_gain", 0) < self.config.ttc_gain_penalty_threshold

    def should_boost_entropy(self, kpi: dict) -> bool:
        return kpi.get("entropy", 1.0) < self.config.entropy_boost_threshold

    def should_tighten_grounding(self, kpi: dict) -> bool:
        return kpi.get("oos_stability", 1.0) < self.config.oos_stability_threshold

    def apply_kpi_control(self, kpi: dict) -> dict:
        actions = {}
        if self.should_increase_exploration(kpi):
            actions["increase_exploration"] = True
        if self.should_boost_entropy(kpi):
            actions["boost_entropy"] = True
        if self.should_tighten_grounding(kpi):
            actions["tighten_grounding"] = True
        return actions

    def record_kpi(self, kpi: KPIRecord) -> None:
        self.kpi_history.append(kpi)

    def get_regime(self, state: dict) -> str:
        return detect_regime(state, self.policy.regime)

    def get_policy_weights(self, state: dict, signals: list) -> dict:
        return self.policy.get_action(state, signals)
