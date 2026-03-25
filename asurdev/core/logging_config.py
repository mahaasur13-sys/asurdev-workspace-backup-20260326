"""
logging_config.py — asurdev Sentinel v3.2
Настройка логирования БЕЗ PII (GDPR compliance)
"""
import logging
import logging.config
import json
from typing import Any
from datetime import datetime


class PIIFilter(logging.Filter):
    """
    Фильтр для удаления PII из логов.
    
    Удаляет:
        - Даты рождения (YYYY-MM-DD, DD/MM/YYYY)
        - Точные координаты (широта/долгота)
        - Имена пользователей
        - Email адреса
    
    Заменяет на: [REDACTED]
    """
    
    import re
    
    PII_PATTERNS = [
        # Даты
        (re.compile(r'\b\d{4}-\d{2}-\d{2}\b'), '[REDACTED_DATE]'),
        (re.compile(r'\b\d{2}/\d{2}/\d{4}\b'), '[REDACTED_DATE]'),
        (re.compile(r'\b\d{2}\.\d{2}\.\d{4}\b'), '[REDACTED_DATE]'),
        
        # Координаты (примерно)
        (re.compile(r'lat[:\s=]*[-+]?\d{1,3}\.\d{4,}'), 'lat=[REDACTED]'),
        (re.compile(r'lon[:\s=]*[-+]?\d{1,3}\.\d{4,}'), 'lon=[REDACTED]'),
        (re.compile(r'latitude[:\s=]*[-+]?\d{1,3}\.\d{4,}'), 'latitude=[REDACTED]'),
        (re.compile(r'longitude[:\s=]*[-+]?\d{1,3}\.\d{4,}'), 'longitude=[REDACTED]'),
        
        # Email
        (re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'), '[REDACTED_EMAIL]'),
        
        # Имена (первое слово с заглавной буквы, 3-20 букв)
        (re.compile(r'\b[A-Z][a-z]{2,19}\b'), '[REDACTED_NAME]'),
    ]
    
    def filter(self, record: logging.LogRecord) -> bool:
        if hasattr(record, 'msg') and isinstance(record.msg, str):
            record.msg = self._redact_pii(record.msg)
        
        if hasattr(record, 'args') and record.args:
            record.args = tuple(
                self._redact_pii(str(arg)) if isinstance(arg, str) else arg
                for arg in record.args
            )
        
        # Всегда добавляем timestamp в ISO формате (не PII)
        record.iso_timestamp = datetime.utcnow().isoformat() + "Z"
        
        return True
    
    def _redact_pii(self, text: str) -> str:
        for pattern, replacement in self.PII_PATTERNS:
            text = pattern.sub(replacement, text)
        return text


class StructuredLogFormatter(logging.Formatter):
    """
    Форматирует логи в JSON для удобного парсинга.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": getattr(record, 'iso_timestamp', datetime.utcnow().isoformat() + "Z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Добавляем extra fields
        if hasattr(record, 'request_hash'):
            log_data["request_hash"] = record.request_hash
        if hasattr(record, 'jd_ut'):
            log_data["jd_ut"] = record.jd_ut
        if hasattr(record, 'ayanamsa'):
            log_data["ayanamsa"] = record.ayanamsa
        if hasattr(record, 'agent'):
            log_data["agent"] = record.agent
        if hasattr(record, 'error'):
            log_data["error"] = str(record.error)
        
        # Добавляем exception info если есть
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data, ensure_ascii=False)


# Конфигурация логирования
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "pii_filtered": {
            "()": StructuredLogFormatter,
        },
        "simple": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "filters": {
        "pii_filter": {
            "()": PIIFilter,
        },
    },
    "handlers": {
        "console": {
            "class": logging.StreamHandler,
            "formatter": "simple",
            "filters": ["pii_filter"],
            "stream": "ext://sys.stdout",
        },
        "file": {
            "class": logging.handlers.RotatingFileHandler,
            "formatter": "pii_filtered",
            "filters": ["pii_filter"],
            "filename": "/tmp/asurdev_sentinel.log",
            "maxBytes": 10_485_760,  # 10 MB
            "backupCount": 5,
        },
        "audit_file": {
            "class": logging.handlers.RotatingFileHandler,
            "formatter": "pii_filtered",
            "filters": ["pii_filter"],
            "filename": "/tmp/asurdev_audit.log",
            "maxBytes": 10_485_760,
            "backupCount": 10,
        },
    },
    "loggers": {
        "asurdev": {
            "level": "DEBUG",
            "handlers": ["console", "file"],
            "propagate": False,
        },
        "asurdev.audit": {
            "level": "INFO",
            "handlers": ["audit_file"],
            "propagate": False,
        },
    },
    "root": {
        "level": "WARNING",
        "handlers": ["console"],
    },
}


def setup_logging():
    """Инициализирует логирование при импорте модуля."""
    import logging.config
    logging.config.dictConfig(LOGGING_CONFIG)


# Автоматическая инициализация при импорте
setup_logging()
