"""
Конфигурация AstroFin Sentinel.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Настройки приложения."""
    
    # === FastAPI ===
    APP_NAME: str = "AstroFin Sentinel"
    VERSION: str = "4.1.0"
    DEBUG: bool = False
    
    # === Database ===
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/astrofin"
    
    # === TradingView Webhook ===
    TRADINGVIEW_SECRET: str = ""
    WEBHOOK_PORT: int = 8000
    WEBHOOK_HOST: str = "0.0.0.0"
    
    # === Ollama LLM (GreenBoost RTX 3060 12GB) ===
    # Модели для разных ролей:
    # - synthesis: 70B для сложного синтеза (Q4_K_M ~40GB, не влезет в 12GB)
    # - analyst: 32B Q4_K_M ~20GB,勉强 fits
    # - astro: 7B Q4_K_M ~4GB, легко
    
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    
    # Primary model for agents
    # Note: Current VM has only 2.7GB free RAM - use tinyllama
    # For full 32B models, use a machine with 32GB+ RAM
    OLLAMA_MODEL: str = "tinyllama:1.1b"
    
    # Models by role
    ANALYST_MODEL: str = "tinyllama:1.1b"
    ASTRO_MODEL: str = "tinyllama:1.1b"
    SYNTHESIS_MODEL: str = "tinyllama:1.1b"
    
    # === Ollama Generation Settings ===
    OLLAMA_TEMPERATURE: float = 0.3      # Lower for analytical
    OLLAMA_NUM_PREDICT: int = 256        # Max tokens (tinyllama is fast, 256 is enough)
    OLLAMA_TIMEOUT: int = 60             # Timeout seconds (tinyllama is fast)
    
    # === Астрология ===
    EPHEMERIS_PATH: str = "./de421.bsp"  # Swiss Ephemeris data file
    DEFAULT_LATITUDE: float = 55.75      # Moscow
    DEFAULT_LONGITUDE: float = 37.62
    
    # === Telegram ===
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""
    
    # === Twilio SMS ===
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_FROM_NUMBER: str = ""
    TWILIO_TO_NUMBER: str = ""
    
    # === Notification Settings ===
    NOTIFY_TELEGRAM: bool = True
    NOTIFY_SMS: bool = False
    
    # === Логирование ===
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        extra = "allow"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
