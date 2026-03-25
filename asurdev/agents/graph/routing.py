"""
LangGraph Routing Logic
asurdev Sentinel v3.2

Conditional routing functions for the state machine.
"""

from typing import Literal
from ..state import SentinelState


def route_based_on_disagreement(state: SentinelState) -> Literal["gann", "andrews", "synthesize"]:
    """
    Route based on bull/bear disagreement level.
    
    Flow:
    - diff > 30 → Gann (needs resolution)
    - diff > 15 → Andrews (moderate)
    - else → direct synthesis
    
    Args:
        state: Current SentinelState
        
    Returns:
        Next node name: "gann", "andrews", or "synthesize"
    """
    bull = state.get("bull_response")
    bear = state.get("bear_response")
    
    if not bull or not bear:
        return "synthesize"
    
    diff = abs(bull.confidence - bear.confidence)
    
    if diff > 30:
        return "gann"
    elif diff > 15:
        return "andrews"
    else:
        return "synthesize"
