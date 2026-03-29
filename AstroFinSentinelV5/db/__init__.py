"""db/ — AstroFin V5 Database Layer (ATOM-019)

Modules:
    session.py       - PostgreSQL connection pooling + scoped sessions
    models.py        - SQLAlchemy 2.0 models
    repositories.py   - CRUD operations for all entities
    karl_replay.py   - PostgresReplayBuffer (KARL trajectories)
    safe_json.py     - Safe JSON/JSONL operations (SQLite fallback)
"""
from db.session import get_engine, pg_session, is_postgres_available, get_db_stats
from db.repositories import (
    DecisionRecordRepository,
    AgentSignalRepository,
    AstroPositionRepository,
    AuditLogRepository,
    get_all_stats,
)
from db.karl_replay import PostgresReplayBuffer, get_default_pg_buffer

__all__ = [
    "get_engine", "pg_session", "is_postgres_available", "get_db_stats",
    "DecisionRecordRepository", "AgentSignalRepository",
    "AstroPositionRepository", "AuditLogRepository", "get_all_stats",
    "PostgresReplayBuffer", "get_default_pg_buffer",
]
