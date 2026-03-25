# Core package
from .config import settings, get_settings

# Lazy imports for database (requires asyncpg)
def _lazy_db_imports():
    from .database import get_db, init_db, close_db, AlertRecord, NotificationLog
    return get_db, init_db, close_db, AlertRecord, NotificationLog

__all__ = [
    "settings",
    "get_settings",
]
