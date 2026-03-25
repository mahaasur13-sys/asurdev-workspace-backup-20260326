"""
AstroFin Sentinel — LangGraph State Definitions

Defines the state schema and message types for the multi-agent graph.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Literal
from enum import Enum


class AgentName(str, Enum):
    """Names of agents in the system."""
    ORCHESTRATOR = "orchestrator"
    TECHNICAL_ANALYST = "technical_analyst"
    FUNDAMENTAL_ANALYST = "fundamental_analyst"
    ASTROLOGER = "astrologer"
    SYNTHESIZER = "synthesizer"
    ROUTER = "router"


class MessageRole(str, Enum):
    """Roles for messages in the conversation."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    AGENT = "agent"  # Message from an agent


@dataclass
class AgentMessage:
    """A single message from an agent or user."""
    role: MessageRole
    content: str
    agent: Optional[AgentName] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: dict = field(default_factory=dict)


@dataclass
class Query:
    """User query for analysis."""
    symbol: str  # e.g., "BTC/USDT"
    side: Literal["buy", "sell"] = "buy"
    interval: str = "1h"  # Timeframe for technical analysis
    birth_date: Optional[str] = None  # Birth date for personalized astrology (DD.MM.YYYY)
    birth_time: Optional[str] = None  # Birth time (HH:MM)
    weights: dict = field(default_factory=lambda: {
        "technical": 0.30,
        "fundamental": 0.30,
        "astrological": 0.40
    })
    user_id: str = "default"


@dataclass 
class TechnicalReport:
    """Report from Technical Analyst."""
    signal: str  # BUY, SELL, HOLD, WAIT, STRONG_BUY, STRONG_SELL
    confidence: float  # 0.0 - 1.0
    reasoning: str
    levels: dict  # entry, stop_loss, take_profit_1/2/3
    indicators: dict  # RSI, MACD, Bollinger, etc.
    pattern: str  # Detected pattern name
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class FundamentalReport:
    """Report from Fundamental Analyst."""
    verdict: str  # STRONG_BUY, BUY, NEUTRAL, SELL, STRONG_SELL
    strength: float  # 0.0 - 1.0
    reasoning: str
    factors: list  # [{"factor": "...", "type": "positive/negative", "impact": "HIGH/MEDIUM/LOW"}]
    risk_factors: list  # [{"risk": "...", "severity": "HIGH/MEDIUM/LOW"}]
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class AstroReport:
    """Report from Vedic Astrologer."""
    signal: str
    confidence: float
    reasoning: str
    muhurta: dict  # overall, best_time, worst_time, reasoning
    favorable: list
    unfavorable: list
    planetary_yoga: dict
    transits: dict
    dasha: dict
    # Extended fields
    planet_strength: dict = field(default_factory=dict)
    nakshatra_influence: str = ""
    moon_phase: str = ""
    eclipse_risk: bool = False
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class SynthesizerReport:
    """Final synthesized report from the Board of Directors."""
    summary: str
    scenarios: dict  # bull, base, bear with probability, entry, target, stop_loss, risk_reward
    board_opinions: dict  # opinions from each agent
    weighted_score: dict  # technical, fundamental, astrological, composite
    recommendation: dict  # action, position_size, entry_zone, stop_loss, targets
    muhurta_time: str
    risk_warnings: list
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    symbol: str = ""


@dataclass
class AstroFinState:
    """
    Main state schema for LangGraph.
    
    This is the central state that flows through all nodes in the graph.
    """
    # User query
    query: Optional[Query] = None
    
    # Agent reports (populated as agents complete)
    technical_report: Optional[TechnicalReport] = None
    fundamental_report: Optional[FundamentalReport] = None
    astrological_report: Optional[AstroReport] = None
    
    # Synthesized result
    synthesizer_report: Optional[SynthesizerReport] = None
    
    # Conversation history (for RAG and context)
    messages: list[AgentMessage] = field(default_factory=list)
    
    # Memory retrieval results (from vector store)
    retrieved_memories: list[str] = field(default_factory=list)
    
    # Graph routing
    current_agent: Optional[AgentName] = None
    next_agents: list[AgentName] = field(default_factory=list)  # Agents to run next
    is_complete: bool = False
    
    # Error handling
    errors: dict = field(default_factory=dict)
    
    # Metadata
    conversation_id: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    # Configuration
    weights: dict = field(default_factory=lambda: {
        "technical": 0.30,
        "fundamental": 0.30,
        "astrological": 0.40
    })
    
    # Parallel execution flag
    parallel_enabled: bool = True
    
    # RAG enabled flag
    rag_enabled: bool = True


@dataclass 
class MemoryEntry:
    """Entry stored in RAG memory."""
    id: str
    content: str
    metadata: dict  # symbol, agent, timestamp, type (report/insight/warning)
    embedding: Optional[list[float]] = None


@dataclass
class AnalysisContext:
    """Context for a single analysis session (ephemeral)."""
    query: Query
    reports: dict  # agent_name -> report
    start_time: datetime
    end_time: Optional[datetime] = None
    
    @property
    def duration_seconds(self) -> float:
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0
