"""db/init.py - ATOM-020: Auto-create tables on first run"""
import logging
from db.session import get_engine, is_postgres_available
from db.models import Base
from alembic.config import Config
from alembic import command

logger = logging.getLogger(__name__)

def init_schema_if_needed() -> bool:
    """Create all tables if they don't exist. Returns True if successful."""
    if not is_postgres_available():
        logger.warning("[DB-INIT] PostgreSQL not available, skipping schema init")
        return False
    try:
        engine = get_engine()
        # Check if tables exist
        from sqlalchemy import inspect
        inspector = inspect(engine)
        existing = inspector.get_table_names()
        if existing:
            logger.info(f"[DB-INIT] Tables already exist: {len(existing)} tables")
            return True
        # Create all tables
        Base.metadata.create_all(engine)
        logger.info("[DB-INIT] Created all tables successfully")
        return True
    except Exception as e:
        logger.error(f"[DB-INIT] Failed to create tables: {e}")
        return False

def init_with_alembic(alembic_cfg_path: str = "alembic.ini") -> bool:
    """Run Alembic upgrade head for proper migrations."""
    if not is_postgres_available():
        return False
    try:
        cfg = Config(alembic_cfg_path)
        command.upgrade(cfg, "head")
        logger.info("[DB-INIT] Alembic upgrade completed")
        return True
    except Exception as e:
        logger.warning(f"[DB-INIT] Alembic failed (using Base.create_all): {e}")
        return init_schema_if_needed()

def init_db_if_needed() -> dict:
    """Main entry point - init DB and return status."""
    result = {
        "postgres_available": is_postgres_available(),
        "tables_created": False,
        "error": None,
    }
    if result["postgres_available"]:
        result["tables_created"] = init_schema_if_needed()
    else:
        logger.info("[DB-INIT] Skipped - no PostgreSQL connection")
    return result
