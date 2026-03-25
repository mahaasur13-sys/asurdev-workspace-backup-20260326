"""
Configuration settings for asurdev Sentinel v3.2
==================================================

Unified settings using pydantic-settings v2.
Supports environment variables with asurdev_ prefix.

Based on best practices from asurdev-sentinel (P2).
"""

from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from typing import Literal
import os


class Settings(BaseSettings):
    """Main settings for asurdev Sentinel v3.2"""

    # Project paths
    project_root: Path = Field(default_factory=lambda: Path(__file__).parent.parent)
    data_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent / "data")

    # LLM Providers
    llm_provider: Literal["auto", "openai", "anthropic", "ollama"] = "auto"
    openai_model: str = "gpt-4o"
    anthropic_model: str = "claude-sonnet-4-20250514"
    
    # Ollama settings
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen3-coder:32b"
    ollama_temperature: float = 0.7

    # Agent settings
    max_debate_rounds: int = 4
    analyst_temperature: float = 0.7
    astrologer_temperature: float = 0.5
    synthesizer_temperature: float = 0.3

    # Board of Directors settings
    board_mode: Literal["round_robin", "debate"] = "debate"
    include_astrology: bool = True
    include_risk_manager: bool = True

    # Astro settings
    ephemeris_path: str = "/tmp/ephe"
    default_location: tuple[float, float] = (55.7558, 37.6173)
    house_system: str = "P"  # Placidus

    # Market data
    yf_interval: str = "1d"
    yf_period: str = "3mo"
    news_limit: int = 20

    # RAG settings
    rag_enabled: bool = True
    chroma_persist_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent / "data" / "chroma")

    # API settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # API keys (set via environment)
    openai_api_key: str | None = Field(default=None, validation_alias="OPENAI_API_KEY")
    anthropic_api_key: str | None = Field(default=None, validation_alias="ANTHROPIC_API_KEY")
    alpha_vantage_key: str | None = None

    @field_validator("openai_api_key", mode="before")
    @classmethod
    def get_openai_key(cls, v):
        return v or os.environ.get("asurdev_OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY")

    @field_validator("anthropic_api_key", mode="before")
    @classmethod
    def get_anthropic_key(cls, v):
        return v or os.environ.get("asurdev_ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")

    class Config:
        env_prefix = "asurdev_"
        env_file = ".env"


# Singleton instance
settings = Settings()
