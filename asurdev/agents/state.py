"""
SentinelState TypedDict for LangGraph.
Updated for v3.1 with unified types.
"""

from typing import TypedDict, Annotated, Sequence, Optional, Any
from langchain_core.messages import BaseMessage
from .types import Signal


class SentinelState(TypedDict):
    """
    LangGraph state definition for asurdev Sentinel v3.1.
    
    Immutable dict with annotated fields for LangGraph.
    All agent responses are Optional since they're populated during execution.
    """
    
    # Conversation history (LangGraph manages this)
    messages: Annotated[Sequence[BaseMessage], "conversation history"]
    
    # Input parameters
    symbol: str
    action: str
    
    # Location for astrology (optional)
    lat: float
    lon: float
    
    # Market context (populated by market node)
    market_price: float
    market_trend: str  # BULLISH, BEARISH, NEUTRAL
    
    # Agent responses (all Optional, populated during execution)
    market_response: Optional[Any]  # AgentResponse
    bull_response: Optional[Any]
    bear_response: Optional[Any]
    astro_response: Optional[Any]  # AstroCouncil
    cycle_response: Optional[Any]
    dow_response: Optional[Any]
    andrews_response: Optional[Any]
    gann_response: Optional[Any]
    merriman_response: Optional[Any]
    meridian_response: Optional[Any]
    
    # Final synthesis
    synthesis: Optional[Any]  # AgentResponse
    final_verdict: Signal
    
    # Metadata
    errors: list[str]
    confidence_avg: float
