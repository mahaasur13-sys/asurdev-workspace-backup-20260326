"""amre/hierarchical_policy.py — ATOM-KARL Hierarchical Policy + Regime Detection"""
from dataclasses import dataclass

@dataclass
class PolicyConfig:
    high_vol_threshold: float = 0.7
    trend_threshold: float = 0.6

def detect_regime(state: dict, config: PolicyConfig = None) -> str:
    if config is None:
        config = PolicyConfig()
    vol = state.get("volatility", state.get("atr_pct", 0) / 10)
    trend = state.get("trend_strength", 0.5)
    if vol > config.high_vol_threshold:
        return "high_vol"
    elif trend > config.trend_threshold:
        return "trend"
    else:
        return "range"

class HierarchicalPolicy:
    def __init__(self):
        self.regime = "range"

    def get_action(self, state: dict, signals: list) -> dict:
        self.regime = detect_regime(state)
        if self.regime == "high_vol":
            return {"dominant": "market_dominant", "astro_weight": 0.1, "market_weight": 0.9}
        elif self.regime == "trend":
            return {"dominant": "balanced", "astro_weight": 0.3, "market_weight": 0.7}
        else:
            return {"dominant": "astro_dominant", "astro_weight": 0.5, "market_weight": 0.5}

def dynamic_thresholds(kpi: dict) -> dict:
    base_buy = 0.6
    base_sell = 0.6
    penalty = kpi.get("oos_variance", 0) + kpi.get("uncertainty_mean", 0)
    return {
        "buy": base_buy + 0.2 * penalty,
        "sell": base_sell + 0.2 * penalty,
    }
