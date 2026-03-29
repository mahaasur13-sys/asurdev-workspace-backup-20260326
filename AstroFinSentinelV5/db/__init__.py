"""db/ - AstroFin V5 Database Layer (ATOM-019 + ATOM-020)

Modules:
    init.py         - ATOM-020: Auto-create tables on first run
    session.py      - PostgreSQL connection pooling + scoped sessions
    models.py       - SQLAlchemy 2.0 models
    repositories.py - CRUD operations for all entities
    karl_replay.py - PostgresReplayBuffer (KARL trajectories)
    safe_json.py   - Safe JSON/JSONL operations (SQLite fallback)
"""
from db.session import get_engine, pg_session, is_postgres_available, get_db_stats
from db.init import init_db_if_needed, init_schema_if_needed
from db.repositories import (
    DecisionRecordRepository,
    AgentSignalRepository,
    AstroPositionRepository,
    AuditLogRepository,
    get_all_stats,
)
from db.karl_replay import PostgresReplayBuffer, get_default_pg_buffer

__all__ = [
    # Session
    "get_engine", "pg_session", "is_postgres_available", "get_db_stats",
    # Init
    "init_db_if_needed", "init_schema_if_needed",
    # Repositories
    "DecisionRecordRepository", "AgentSignalRepository",
    "AstroPositionRepository", "AuditLogRepository", "get_all_stats",
    # KARL Replay
    "PostgresReplayBuffer", "get_default_pg_buffer",
]
