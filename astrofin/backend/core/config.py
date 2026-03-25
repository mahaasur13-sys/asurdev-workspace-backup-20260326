"""Backend configuration."""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings."""

    app_name: str = "AstroFin Sentinel"
    debug: bool = False

    # API Keys
    polygon_api_key: str = ""
    fred_api_key: str = ""
    coingecko_api_key: str = ""

    # Swiss Ephemeris
    swiss_ephemeris_path: str = "/home/workspace/astrofin/backend/ephe"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Agent settings
    default_risk_percentage: float = 0.02
    max_position_size: float = 0.10
    latency_target_ms: float = 650.0

    class Config:
        env_file = ".env"
        env_prefix = "ASTROFIN_"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
