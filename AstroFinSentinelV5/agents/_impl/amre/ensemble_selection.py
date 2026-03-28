"""amre/ensemble_selection.py — ATOM-KARL-007 Ensemble TTC Selection"""
from typing import List, Optional
from .trajectory import Trajectory

def majority_vote(directions: List[str]) -> str:
    counts = {}
    for d in directions:
        canon = d.upper()
        if canon in ("BUY", "STRONG_BUY"):
            canon = "LONG"
        elif canon in ("SELL", "STRONG_SELL"):
            canon = "SHORT"
        counts[canon] = counts.get(canon, 0) + 1
    if not counts:
        return "NEUTRAL"
    return max(counts, key=counts.get)

def ensemble_select(trajectories: List[Trajectory], top_k: int = 5) -> dict:
    """ATOM-KARL-007: Replace max() with ensemble selection."""
    if not trajectories:
        return {"direction": "NEUTRAL", "confidence": 50, "count": 0}
    sorted_traj = sorted(trajectories, key=lambda t: t.final_reward, reverse=True)
    top = sorted_traj[:top_k]
    directions = [t.direction for t in top]
    direction = majority_vote(directions)
    confidence = sum(t.confidence for t in top) // len(top)
    return {"direction": direction, "confidence": confidence, "count": len(top)}

def ensemble_select_from_buffer(buffer: list, top_k: int = 5) -> List[Trajectory]:
    """Select top-k from buffer using ensemble method."""
    if not buffer:
        return []
    sorted_traj = sorted(buffer, key=lambda t: t.final_reward, reverse=True)
    return sorted_traj[:top_k]
