"""amre/replay_buffer.py — KARL Replay Buffer with TTC + Ensemble"""
from typing import List, Optional
from collections import deque
from .trajectory import Trajectory, TrajectoryMetrics
from .reward import compute_reward, RewardConfig
from .similarity import get_similar_trajectories
from .counterfactual import CounterfactualEngine
from .ensemble_selection import ensemble_select_from_buffer

class ReplayBuffer:
    def __init__(self, capacity: int = 1000):
        self.capacity = capacity
        self.buffer: deque = deque(maxlen=capacity)
        self.counterfactual_engine = CounterfactualEngine()

    def add(self, trajectory: Trajectory) -> None:
        self.buffer.append(trajectory)

    def get_trajectories(self) -> List[Trajectory]:
        return list(self.buffer)

    def get_by_symbol(self, symbol: str) -> List[Trajectory]:
        return [t for t in self.buffer if t.symbol == symbol]

    def select_best(self, trajectories: List[Trajectory], top_k: int = 5) -> List[Trajectory]:
        return ensemble_select_from_buffer(trajectories, top_k=top_k)

    def get_kpi(self) -> dict:
        if not self.buffer:
            return {"count": 0, "avg_reward": 0, "avg_sharpe": 0}
        trajs = list(self.buffer)
        rewards = [t.final_reward for t in trajs]
        sharpes = [t.metrics.sharpe if t.metrics else 0 for t in trajs]
        return {
            "count": len(trajs),
            "avg_reward": sum(rewards) / len(rewards),
            "avg_sharpe": sum(sharpes) / len(sharpes),
        }

DEFAULT_BUFFER: Optional[ReplayBuffer] = None

def get_global_buffer() -> ReplayBuffer:
    global DEFAULT_BUFFER
    if DEFAULT_BUFFER is None:
        DEFAULT_BUFFER = ReplayBuffer()
    return DEFAULT_BUFFER
