"""amre/replay_buffer.py — Replay Buffer for trajectory learning"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from .trajectory import Trajectory, TrajectoryMetrics
from .similarity import is_similar_trajectory

DEFAULT_BUFFER_SIZE = 1000

@dataclass
class BufferEntry:
    trajectory: Trajectory
    metrics: TrajectoryMetrics
    outcome: float
    market_context: Dict[str, Any]
    created_at: str

class ReplayBuffer:
    def __init__(self, max_size: int = DEFAULT_BUFFER_SIZE):
        self.max_size = max_size
        self.buffer: List[BufferEntry] = []

    def add(self, entry: BufferEntry):
        self.buffer.append(entry)
        if len(self.buffer) > self.max_size:
            self.buffer.pop(0)

    def get_all_trajectories(self) -> List[Trajectory]:
        return [e.trajectory for e in self.buffer]

    def get_similar(self, trajectory: Trajectory, threshold: float = 0.3) -> List[BufferEntry]:
        return [e for e in self.buffer if is_similar_trajectory(trajectory, e.trajectory, threshold)]

    def size(self) -> int:
        return len(self.buffer)

_DEFAULT_BUFFER: Optional[ReplayBuffer] = None

def get_default_buffer() -> ReplayBuffer:
    global _DEFAULT_BUFFER
    if _DEFAULT_BUFFER is None:
        _DEFAULT_BUFFER = ReplayBuffer()
    return _DEFAULT_BUFFER

def _select_best_trajectory(trajectories: List[Trajectory], q_star_scores: List[float]) -> Trajectory:
    if not trajectories:
        raise ValueError("No trajectories provided")
    scored = list(zip(trajectories, q_star_scores))
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[0][0]
