from typing import TypedDict, Annotated
from datetime import datetime
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import add_messages
from src.types import (
    Symbol, TimeFrame, Decision, MarketData, AstroSignal,
    TechnicalAnalysis, AgentOpinion, BoardVote
)


class AgentState(TypedDict):
    """Shared state for the multi-agent graph."""
    # Input
    symbol: Symbol
    timeframe: TimeFrame
    user_question: str
    
    # Market data
    market_data: MarketData | None
    technical_analysis: TechnicalAnalysis | None
    
    # Astro
    astro_signal: AstroSignal | None
    
    # Agent opinions (accumulated)
    market_analyst_opinion: AgentOpinion | None
    bull_opinion: AgentOpinion | None
    bear_opinion: AgentOpinion | None
    astro_opinion: AgentOpinion | None
    
    # Messages for LLM calls
    messages: Annotated[list[BaseMessage], add_messages]
    
    # Final output
    board_vote: BoardVote | None
    
    # Metadata
    started_at: datetime
    errors: list[str]


def create_initial_state(
    symbol: Symbol,
    timeframe: TimeFrame = TimeFrame.HOUR_4,
    user_question: str = ""
) -> AgentState:
    """Factory to create initial state."""
    return AgentState(
        symbol=symbol,
        timeframe=timeframe,
        user_question=user_question,
        market_data=None,
        technical_analysis=None,
        astro_signal=None,
        market_analyst_opinion=None,
        bull_opinion=None,
        bear_opinion=None,
        astro_opinion=None,
        messages=[HumanMessage(content=user_question)] if user_question else [],
        board_vote=None,
        started_at=datetime.utcnow(),
        errors=[]
    )
