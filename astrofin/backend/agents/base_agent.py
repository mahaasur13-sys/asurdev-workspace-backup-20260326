"""Base agent classes for AstroFin."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class Signal(str, Enum):
    """Trading signal direction."""

    LONG = "LONG"
    SHORT = "SHORT"
    NEUTRAL = "NEUTRAL"
    AVOID = "AVOID"


@dataclass
class AgentResponse:
    """Standard response from every agent."""

    agent_name: str
    signal: Signal
    confidence: float
    reasoning: str = ""
    sources: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "agent_name": self.agent_name,
            "signal": self.signal.value,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "sources": self.sources,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
        }


@dataclass
class TradingSignal:
    """Final trading signal with risk management."""

    signal: Signal
    confidence: float
    reasoning: str
    entry_price: float = 0.0
    stop_loss_pct: float = 0.05
    targets: list[float] = field(default_factory=list)
    position_size_pct: float = 0.05
    risk_reward: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_agents(
        cls, symbol: str, responses: list[AgentResponse], entry_price: float
    ) -> "TradingSignal":
        """
        Aggregate agent responses into final signal using weighted voting.

        Uses proper weighted scoring instead of simple vote counting.
        """
        # Agent weights for synthesis
        WEIGHTS: dict[str, float] = {
            "AstroCouncil": 0.20,
            "FundamentalAgent": 0.18,
            "MacroAgent": 0.13,
            "QuantAgent": 0.12,
            "PredictorAgent": 0.12,
            "OptionsFlowAgent": 0.10,
            "SentimentAgent": 0.08,
            "TechnicalAgent": 0.07,
        }

        long_score = 0.0
        short_score = 0.0
        neutral_score = 0.0
        avoid_score = 0.0
        total_weight = 0.0
        votes = []

        for resp in responses:
            weight = WEIGHTS.get(resp.agent_name, 0.05)
            total_weight += weight

            if resp.signal == Signal.LONG:
                long_score += resp.confidence * weight
                votes.append(f"+{resp.agent_name}×{weight:.2f}")
            elif resp.signal == Signal.SHORT:
                short_score += resp.confidence * weight
                votes.append(f"-{resp.agent_name}×{weight:.2f}")
            elif resp.signal == Signal.AVOID:
                avoid_score += resp.confidence * weight
            else:
                neutral_score += weight * 0.5

        if total_weight == 0:
            total_weight = 1.0

        long_pct = long_score / total_weight
        short_pct = short_score / total_weight
        avoid_pct = avoid_score / total_weight

        # Risk rules
        if avoid_pct > 0.3:
            final_signal = Signal.NEUTRAL
            final_confidence = 1.0 - avoid_pct
            reasoning = f"AVOID: {avoid_pct*100:.0f}% risk. Stand aside."
        elif long_pct > 0.45:
            final_signal = Signal.LONG
            final_confidence = min(0.9, 0.5 + long_pct * 0.4)
            reasoning = f"Long consensus: {long_pct*100:.0f}% ({', '.join(votes[:5])}...)"
        elif short_pct > 0.45:
            final_signal = Signal.SHORT
            final_confidence = min(0.9, 0.5 + short_pct * 0.4)
            reasoning = f"Short consensus: {short_pct*100:.0f}%"
        else:
            final_signal = Signal.NEUTRAL
            final_confidence = 0.4
            reasoning = f"No consensus. Long {long_pct*100:.0f}% | Short {short_pct*100:.0f}%"

        # Calculate risk/reward
        rr = 1.5
        if final_signal == Signal.LONG:
            entry = entry_price * 1.01
            stop = entry_price * 0.97
            target = entry_price * 1.06
            rr = (target - entry) / (entry - stop) if entry != stop else 1.0
        elif final_signal == Signal.SHORT:
            entry = entry_price * 0.99
            stop = entry_price * 1.03
            target = entry_price * 0.94
            rr = (entry - target) / (stop - entry) if stop != entry else 1.0

        return cls(
            signal=final_signal,
            confidence=final_confidence,
            reasoning=reasoning,
            entry_price=entry_price,
            targets=[entry_price * 1.03, entry_price * 1.06, entry_price * 1.10] if final_signal == Signal.LONG else [entry_price * 0.97, entry_price * 0.94, entry_price * 0.90],
            risk_reward=round(rr, 2),
            metadata={"votes": votes, "long_pct": long_pct, "short_pct": short_pct, "avoid_pct": avoid_pct},
        )


class BaseAgent(ABC):
    """Base class for all agents."""

    def __init__(self, name: str, system_prompt: str = "") -> None:
        self.name = name
        self.system_prompt = system_prompt
        self._responses: dict[str, AgentResponse] = {}

    @abstractmethod
    async def run(self, context: dict[str, Any]) -> AgentResponse:
        """Run the agent with given context."""
        pass

    async def analyze(self, context: dict[str, Any]) -> AgentResponse:
        """Alias for run()."""
        return await self.run(context)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.name}>"
