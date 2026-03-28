"""amre/similarity.py — Market regime similarity scoring"""
import hashlib
import pickle
from typing import List
from .trajectory import Trajectory

similarity_cache = {}

def market_state_hash(state: dict) -> str:
    keys = ["rsi", "macd_hist", "volatility", "volume_trend", "trend_strength"]
    vals = [state.get(k, 0) for k in keys]
    return hashlib.md5(pickle.dumps(vals)).hexdigest()[:8]

def compute_trajectory_similarity(t1: Trajectory, t2: Trajectory) -> float:
    if t1.market_state_hash == t2.market_state_hash:
        return 1.0
    s1 = set(t1.market_state_hash)
    s2 = set(t2.market_state_hash)
    return len(s1 & s2) / max(len(s1 | s2), 1)

def is_similar_regime(traj: Trajectory, buffer_trajectories: List[Trajectory], threshold: float = 0.6) -> bool:
    if not buffer_trajectories:
        return False
    for bt in buffer_trajectories:
        sim = compute_trajectory_similarity(traj, bt)
        if sim >= threshold:
            return True
    return False

def get_similar_trajectories(traj: Trajectory, buffer_trajectories: List[Trajectory], top_k: int = 5) -> List[Trajectory]:
    scored = []
    for bt in buffer_trajectories:
        sim = compute_trajectory_similarity(traj, bt)
        if sim > 0:
            scored.append((sim, bt))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [t for _, t in scored[:top_k]]
