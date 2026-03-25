"""
Асинхронная база данных для AstroFin Sentinel.
Использует SQLAlchemy 2.0 + asyncpg для PostgreSQL.
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, String, Float, DateTime, Text, Integer, Boolean, JSON, Index
from datetime import datetime
from typing import AsyncGenerator
import logging

from core.config import settings

logger = logging.getLogger(__name__)

# === Async Engine ===

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    pass


# === Models ===

class AlertRecord(Base):
    """Запись TradingView Alert в БД."""
    
    __tablename__ = "alerts"
    
    id = Column(String(36), primary_key=True)  # UUID
    symbol = Column(String(20), nullable=False, index=True)
    action = Column(String(10), nullable=False)  # buy, sell, hold
    price = Column(Float, nullable=False)
    quantity = Column(Float, nullable=True)
    strategy = Column(String(50), nullable=True)
    timeframe = Column(String(10), nullable=True)
    ml_confidence = Column(Float, default=0.5)
    astro_signal = Column(Boolean, default=False)
    
    # Статус
    status = Column(String(20), default="pending", index=True)  # pending, processing, completed, failed
    error = Column(Text, nullable=True)
    
    # Временные метки
    received_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    processing_time_ms = Column(Float, nullable=True)
    
    # Сырые данные
    raw_data = Column(JSON, nullable=True)
    
    # Результаты агентов (JSON)
    tech_result = Column(JSON, nullable=True)
    astro_result = Column(JSON, nullable=True)
    synthesis_result = Column(JSON, nullable=True)
    
    # Нотификации
    telegram_sent = Column(Boolean, default=False)
    telegram_sent_at = Column(DateTime, nullable=True)
    sms_sent = Column(Boolean, default=False)
    sms_sent_at = Column(DateTime, nullable=True)
    
    __table_args__ = (
        Index("ix_alerts_received_at", "received_at"),
        Index("ix_alerts_symbol_status", "symbol", "status"),
    )


class NotificationLog(Base):
    """Лог отправленных уведомлений."""
    
    __tablename__ = "notification_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    alert_id = Column(String(36), nullable=False, index=True)
    channel = Column(String(20), nullable=False)  # telegram, sms
    status = Column(String(20), nullable=False)  # sent, failed
    response = Column(Text, nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# === Async Session Dependency ===

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency для FastAPI — предоставляет сессию БД."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# === Init DB ===

async def init_db():
    """Создаёт таблицы в БД."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created")


async def close_db():
    """Закрывает соединения с БД."""
    await engine.dispose()
    logger.info("Database connections closed")
