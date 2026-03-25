"""
AstroFin Sentinel — Technical Feature Vector
============================================
Построение 24-мерного числового вектора признаков из AgentResult.

Структура вектора:
  [0]     price_norm       — цена / ATH (нормализация 0–1)
  [1]     change_24h       — дневное изменение (%)
  [2]     volume_log       — log10(объём), стандартизован
  [3]     volatility       — (high - low) / price
  [4]     rsi_normalized   — RSI / 100 (0–1)
  [5]     trend_up         — one-hot: uptrend = 1
  [6]     trend_down       — one-hot: downtrend = 1
  [7]     trend_strength   — |change_24h| * volume_factor
  [8]     macd_bullish    — one-hot: macd_signal = bullish
  [9]     macd_bearish    — one-hot: macd_signal = bearish
  [10]    sr_distance     — (resistance - support) / price
  [11]    near_support    — (price - support) / price
  [12]    near_resistance — (resistance - price) / price
  [13]    range_position  — где цена в диапазоне support–resistance (0–1)
  [14]    volume_vs_avg   — объём / средний объём
  [15]    bull_prob       — вероятность бычьего сценария
  [16]    bear_prob       — вероятность медвежьего сценария
  [17]    neutral_prob    — вероятность нейтрального сценария
  [18]    scenario_spread — |bull_prob - bear_prob|
  [19]    upside_pct      — (target_bull - price) / price
  [20]    downside_pct    — (price - target_bear) / price
  [21]    direction_enc   — encoded: -1 (bearish), 0 (neutral), +1 (bullish)
  [22]    confidence_enc  — encoded: 0 (LOW), 0.5 (MEDIUM), 1.0 (HIGH)
  [23]    action_enc      — encoded: -1 (SELL), 0 (HOLD), 1 (BUY)

Использование:
  - Weighted voting в Board of Directors
  - Similarity search по историческим паттернам
  - Input для ML-классификатора (LightGBM/XGBoost)
"""

from __future__ import annotations
import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


# ─── Minimal Types (copy from agents.base.base_agent) ───────
# Defined locally to avoid broken import chain in agents/__init__.py

class Confidence(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Action(Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    SKIP = "SKIP"


@dataclass
class RawMarketData:
    symbol: str = ""
    timeframe: str = ""
    price: float = 0.0
    volume_24h: float = 0.0
    change_24h: float = 0.0
    high_24h: float = 0.0
    low_24h: float = 0.0
    rsi: float = 50.0
    macd_signal: str = "neutral"
    trend: str = "neutral"
    support: float = 0.0
    resistance: float = 0.0
    raw_ohlcv: list = field(default_factory=list)
    ath: float = 0.0


@dataclass
class AgentResult:
    agent_id: str = ""
    agent_role: str = ""
    status: str = "success"
    findings: dict = field(default_factory=dict)
    narrative: str = ""
    confidence: Any = None
    action_recommendation: Any = None
    metadata: dict = field(default_factory=dict)
    errors: list = field(default_factory=list)
    knowledge_sources: list = field(default_factory=list)


# ─── Constants ─────────────────────────────────────────────

FEATURE_DIM = 24
FEATURE_NAMES = [
    "price_norm", "change_24h", "volume_log", "volatility",
    "rsi_normalized",
    "trend_up", "trend_down", "trend_strength",
    "macd_bullish", "macd_bearish",
    "sr_distance", "near_support", "near_resistance", "range_position", "volume_vs_avg",
    "bull_prob", "bear_prob", "neutral_prob", "scenario_spread", "upside_pct", "downside_pct",
    "direction_enc", "confidence_enc", "action_enc",
]


# ─── Encoding helpers ──────────────────────────────────────

def _trend_map(t: str) -> int:
    return {"uptrend": 1, "downtrend": -1, "neutral": 0}.get(t.lower(), 0)


def _macd_map(m: str) -> int:
    return {"bullish": 1, "bearish": -1, "neutral": 0}.get(m.lower(), 0)


def _conf_map(c) -> float:
    if isinstance(c, str):
        return {"low": 0.0, "medium": 0.5, "high": 1.0}.get(c.lower(), 0.5)
    if isinstance(c, Confidence):
        return {Confidence.LOW: 0.0, Confidence.MEDIUM: 0.5, Confidence.HIGH: 1.0}.get(c, 0.5)
    return 0.5


def _action_map(a) -> float:
    if isinstance(a, str):
        return {"sell": -1.0, "hold": 0.0, "buy": 1.0, "skip": 0.0}.get(a.lower(), 0.0)
    if isinstance(a, Action):
        return {Action.SELL: -1.0, Action.HOLD: 0.0, Action.BUY: 1.0, Action.SKIP: 0.0}.get(a, 0.0)
    return 0.0


# ─── Dataclass ─────────────────────────────────────────────

@dataclass
class TechnicalFeatureVector:
    """
    24-мерный вектор признаков технического анализа.
    """
    vector: list[float]
    magnitude: float
    source_agent: str
    symbol: str
    timeframe: str

    def to_list(self) -> list[float]:
        return self.vector

    def to_dict(self) -> dict[str, float]:
        return dict(zip(FEATURE_NAMES, self.vector))

    @classmethod
    def from_result(cls, result: AgentResult) -> "TechnicalFeatureVector":
        return build_from_agent_result(result)


# ─── Core Builder ─────────────────────────────────────────

def build_from_agent_result(result: AgentResult) -> TechnicalFeatureVector:
    """
    Построение 24-мерного вектора из AgentResult market_analyst.
    """
    f = result.findings
    market: Optional[RawMarketData] = result.metadata.get("raw_market")

    if market is None:
        market = _reconstruct_market_from_findings(f)

    symbol = f.get("symbol", result.agent_id)
    timeframe = f.get("timeframe", "unknown")
    vec = [0.0] * FEATURE_DIM

    # [0] price_norm
    price = market.price or f.get("price", 0.0)
    ath = getattr(market, 'ath', None) or f.get("ath", 0.0)
    if not ath or ath == 0:
        ath = price * 1.5
    vec[0] = price / ath if ath > 0 else 0.5

    # [1] change_24h
    vec[1] = (market.change_24h or f.get("change_24h", 0.0)) / 100.0

    # [2] volume_log
    vol = market.volume_24h or f.get("volume_24h", 0.0)
    vec[2] = math.log10(vol + 1) / 10.0 if vol > 0 else 0.0

    # [3] volatility
    high = market.high_24h or f.get("high_24h", price)
    low = market.low_24h or f.get("low_24h", price)
    vec[3] = (high - low) / price if price > 0 else 0.0

    # [4] rsi_normalized
    rsi_val = getattr(market, 'rsi', None)
    rsi = rsi_val if rsi_val else f.get("rsi", 50.0)
    vec[4] = rsi / 100.0

    # [5-6] trend one-hot
    trend = _trend_map(market.trend or f.get("trend", "neutral"))
    vec[5] = 1.0 if trend == 1 else 0.0
    vec[6] = 1.0 if trend == -1 else 0.0

    # [7] trend_strength
    vec[7] = abs(vec[1]) * (1.0 + vec[2])

    # [8-9] MACD one-hot
    macd = _macd_map(market.macd_signal or f.get("macd_signal", "neutral"))
    vec[8] = 1.0 if macd == 1 else 0.0
    vec[9] = 1.0 if macd == -1 else 0.0

    # [10-13] Support/Resistance
    support = market.support or f.get("support", price * 0.95)
    resistance = market.resistance or f.get("resistance", price * 1.05)
    sr_range = resistance - support
    vec[10] = sr_range / price if price > 0 else 0.05
    vec[11] = (price - support) / price if price > 0 else 0.05
    vec[12] = (resistance - price) / price if price > 0 else 0.05
    vec[13] = vec[11] / (vec[11] + vec[12] + 1e-9)

    # [14] volume_vs_avg
    avg_vol = f.get("avg_volume_24h", vol)
    vec[14] = vol / avg_vol if avg_vol and avg_vol > 0 else 1.0

    # [15-20] Scenarios
    scenarios = f.get("scenarios", {})
    bull = scenarios.get("bull", {})
    bear = scenarios.get("bear", {})
    neutral = scenarios.get("neutral", {})

    bull_prob = bull.get("probability", 0.33)
    bear_prob = bear.get("probability", 0.33)
    neutral_prob = neutral.get("probability", 0.34)

    vec[15] = bull_prob
    vec[16] = bear_prob
    vec[17] = neutral_prob
    vec[18] = abs(bull_prob - bear_prob)

    target_bull = bull.get("target", resistance)
    target_bear = bear.get("target", support)
    vec[19] = (target_bull - price) / price if price > 0 else 0.05
    vec[20] = (price - target_bear) / price if price > 0 else 0.05

    # [21] direction_enc
    direction_str = f.get("direction", "neutral")
    vec[21] = {"bullish": 1.0, "bearish": -1.0, "neutral": 0.0}.get(direction_str.lower(), 0.0)

    # [22] confidence_enc
    vec[22] = _conf_map(result.confidence)

    # [23] action_enc
    vec[23] = _action_map(result.action_recommendation)

    magnitude = math.sqrt(sum(v * v for v in vec))

    return TechnicalFeatureVector(
        vector=vec,
        magnitude=magnitude,
        source_agent=result.agent_id,
        symbol=symbol,
        timeframe=timeframe,
    )


def _reconstruct_market_from_findings(f: dict) -> RawMarketData:
    """Fallback: создаём RawMarketData из flat findings dict."""
    return RawMarketData(
        symbol=f.get("symbol", "UNKNOWN"),
        timeframe=f.get("timeframe", "1h"),
        price=f.get("price", 0.0),
        volume_24h=f.get("volume_24h", 0.0),
        change_24h=f.get("change_24h", 0.0),
        high_24h=f.get("high_24h", f.get("price", 0.0)),
        low_24h=f.get("low_24h", f.get("price", 0.0)),
        rsi=f.get("rsi", 50.0),
        macd_signal=f.get("macd_signal", "neutral"),
        trend=f.get("trend", "neutral"),
        support=f.get("support", 0.0),
        resistance=f.get("resistance", 0.0),
        ath=f.get("ath", 0.0),
    )


# ─── Similarity ─────────────────────────────────────────────

def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Косинусная близость между двумя векторами."""
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(v * v for v in a))
    mag_b = math.sqrt(sum(v * v for v in b))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


def weighted_combine(
    vectors: list[TechnicalFeatureVector],
    weights: list[float]
) -> list[float]:
    """
    Взвешенная сумма векторов (Board of Directors voting).
    weights нормализуются автоматически.
    """
    if not vectors:
        return [0.0] * FEATURE_DIM
    total_w = sum(weights)
    norm_weights = [w / total_w for w in weights]
    result = [0.0] * FEATURE_DIM
    for vec, weight in zip(vectors, norm_weights):
        for i, v in enumerate(vec.vector):
            result[i] += v * weight
    return result


# ─── CLI Test ──────────────────────────────────────────────

if __name__ == "__main__":
    mock_result = AgentResult(
        agent_id="market_analyst",
        agent_role="market_analyst",
        status="success",
        findings={
            "symbol": "BTC",
            "timeframe": "1h",
            "price": 67430.0,
            "volume_24h": 28_500_000_000.0,
            "change_24h": 2.34,
            "high_24h": 68100.0,
            "low_24h": 65800.0,
            "rsi": 62.5,
            "macd_signal": "bullish",
            "trend": "uptrend",
            "support": 65800.0,
            "resistance": 68500.0,
            "ath": 73750.0,
            "scenarios": {
                "bull": {"probability": 0.40, "target": 72000.0},
                "bear": {"probability": 0.20, "target": 64000.0},
                "neutral": {"probability": 0.40},
            },
            "direction": "bullish",
        },
        confidence=Confidence.MEDIUM,
        action_recommendation=Action.HOLD,
        metadata={},
    )

    fv = build_from_agent_result(mock_result)

    print(f"Vector dimension: {len(fv.vector)} (expected {FEATURE_DIM})")
    print(f"Magnitude: {fv.magnitude:.4f}")
    print()
    for name, val in fv.to_dict().items():
        print(f"  {name:22s}: {val:+.4f}")
