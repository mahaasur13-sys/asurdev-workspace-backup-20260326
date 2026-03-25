"""
State definitions for AstroFin Sentinel LangGraph

Contains:
- AnalysisState: Main state managed throughout graph execution
- AgentReport: Dataclass for individual agent outputs
- ReportMetadata: Metadata for each agent report
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Any
from pydantic import BaseModel, Field


class QueryType(str, Enum):
    """Type of analysis query."""
    TECHNICAL_ONLY = "technical_only"
    TECHNICAL_FUNDAMENTAL = "technical_fundamental"
    FULL_ANALYSIS = "full_analysis"
    QUICK_SCAN = "quick_scan"


class AgentStatus(str, Enum):
    """Status of agent execution."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class RiskLevel(str, Enum):
    """Risk tolerance level."""
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"


@dataclass
class ReportMetadata:
    """Metadata for an agent report."""
    agent_id: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    execution_time_ms: Optional[int] = None
    status: AgentStatus = AgentStatus.PENDING
    error: Optional[str] = None
    confidence_override: Optional[float] = None  # Manual adjustment


@dataclass
class AgentReport:
    """
    Individual agent report with standardized fields.
    
    Each agent (Technical, Fundamental, Astrologer) produces
    this structure which is then passed to the Synthesizer.
    """
    agent_id: str
    signal: str  # BUY, SELL, HOLD, WAIT, STRONG_BUY, STRONG_SELL
    confidence: float  # 0.0 - 1.0
    reasoning: str
    data: dict = field(default_factory=dict)  # Agent-specific data
    metadata: Optional[ReportMetadata] = None
    
    def to_dict(self) -> dict:
        return {
            "agent_id": self.agent_id,
            "signal": self.signal,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "data": self.data,
            "metadata": {
                "status": self.metadata.status.value if self.metadata else None,
                "execution_time_ms": self.metadata.execution_time_ms if self.metadata else None
            } if self.metadata else None
        }


@dataclass
class AnalysisState:
    """
    Main state managed throughout the LangGraph execution.
    
    This state is passed between nodes and accumulates results
    as the graph progresses through the analysis pipeline.
    """
    # === Input ===
    symbol: str = ""
    side: str = "buy"  # "buy" or "sell"
    interval: str = "1h"
    birth_date: Optional[str] = None
    birth_time: Optional[str] = None
    weights: dict = field(default_factory=lambda: {
        "technical": 0.30,
        "fundamental": 0.30,
        "astrological": 0.40
    })
    risk_level: RiskLevel = RiskLevel.MODERATE
    
    # === Query Routing ===
    query_type: QueryType = QueryType.FULL_ANALYSIS
    skip_agents: list = field(default_factory=list)  # Agents to skip
    
    # === Agent Reports ===
    technical_report: Optional[AgentReport] = None
    fundamental_report: Optional[AgentReport] = None
    astrologer_report: Optional[AgentReport] = None
    
    # === Agent Metadata ===
    technical_meta: Optional[ReportMetadata] = None
    fundamental_meta: Optional[ReportMetadata] = None
    astrologer_meta: Optional[ReportMetadata] = None
    
    # === Synthesis ===
    synthesizer_report: Optional[dict] = None
    composite_score: Optional[float] = None
    
    # === Memory / RAG ===
    session_id: str = ""
    memory_context: list = field(default_factory=list)  # Retrieved relevant memories
    analysis_history: list = field(default_factory=list)  # Past analyses
    
    # === Quality Gate ===
    quality_passed: bool = True
    quality_issues: list = field(default_factory=list)
    
    # === Output ===
    final_recommendation: Optional[dict] = None
    markdown_output: str = ""
    error: Optional[str] = None
    
    # === Timestamps ===
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    
    def get_all_reports(self) -> list[AgentReport]:
        """Get all completed agent reports."""
        reports = []
        if self.technical_report and self.technical_meta and self.technical_meta.status == AgentStatus.COMPLETED:
            reports.append(self.technical_report)
        if self.fundamental_report and self.fundamental_meta and self.fundamental_meta.status == AgentStatus.COMPLETED:
            reports.append(self.fundamental_report)
        if self.astrologer_report and self.astrologer_meta and self.astrologer_meta.status == AgentStatus.COMPLETED:
            reports.append(self.astrologer_report)
        return reports
    
    def get_active_signals(self) -> dict[str, float]:
        """Get signals from all active agents with their confidences."""
        signals = {}
        for report in self.get_all_reports():
            signals[report.agent_id] = report.confidence
        return signals
    
    def is_complete(self) -> bool:
        """Check if all required agents have completed."""
        required = []
        if self.query_type in [QueryType.FULL_ANALYSIS, QueryType.TECHNICAL_ONLY, QueryType.QUICK_SCAN]:
            if "technical" not in self.skip_agents:
                required.append("technical")
        if self.query_type in [QueryType.FULL_ANALYSIS, QueryType.TECHNICAL_FUNDAMENTAL]:
            if "fundamental" not in self.skip_agents:
                required.append("fundamental")
        if self.query_type == QueryType.FULL_ANALYSIS:
            if "astrologer" not in self.skip_agents:
                required.append("astrologer")
        
        for agent in required:
            meta = getattr(self, f"{agent}_meta")
            if not meta or meta.status != AgentStatus.COMPLETED:
                return False
        return True


# === Pydantic models for API serialization ===

class AgentReportModel(BaseModel):
    """Pydantic model for API responses."""
    agent_id: str
    signal: str
    confidence: float
    reasoning: str
    data: dict = Field(default_factory=dict)
    execution_time_ms: Optional[int] = None

    class Config:
        use_enum_values = True


class AnalysisResultModel(BaseModel):
    """Pydantic model for final analysis result."""
    symbol: str
    side: str
    composite_score: float
    recommendation: dict
    technical: Optional[AgentReportModel] = None
    fundamental: Optional[AgentReportModel] = None
    astrologer: Optional[AgentReportModel] = None
    board_opinions: dict
    scenarios: dict
    risk_warnings: list[str]
    muhurta_time: Optional[str] = None
    markdown: str
    timestamp: str
    
    class Config:
        use_enum_values = True
