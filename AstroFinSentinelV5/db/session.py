"""db/session.py — PostgreSQL Session Management (ATOM-019)
Singleton SQLAlchemy engine + scoped sessions.
"""
import os
from contextlib import contextmanager
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import QueuePool

_ENGINE = None
_Session = None

def get_database_url() -> str:
    return (
        f"postgresql://{os.getenv('POSTGRES_USER', 'astrofin')}:"
        f"{os.getenv('POSTGRES_PASSWORD', 'xxx')}@"
        f"{os.getenv('POSTGRES_HOST', 'localhost')}:"
        f"{os.getenv('POSTGRES_PORT', '5432')}/"
        f"{os.getenv('POSTGRES_DB', 'astrofin')}"
    )

def get_engine():
    global _ENGINE
    if _ENGINE is None:
        url = get_database_url()
        _ENGINE = create_engine(
            url,
            poolclass=QueuePool,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
            echo=bool(os.getenv('SQL_ECHO', '')),
        )
        @event.listens_for(_ENGINE, "connect")
        def set_search_path(dbapi_conn, connection_record):
            cursor = dbapi_conn.cursor()
            cursor.execute("SELECT set_config('app.search_path', 'public', FALSE)")
            cursor.close()
    return _ENGINE

def get_session_factory():
    global _Session
    if _Session is None:
        _Session = scoped_session(sessionmaker(bind=get_engine(), autoflush=False))
    return _Session

@contextmanager
def pg_session():
    """Context manager for PostgreSQL sessions."""
    session = get_session_factory()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

def is_postgres_available() -> bool:
    try:
        eng = get_engine()
        with eng.connect() as conn:
            conn.execute("SELECT 1")
        return True
    except Exception:
        return False

def get_db_stats() -> dict:
    """Connection pool stats for monitoring."""
    try:
        eng = get_engine()
        pool = eng.pool
        return {
            "size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "available": pool.available(),
        }
    except Exception as e:
        return {"error": str(e)}
