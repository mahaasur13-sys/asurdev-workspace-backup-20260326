"""amre/grounding.py — ATOM-KARL Grounding Engine"""
from dataclasses import dataclass

@dataclass
class MarketContext:
    price: float
    regime: str
    trend_strength: float
    volatility: float
    volume: float

def check_grounding(state: dict, trajectory) -> dict:
    context = MarketContext(
        price=state.get("current_price", 0),
        regime=state.get("regime", "unknown"),
        trend_strength=state.get("trend_strength", 0.5),
        volatility=state.get("volatility", 0.5),
        volume=state.get("volume", 0),
    )
    issues = []
    score = 1.0

    # Price context check
    if trajectory.direction == "LONG" and trajectory.steps:
        entry_prices = [s.market_state.get("price", context.price) for s in trajectory.steps]
        if entry_prices and max(entry_prices) > context.price * 1.05:
            issues.append("entry_above_current")
            score *= 0.9

    # Volatility regime
    if context.volatility > 0.7 and "astro" in trajectory.metadata.get("primary_signal", ""):
        issues.append("astro_in_high_vol")
        score *= 0.85

    # Trend alignment
    if context.trend_strength > 0.6:
        if trajectory.direction == "NEUTRAL":
            issues.append("neutral_in_trend")
            score *= 0.8

    grounded = score >= 0.8 and len(issues) == 0
    return {"grounded": grounded, "score": round(score, 3), "issues": issues}
