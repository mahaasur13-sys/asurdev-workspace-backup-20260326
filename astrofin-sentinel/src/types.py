from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class Symbol(str, Enum):
    BTC = "bitcoin"
    ETH = "ethereum"
    SOL = "solana"
    # extend as needed


class TimeFrame(str, Enum):
    HOUR_1 = "1h"
    HOUR_4 = "4h"
    DAY_1 = "1d"
    DAY_7 = "7d"


class Decision(str, Enum):
    STRONG_BUY = "STRONG_BUY"
    BUY = "BUY"
    NEUTRAL = "NEUTRAL"
    SELL = "SELL"
    STRONG_SELL = "STRONG_SELL"


class MarketData(BaseModel):
    symbol: Symbol
    timeframe: TimeFrame
    price: float
    change_24h: float
    volume: float
    market_cap: float
    ath: float
    ath_change: float
    high_24h: float
    low_24h: float
    fetched_at: datetime


class AstroSignal(BaseModel):
    moon_phase: str
    moon_phase_deg: float
    lunar_day: str  # Shukla Paksha / Krishna Paksha
    nakshatra: str
    yoga: str
    karana: str
    is_favorable: bool
    strength_score: float = Field(ge=0.0, le=1.0)
    interpretation: str
    recommendation: str


class TechnicalAnalysis(BaseModel):
    trend: str  # "bullish", "bearish", "neutral"
    support: float
    resistance: float
    rsi: float
    macd_signal: str
    signals: list[str]
    confidence: float = Field(ge=0.0, le=1.0)


class SentimentResult(BaseModel):
    source: str
    score: float  # -1 to 1
    summary: str


class AgentOpinion(BaseModel):
    agent_name: str
    role: str
    decision: Decision
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str
    key_factors: list[str]
    weight: float = Field(ge=0.0, le=1.0, default=1.0)


class BoardVote(BaseModel):
    timestamp: datetime
    symbol: Symbol
    agents: list[AgentOpinion]
    consensus_score: float  # how aligned are agents (0-1)
    final_decision: Decision
    final_confidence: float
    final_recommendation: str
    risk_assessment: str
