"""
agents._impl.types — Unified types for AstroFin Sentinel v5.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum


class Signal(str, Enum):
    STRONG_BUY = "STRONG_BUY"
    BUY = "BUY"
    NEUTRAL = "NEUTRAL"
    HOLD = "HOLD"
    SELL = "SELL"
    STRONG_SELL = "STRONG_SELL"
    
    @property
    def score(self) -> float:
        """Map signal to numeric score for weighted calculation."""
        scores = {
            "STRONG_BUY": 100,
            "BUY": 75,
            "NEUTRAL": 50,
            "HOLD": 50,
            "SELL": 25,
            "STRONG_SELL": 0,
        }
        return scores.get(self.value, 50)


@dataclass
class AgentResponse:
    """Standard agent response."""
    agent_name: str
    signal: str
    confidence: int
    summary: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class TradingSignal:
    """Final trading signal from weighted agent responses."""
    symbol: str
    signal: Signal
    confidence: int
    entry: float
    stop_loss: float
    take_profit: float
    risk_reward: float
    agents: List[AgentResponse]
    summary: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    @staticmethod
    def _normalize_conf(conf) -> int:
        """Normalize confidence to 0-100 int scale.
        Handles both 0-1 floats (e.g. 0.75) and 0-100 floats/ints (e.g. 75 or 47.5).
        """
        if isinstance(conf, float):
            if conf >= 1:
                return int(round(conf))
            return int(round(conf * 100))
        return int(conf)

    def to_dict(self) -> Dict:
        return {
            "symbol": self.symbol,
            "signal": self.signal.value,
            "confidence": self.confidence,
            "entry": self.entry,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "risk_reward": self.risk_reward,
            "summary": self.summary,
            "agents": [a.to_dict() for a in self.agents],
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_agents(
        cls,
        symbol: str,
        responses: List[AgentResponse],
        entry_price: float,
        weights: Optional[Dict[str, float]] = None,
        risk_pct: float = 0.02,
    ) -> "TradingSignal":
        """
        Гибридное взвешивание сигналов от агентов.
        weights = {agent_name: weight}, сумма должна = 1.0
        """
        # Guard: empty responses
        if not responses:
            entry = entry_price
            stop = entry * (1 - risk_pct)
            target = entry * (1 + risk_pct * 2)
            return cls(
                symbol=symbol,
                signal=Signal.NEUTRAL,
                confidence=0,
                entry=round(entry, 2),
                stop_loss=round(stop, 2),
                take_profit=round(target, 2),
                risk_reward=1.0,
                agents=[],
                summary="NEUTRAL (no agents)",
            )

        default_weights = {
            "Fundamental": 0.2041,
            "Macro": 0.1531,
            "Quant": 0.2041,
            "OptionsFlow": 0.1531,
            "Sentiment": 0.0918,
            "Technical": 0.0918,
            "BullResearcher": 0.0510,
            "BearResearcher": 0.0510,
        }
        weights = weights or default_weights

        total_weight = 0.0
        weighted_score = 0.0

        # Normalize each confidence once, up front
        normalized_confidences = [cls._normalize_conf(r.confidence) for r in responses]

        for resp, norm_conf in zip(responses, normalized_confidences):
            w = weights.get(resp.agent_name, 0.10)
            try:
                sig = Signal(resp.signal)
            except ValueError:
                sig = Signal.NEUTRAL
            score = sig.score
            weighted_score += w * score
            total_weight += w

        # Нормализация
        normalized = (weighted_score / total_weight) * 100 if total_weight > 0 else 50

        # Финальный сигнал
        if normalized >= 80:
            final_signal = Signal.STRONG_BUY
        elif normalized >= 65:
            final_signal = Signal.BUY
        elif normalized >= 50:
            final_signal = Signal.NEUTRAL
        elif normalized >= 35:
            final_signal = Signal.SELL
        else:
            final_signal = Signal.STRONG_SELL

        # Риск-менеджмент
        if final_signal in (Signal.STRONG_BUY, Signal.BUY):
            entry = entry_price
            stop = entry * (1 - risk_pct)
            target = entry * (1 + risk_pct * 2)
        elif final_signal in (Signal.STRONG_SELL, Signal.SELL):
            entry = entry_price
            stop = entry * (1 + risk_pct)
            target = entry * (1 - risk_pct * 2)
        else:
            entry = entry_price
            stop = entry * (1 - risk_pct)
            target = entry * (1 + risk_pct)

        rr = abs(target - entry) / abs(entry - stop) if abs(entry - stop) > 0 else 1.0

        # Average normalized confidences
        avg_conf = min(95, sum(normalized_confidences) // len(normalized_confidences))

        return cls(
            symbol=symbol,
            signal=final_signal,
            confidence=avg_conf,
            entry=round(entry, 2),
            stop_loss=round(stop, 2),
            take_profit=round(target, 2),
            risk_reward=round(rr, 2),
            agents=responses,
            summary=f"{final_signal.value} ({normalized:.0f}/100)",
        )
