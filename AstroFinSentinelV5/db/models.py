"""db/models.py - SQLAlchemy models for AstroFin V5"""
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Text,
    ForeignKey, Enum, JSON, Numeric, Index
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func
import enum

Base = declarative_base()

class SignalDirection(enum.Enum):
    BUY = "BUY"; LONG = "LONG"; SELL = "SELL"; SHORT = "SHORT"
    NEUTRAL = "NEUTRAL"; HOLD = "HOLD"; AVOID = "AVOID"
    STRONG_BUY = "STRONG_BUY"; STRONG_SELL = "STRONG_SELL"

class VolatilityRegime(enum.Enum):
    LOW = "LOW"; NORMAL = "NORMAL"; HIGH = "HIGH"; EXTREME = "EXTREME"

class QueryType(enum.Enum):
    NATURAL = "NATURAL"; TECHNICAL = "TECHNICAL"; FUNDAMENTAL = "FUNDAMENTAL"
    MACRO = "MACRO"; QUANT = "QUANT"; OPTIONS = "OPTIONS"
    SENTIMENT = "SENTIMENT"; ASTRO = "ASTRO"; ELECTION = "ELECTION"

class SessionStatus(enum.Enum):
    pending = "pending"; running = "running"; completed = "completed"
    failed = "failed"; cancelled = "cancelled"

class AgentPool(enum.Enum):
    TECHNICAL = "TECHNICAL"; MACRO = "MACRO"; ASTRO = "ASTRO"; ELECTION = "ELECTION"
    SENTIMENT = "SENTIMENT"; QUANT = "QUANT"; FUNDAMENTAL = "FUNDAMENTAL"; OPTIONS = "OPTIONS"

class Session(Base):
    __tablename__ = "sessions"
    session_id = Column(UUID(as_uuid=True), primary_key=True)
    symbol = Column(String(20), nullable=False)
    timeframe = Column(String(20), nullable=False)
    query_type = Column(Enum(QueryType), nullable=False)
    current_price = Column(Numeric(20, 8))
    session_status = Column(Enum(SessionStatus), default=SessionStatus.pending)
    final_signal = Column(Enum(SignalDirection))
    final_confidence = Column(Integer)
    regime = Column(Enum(VolatilityRegime), default=VolatilityRegime.NORMAL)
    flows_run = Column(JSONB)
    thompson_selections = Column(JSONB)
    agent_count = Column(Integer, default=0)
    started_at = Column(DateTime(timezone=True), default=func.now())
    finished_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=func.now())

    signals = relationship("AgentSignal", back_populates="session", cascade="all, delete-orphan")
    decisions = relationship("KARLDecisionRecord", back_populates="session")

class AgentSignal(Base):
    __tablename__ = "agent_signals"
    signal_id = Column(UUID(as_uuid=True), primary_key=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.session_id", ondelete="CASCADE"))
    agent_name = Column(String(100), nullable=False)
    agent_pool = Column(Enum(AgentPool))
    signal = Column(Enum(SignalDirection))
    confidence = Column(Integer)
    reasoning = Column(Text)
    metadata = Column(JSONB)
    created_at = Column(DateTime(timezone=True), default=func.now())

    session = relationship("Session", back_populates="signals")

class AgentBelief(Base):
    __tablename__ = "agent_beliefs"
    agent_name = Column(String(100), primary_key=True)
    pool_name = Column(Enum(AgentPool), nullable=False)
    alpha = Column(Numeric(10, 4), default=1.0)
    beta = Column(Numeric(10, 4), default=1.0)
    total_sessions = Column(Integer, default=0)
    total_successes = Column(Integer, default=0)
    avg_confidence = Column(Numeric(5, 2), default=50.0)
    updated_at = Column(DateTime(timezone=True), default=func.now())

    @property
    def mean(self):
        return float(self.alpha) / (float(self.alpha) + float(self.beta))

class AgentBeliefHistory(Base):
    __tablename__ = "agent_belief_history"
    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_name = Column(String(100), nullable=False)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.session_id", ondelete="SET NULL"))
    prior_alpha = Column(Numeric(10, 4))
    prior_beta = Column(Numeric(10, 4))
    posterior_alpha = Column(Numeric(10, 4))
    posterior_beta = Column(Numeric(10, 4))
    was_selected = Column(Boolean)
    was_successful = Column(Boolean)
    created_at = Column(DateTime(timezone=True), default=func.now())

class AgentSelectionLog(Base):
    __tablename__ = "agent_selection_log"
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.session_id", ondelete="CASCADE"))
    agent_name = Column(String(100), nullable=False)
    pool_name = Column(Enum(AgentPool), nullable=False)
    was_called = Column(Boolean, nullable=False)
    success_flag = Column(Boolean)
    reward = Column(Numeric(10, 6))
    created_at = Column(DateTime(timezone=True), default=func.now())

class KARLDecisionRecord(Base):
    __tablename__ = "karl_decision_records"
    decision_id = Column(UUID(as_uuid=True), primary_key=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.session_id", ondelete="SET NULL"))
    symbol = Column(String(20))
    price = Column(Numeric(20, 8))
    timeframe = Column(String(20))
    regime = Column(Enum(VolatilityRegime))
    state_hash = Column(String(32))
    top_trajectories = Column(JSONB)
    selected_ensemble = Column(JSONB)
    q_values = Column(JSONB)
    q_star = Column(Numeric(8, 6))
    advantage = Column(Numeric(8, 6))
    uncertainty_aleatoric = Column(Numeric(6, 4))
    uncertainty_epistemic = Column(Numeric(6, 4))
    uncertainty_total = Column(Numeric(6, 4))
    confidence_raw = Column(Integer)
    confidence_final = Column(Integer)
    confidence_adjustments = Column(JSONB)
    final_action = Column(Enum(SignalDirection))
    position_pct = Column(Numeric(6, 4))
    kpi_snapshot = Column(JSONB)
    metadata = Column(JSONB)
    created_at = Column(DateTime(timezone=True), default=func.now())

    session = relationship("Session", back_populates="decisions")

class OAPValidationHistory(Base):
    __tablename__ = "oap_validation_history"
    id = Column(Integer, primary_key=True, autoincrement=True)
    decision_id = Column(UUID(as_uuid=True))
    status = Column(String(20))
    confidence = Column(Integer)
    position_pct = Column(Numeric(6, 4))
    confidence_boost = Column(Integer)
    regime = Column(Enum(VolatilityRegime))
    issues = Column(JSONB)
    created_at = Column(DateTime(timezone=True), default=func.now())

class KPIMetrics(Base):
    __tablename__ = "kpi_metrics"
    id = Column(Integer, primary_key=True, autoincrement=True)
    decision_id = Column(UUID(as_uuid=True))
    metric_name = Column(String(50), nullable=False)
    metric_value = Column(Numeric(12, 6))
    regime = Column(Enum(VolatilityRegime))
    created_at = Column(DateTime(timezone=True), default=func.now())

class RewardCalibration(Base):
    __tablename__ = "reward_calibration"
    id = Column(Integer, primary_key=True, autoincrement=True)
    n_bins = Column(Integer, default=10)
    slope = Column(Numeric(8, 6), default=1.0)
    intercept = Column(Numeric(8, 6), default=0.0)
    calibration_error = Column(Numeric(8, 6))
    fitted = Column(Boolean, default=False)
    updated_at = Column(DateTime(timezone=True), default=func.now())

class BacktestRun(Base):
    __tablename__ = "backtest_runs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.session_id", ondelete="SET NULL"))
    symbol = Column(String(20), nullable=False)
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    timeframe = Column(String(20))
    win_rate = Column(Numeric(5, 4))
    sharpe_ratio = Column(Numeric(8, 4))
    total_trades = Column(Integer)
    winning_trades = Column(Integer)
    losing_trades = Column(Integer)
    avg_win_pct = Column(Numeric(8, 4))
    avg_loss_pct = Column(Numeric(8, 4))
    total_return_pct = Column(Numeric(10, 4))
    max_drawdown_pct = Column(Numeric(10, 4))
    avg_confidence = Column(Numeric(5, 2))
    initial_capital = Column(Numeric(20, 8))
    final_capital = Column(Numeric(20, 8))
    created_at = Column(DateTime(timezone=True), default=func.now())

class RAGEmbedding(Base):
    __tablename__ = "rag_embeddings"
    id = Column(Integer, primary_key=True, autoincrement=True)
    chunk_id = Column(String(100), nullable=False)
    domain = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    embedding = Column(JSONB)
    metadata = Column(JSONB)
    created_at = Column(DateTime(timezone=True), default=func.now())

class AuditLog(Base):
    __tablename__ = "audit_log"
    id = Column(Integer, primary_key=True, autoincrement=True)
    table_name = Column(String(50), nullable=False)
    record_id = Column(UUID(as_uuid=True))
    action = Column(String(20), nullable=False)
    old_data = Column(JSONB)
    new_data = Column(JSONB)
    created_at = Column(DateTime(timezone=True), default=func.now())
