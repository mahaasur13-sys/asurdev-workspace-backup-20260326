"""
SentinelState — единый state для LangGraph графа AstroFin Sentinel.

All astro data MUST come from Swiss Ephemeris (verified) before reaching LLM.
LLM receives ONLY interpretations, never raw calculation results.
"""

from typing import Literal, Optional
from pydantic import BaseModel, Field, field_validator
from datetime import datetime


# ============================================================
# RAW ASTRO DATA CONTRACTS (from Swiss Ephemeris only)
# ============================================================

class MoonPhaseData(BaseModel):
    """Верифицированные данные лунной фазы (из Swiss Ephemeris)."""
    phase_name: str                          # "New Moon", "Full Moon", etc.
    phase_value: float = Field(ge=0.0, le=1.0)  # 0.0-1.0synodic cycle
    illumination_pct: float = Field(ge=0.0, le=100.0)
    days_since_new_moon: float = Field(ge=0.0, le=29.53)
    zodiac_sign: str
    zodiac_degree: float = Field(ge=0.0, le=30.0)
    timestamp: datetime

    @field_validator("phase_name")
    @classmethod
    def validate_phase_name(cls, v: str) -> str:
        valid = {"New Moon", "Waxing Crescent", "First Quarter", "Waxing Gibbous",
                 "Full Moon", "Waning Gibbous", "Last Quarter", "Waning Crescent"}
        if v not in valid:
            raise ValueError(f"Invalid phase: {v}")
        return v


class PlanetaryAspect(BaseModel):
    """Верифицированный планетный аспект (из Swiss Ephemeris)."""
    date: str                                # YYYY-MM-DD
    planet1: str                             # "jupiter", "mars", etc.
    planet2: str
    aspect_name: str                        # "conjunction", "trine", etc.
    exact_degree: float                      # 0-360
    orb: float = Field(ge=0.0, le=5.0)      # orb in degrees
    timestamp: datetime


class RetrogradeStatus(BaseModel):
    """Статус ретроградности планеты."""
    planet: str
    is_retrograde: bool
    speed_deg_per_day: float                 # negative = retrograde
    recommendation: str


class RawAstroData(BaseModel):
    """
    Контракт для сырых астрономических данных.
    ВСЕ поля — из Swiss Ephemeris, верифицированы.
    LLM получает ТОЛЬКО интерпретации, НИКОГДА сырые расчёты.
    """
    moon: MoonPhaseData
    planetary_positions: dict[str, float]   # {planet_name: degrees}
    aspects: list[PlanetaryAspect]
    retrogrades: list[RetrogradeStatus]
    calculation_hash: str                     # SHA256 для дедупликации
    calculated_at: datetime
    ephemeris_source: str = "swisseph"       # or "simplified_fallback"


# ============================================================
# AGENT OUTPUT CONTRACTS
# ============================================================

class KeyFactor(BaseModel):
    """Структурированный ключевой фактор от агента."""
    factor: str
    weight: float = Field(ge=0.0, le=1.0)
    direction: Literal["bullish", "bearish", "neutral"]


class AgentResult(BaseModel):
    """Базовый контракт результата агента."""
    agent_name: str
    recommendation: Literal["buy", "sell", "hold"]
    confidence: float = Field(ge=0.0, le=1.0, description="0.0-1.0, never 1.0 exactly")
    reasoning: str
    key_factors: list[KeyFactor] = []
    warnings: list[str] = []
    metadata: dict = {}
    calculated_at: datetime = Field(default_factory=datetime.utcnow)

    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        if v >= 1.0:
            raise ValueError("Confidence can never be 1.0 (100%)")
        if v <= 0.0:
            raise ValueError("Confidence can never be 0.0")
        return round(v, 3)


class TechnicalResult(AgentResult):
    """Результат Technical Analyst."""
    trend: Literal["bullish", "bearish", "neutral", "unclear"] = "neutral"
    support_level: float | None = None
    resistance_level: float | None = None
    entry_zone: tuple[float, float] | None = None  # (min, max)
    stop_loss: float | None = None
    take_profit: list[float] = []
    risk_reward: float | None = None
    indicators_used: list[str] = []


class DirectionalResult(AgentResult):
    """Результат Bull/Bear Researcher."""
    bias: Literal["bullish", "bearish", "neutral"]
    evidence_strength: float = Field(ge=0.0, le=1.0)
    key_thesis: str
    price_targets: dict[Literal["conservative", "realistic", "optimistic", "worst_case"], float] = {}


class AstroResult(AgentResult):
    """Результат Astro Advisor (ИНТЕРПРЕТАЦИЯ, не сырые данные)."""
    mood_score: float = Field(ge=-1.0, le=1.0)  # -1 very bearish, +1 very bullish
    timing_signal: Literal["highly_favorable", "favorable", "neutral", "unfavorable", "highly_unfavorable"]
    lunar_signal: str                            # e.g. "Full Moon: elevated volatility expected"
    planetary_signal: str                         # e.g. "Mars-Saturn square: tension ahead"
    risk_adjustment: float = Field(ge=-0.3, le=0.3)  # confidence adjustment from astro


class RiskResult(AgentResult):
    """Результат Risk Agent."""
    position_size_pct: float = Field(ge=0.0, le=100.0)
    max_loss_usd: float
    max_gain_usd: float
    risk_per_trade_pct: float = Field(ge=0.0, le=5.0)
    stop_loss_pct: float | None = None
    time_stop_hours: int | None = None


class SynthesisResult(AgentResult):
    """Финальный результат синтезатора."""
    vote_counts: dict[str, int] = {}           # {"buy": 3, "sell": 1, "hold": 1}
    weighted_scores: dict[str, float] = {}      # {"buy": 0.65, "sell": 0.20, "hold": 0.15}
    debate_summary: str
    final_recommendation: Literal["buy", "sell", "hold"]
    confidence: float = Field(ge=0.0, le=1.0)
    risk_assessment: Literal["low", "medium", "high", "extreme"]
    warnings: list[str] = []


# ============================================================
# SENTINEL STATE (LangGraph state schema)
# ============================================================

class SentinelState(BaseModel):
    """
    Единый state для LangGraph графа.
    
    Правила:
    1. RawAstroData вычисляется ДО вызова любого LLM агента
    2. LLM агенты получают ТОЛЬКО интерпретации (не сырые данные)
    3. Все результаты проходят валидацию через Pydantic
    """
    # === INPUT ===
    symbol: str
    action: Literal["buy", "sell", "hold"]
    price: float
    ml_confidence: float = Field(ge=0.0, le=1.0)
    strategy: str = "unknown"
    timeframe: str = "1h"
    alert_id: str = ""
    
    # === RAW ASTRO (verified, from Swiss Ephemeris) ===
    astro_data: RawAstroData | None = None
    
    # === AGENT RESULTS ===
    technical_result: TechnicalResult | None = None
    bull_result: DirectionalResult | None = None
    bear_result: DirectionalResult | None = None
    astro_result: AstroResult | None = None
    risk_result: RiskResult | None = None
    
    # === SYNTHESIS ===
    synthesis: SynthesisResult | None = None
    
    # === META ===
    errors: list[str] = []
    iteration: int = 0
    mode: Literal["quick", "standard", "full", "debate"] = "standard"
    
    # === FLAGS ===
    astro_data_verified: bool = False
    agents_completed: list[str] = []
    
    @property
    def completed_agents_count(self) -> int:
        return len(self.agents_completed)
    
    @property
    def has_errors(self) -> bool:
        return len(self.errors) > 0
