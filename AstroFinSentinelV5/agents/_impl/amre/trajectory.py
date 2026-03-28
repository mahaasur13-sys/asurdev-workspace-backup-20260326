"""amre/trajectory.py — KARL Trajectory data structures"""
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime

@dataclass
class TrajectoryStep:
    timestamp: str
    direction: str
    confidence: int
    reasoning: str
    market_state: dict
    metadata: dict

@dataclass
class TrajectoryMetrics:
    sharpe: float = 0.0
    win_rate: float = 0.0
    total_return: float = 0.0
    max_drawdown: float = 0.0
    trade_count: int = 0
    avg_confidence: float = 50.0
    q_star: Optional[float] = None

@dataclass
class Trajectory:
    trajectory_id: str
    symbol: str
    timeframe: str
    direction: str
    confidence: int
    reasoning: str
    start_time: str
    end_time: str
    final_reward: float = 0.0
    steps: list = field(default_factory=list)
    metrics: Optional[TrajectoryMetrics] = None
    market_state_hash: str = ""
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "trajectory_id": self.trajectory_id,
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "direction": self.direction,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "final_reward": self.final_reward,
            "steps": [{"timestamp": s.timestamp, "direction": s.direction, "confidence": s.confidence, "reasoning": s.reasoning} for s in self.steps],
            "metrics": {"sharpe": self.metrics.sharpe, "win_rate": self.metrics.win_rate, "total_return": self.metrics.total_return, "max_drawdown": self.metrics.max_drawdown, "trade_count": self.metrics.trade_count, "avg_confidence": self.metrics.avg_confidence, "q_star": self.metrics.q_star} if self.metrics else {},
            "market_state_hash": self.market_state_hash,
            "metadata": self.metadata,
        }
