"""
Structured Logging Configuration for AstroFin Sentinel.

Provides consistent, auditable logging across all agents and components.
"""

from __future__ import annotations

import sys
import logging
from typing import Any, Dict
from datetime import datetime

import structlog
from structlog.types import Processor


def setup_logging(
    level: str = "INFO",
    json_logs: bool = False,
    log_dir: str = "/dev/shm"
) -> None:
    """
    Configure structlog for AstroFin Sentinel.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR)
        json_logs: Output JSON format for production
        log_dir: Directory for log files
    """
    
    # Shared processors for all loggers
    shared_processors: list[Processor] = [
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(
            fmt="iso",
            utc=True,
        ),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]
    
    if json_logs:
        # JSON output for production
        shared_processors.append(structlog.processors.JSONRenderer())
    else:
        # Pretty console output for development
        shared_processors.extend([
            structlog.processors.CallsiteParameterAdder(
                [
                    structlog.processors.CallsiteParameter.FILENAME,
                    structlog.processors.CallsiteParameter.FUNC_NAME,
                    structlog.processors.CallsiteParameter.LINENO,
                ]
            ),
            structlog.dev.ConsoleRenderer(
                 colors=True,
                 exception_formatter=structlog.dev.plain_traceback,
            ),
        ])
    
    # Configure structlog
    structlog.configure(
        processors=shared_processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, level.upper()),
    )
    
    # Set specific log levels for noisy libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


def get_logger(name: str, **kwargs: Any) -> structlog.stdlib.BoundLogger:
    """
    Get a configured structlog logger.
    
    Usage:
        logger = get_logger(__name__)
        logger.info("event", key="value")
    """
    return structlog.get_logger(name, **kwargs)


class AuditLogger:
    """
    Special logger for audit events.
    
    All agent decisions, trading signals, and safety events are logged here.
    """
    
    def __init__(self, service_name: str = "astrofin"):
        self.service_name = service_name
        self.logger = get_logger(f"audit.{service_name}")
        self._event_count = 0
    
    def log_agent_decision(
        self,
        agent_name: str,
        signal: str,
        confidence: float,
        reasoning: str,
        context: Dict[str, Any],
        duration_ms: float,
    ) -> None:
        """Log an agent's trading decision."""
        self._event_count += 1
        self.logger.info(
            "agent_decision",
            event_id=self._event_count,
            agent=agent_name,
            signal=signal,
            confidence=confidence,
            reasoning_hash=hash(reasoning) % 10**10,
            context_keys=list(context.keys()),
            duration_ms=round(duration_ms, 2),
        )
    
    def log_trading_signal(
        self,
        symbol: str,
        direction: str,
        confidence: float,
        entry_price: float,
        stop_loss: float,
        targets: list[float],
        position_size: float,
        council_votes: list[Dict[str, Any]],
    ) -> None:
        """Log a final trading signal."""
        self.logger.warning(
            "trading_signal",
            event_id=self._event_count,
            symbol=symbol,
            direction=direction,
            confidence=confidence,
            entry_price=entry_price,
            stop_loss=stop_loss,
            targets=targets,
            position_size=position_size,
            vote_count=len(council_votes),
            risk_reward=self._calc_rr(entry_price, stop_loss, targets, direction),
        )
    
    def log_safety_event(
        self,
        event_type: str,
        description: str,
        blocked: bool,
        agent_name: str = None,
        details: Dict[str, Any] = None,
    ) -> None:
        """Log a safety/guardrails event."""
        self.logger.warning(
            "safety_event",
            event_id=self._event_count,
            safety_event_type=event_type,
            description=description,
            blocked=blocked,
            agent=agent_name,
            details=details or {},
        )
    
    def log_api_request(
        self,
        endpoint: str,
        method: str,
        status_code: int,
        duration_ms: float,
        user_id: str = None,
    ) -> None:
        """Log an API request."""
        self.logger.info(
            "api_request",
            event_id=self._event_count,
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            duration_ms=round(duration_ms, 2),
            user_id_hash=hash(user_id) % 10**10 if user_id else None,
        )
    
    def log_data_fetch(
        self,
        source: str,
        endpoint: str,
        cached: bool,
        duration_ms: float,
        record_count: int = None,
    ) -> None:
        """Log external data fetch."""
        self.logger.info(
            "data_fetch",
            event_id=self._event_count,
            source=source,
            endpoint=endpoint,
            cached=cached,
            duration_ms=round(duration_ms, 2),
            record_count=record_count,
        )
    
    def _calc_rr(
        self,
        entry: float,
        stop: float,
        targets: list[float],
        direction: str,
    ) -> float:
        """Calculate risk-reward ratio."""
        if direction == "LONG":
            risk = entry - stop
            reward = targets[-1] - entry if targets else 0
        else:
            risk = stop - entry
            reward = entry - targets[-1] if targets else 0
        
        return round(reward / risk, 2) if risk > 0 else 0.0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get audit statistics."""
        return {
            "total_events": self._event_count,
            "service": self.service_name,
        }


# Global audit logger
audit_logger = AuditLogger()


# Pre-configured loggers for common components
AGENT_LOGGER = get_logger("agents")
API_LOGGER = get_logger("api")
TRADE_LOGGER = get_logger("trading")
SAFETY_LOGGER = get_logger("safety")
DATA_LOGGER = get_logger("data")
