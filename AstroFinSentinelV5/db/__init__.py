"""db/ - Database connection and utilities for AstroFin V5"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from contextlib import contextmanager

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://astrofin:astrofin_secret@localhost:5432/astrofin"
)

engine = create_engine(DATABASE_URL, pool_size=10, max_overflow=20, echo=False)
Session = scoped_session(sessionmaker(bind=engine))

@contextmanager
def get_session():
    session = Session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.remove()

def init_db():
    """Initialize database connection."""
    from .models import Base
    Base.metadata.create_all(engine)

__all__ = ["engine", "Session", "get_session", "init_db"]
