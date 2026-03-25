"""
Unified types for asurdev Sentinel v3.1
=========================================

Single source of truth for:
- Signal enum
- AgentResponse dataclass
- TradingSignal dataclass

No more duplicates across signal.py, _core/types.py, base_agent.py!
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum


# =============================================================================
# SIGNAL ENUM
# =============================================================================

class Signal(str, Enum):
    """
    Unified trading signal enum.
    6-level scale + helper properties.
    """
    
    STRONG_BUY = "STRONG_BUY"
    BUY = "BUY"
    NEUTRAL = "NEUTRAL"
    HOLD = "HOLD"
    SELL = "SELL"
    STRONG_SELL = "STRONG_SELL"
    
    # Backwards compatibility aliases
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    
    # Legacy mapping
    @classmethod
    def from_string(cls, s: str) -> "Signal":
        """Convert string to Signal."""
        mapping = {
            "STRONG_BUY": cls.STRONG_BUY,
            "BUY": cls.BUY,
            "NEUTRAL": cls.NEUTRAL,
            "HOLD": cls.HOLD,
            "SELL": cls.SELL,
            "STRONG_SELL": cls.STRONG_SELL,
            "BULLISH": cls.BUY,
            "BEARISH": cls.SELL,
        }
        return mapping.get(s.upper(), cls.NEUTRAL)
    
    @property
    def is_bullish(self) -> bool:
        return self in (Signal.STRONG_BUY, Signal.BUY, Signal.BULLISH)
    
    @property
    def is_bearish(self) -> bool:
        return self in (Signal.STRONG_SELL, Signal.SELL, Signal.BEARISH)
    
    @property
    def is_neutral(self) -> bool:
        return self in (Signal.NEUTRAL, Signal.HOLD)
    
    @property
    def score(self) -> int:
        """Convert to numeric score (-100 to +100)."""
        score_map = {
            Signal.STRONG_BUY: 100,
            Signal.BUY: 70,
            Signal.NEUTRAL: 50,
            Signal.HOLD: 50,
            Signal.SELL: 30,
            Signal.STRONG_SELL: 0,
            Signal.BULLISH: 70,
            Signal.BEARISH: 30,
        }
        return score_map.get(self, 50)
    
    def __str__(self) -> str:
        return self.value


# =============================================================================
# AGENT RESPONSE
# =============================================================================

@dataclass
class AgentResponse:
    """
    Standardized agent response.
    
    All agents return this type for unified processing.
    """
    agent_name: str
    signal: str  # BULLISH / BEARISH / NEUTRAL
    confidence: int  # 0-100
    summary: str
    details: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        if isinstance(d.get('timestamp'), datetime):
            d['timestamp'] = d['timestamp'].isoformat()
        return d
    
    @property
    def signal_enum(self) -> Signal:
        """Get Signal enum from string."""
        return Signal.from_string(self.signal)


# =============================================================================
# TRADING SIGNAL (Final output)
# =============================================================================

@dataclass
class TradingSignal:
    """
    Final trading signal output.
    Combines all agent responses into actionable recommendation.
    """
    symbol: str
    signal: Signal
    confidence: int  # 0-100
    entry: float
    stop_loss: float
    take_profit: float
    risk_reward: float
    agents: List[AgentResponse]
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    @classmethod
    def from_agents(
        cls,
        symbol: str,
        responses: List[AgentResponse],
        entry_price: float,
    ) -> "TradingSignal":
        """Create TradingSignal from agent responses."""
        
        # Weighted average of signals
        total_weight = 0
        weighted_score = 0
        
        weights = {
            "Market": 0.25,
            "Bull": 0.15,
            "Bear": 0.15,
            "AstroCouncil": 0.20,
            "Cycle": 0.10,
            "Gann": 0.05,
            "Andrews": 0.05,
            "Dow": 0.05,
        }
        
        for resp in responses:
            w = weights.get(resp.agent_name, 0.1)
            score = Signal.from_string(resp.signal).score
            weighted_score += w * score
            total_weight += w
        
        if total_weight > 0:
            normalized = (weighted_score / total_weight - 50) * 2 + 50
        else:
            normalized = 50
        
        # Determine final signal
        if normalized >= 80:
            signal = Signal.STRONG_BUY
        elif normalized >= 65:
            signal = Signal.BUY
        elif normalized >= 45:
            signal = Signal.NEUTRAL
        elif normalized >= 30:
            signal = Signal.SELL
        else:
            signal = Signal.STRONG_SELL
        
        # Calculate levels (simplified)
        risk_pct = 0.02  # 2% risk
        if signal.is_bullish:
            entry = entry_price
            stop = entry * (1 - risk_pct)
            target = entry * (1 + risk_pct * 2)
        else:
            entry = entry_price
            stop = entry * (1 + risk_pct)
            target = entry * (1 - risk_pct * 2)
        
        rr = abs(target - entry) / abs(entry - stop) if abs(entry - stop) > 0 else 1
        
        avg_conf = sum(r.confidence for r in responses) / len(responses) if responses else 50
        
        return cls(
            symbol=symbol,
            signal=signal,
            confidence=min(95, avg_conf),
            entry=round(entry, 2),
            stop_loss=round(stop, 2),
            take_profit=round(target, 2),
            risk_reward=round(rr, 2),
            agents=responses,
        )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "signal": self.signal.value,
            "confidence": self.confidence,
            "entry": self.entry,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "risk_reward": self.risk_reward,
            "agents": [a.to_dict() for a in self.agents],
            "timestamp": self.timestamp,
        }


# =============================================================================
# LEGACY ALIASES (for backwards compatibility)
# =============================================================================

# Keep old names as aliases
SignalType = Signal  # Backwards compatibility
AgentResult = AgentResponse  # Backwards compatibility
