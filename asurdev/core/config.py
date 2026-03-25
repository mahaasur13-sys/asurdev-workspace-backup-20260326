"""
Core configuration for asurdev Sentinel
"""
from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path


@dataclass
class OllamaConfig:
    """Ollama LLM configuration"""
    base_url: str = "http://localhost:11434"
    default_model: str = "qwen2.5-coder:32b"
    timeout: int = 120


@dataclass
class DeviceConfig:
    """Device network configuration"""
    core_pc: str = "192.168.10.10"
    rk3576: str = "192.168.20.40"
    postgres_host: str = "192.168.10.20"
    postgres_port: int = 5432


@dataclass
class AstroConfig:
    """Astrology settings"""
    latitude: float = 53.1955  # Самара, Россия
    longitude: float = 50.1017
    timezone: str = "Europe/Samara"


@dataclass
class PathsConfig:
    """File paths"""
    ts_signals: str = "/home/workspace/asurdevSentinel/data/ts_signals"
    ts_export: str = "/home/workspace/asurdevSentinel/data/ts_export"
    quality_db: str = "/home/workspace/asurdevSentinel/quality"


@dataclass
class SentinelConfig:
    """Main configuration"""
    ollama: OllamaConfig = field(default_factory=OllamaConfig)
    device: DeviceConfig = field(default_factory=DeviceConfig)
    astro: AstroConfig = field(default_factory=AstroConfig)
    paths: PathsConfig = field(default_factory=PathsConfig)
    
    # Feature flags
    enable_cycle_agent: bool = True
    enable_quality_logging: bool = True
    
    @classmethod
    def from_env(cls) -> "SentinelConfig":
        """Create config from environment variables"""
        import os
        return cls(
            ollama=OllamaConfig(
                base_url=os.getenv("OLLAMA_URL", "http://localhost:11434"),
                default_model=os.getenv("OLLAMA_MODEL", "qwen2.5-coder:32b"),
            ),
            device=DeviceConfig(
                core_pc=os.getenv("CORE_PC", "192.168.10.10"),
                rk3576=os.getenv("RK3576", "192.168.20.40"),
            )
        )


# Global config instance
_config: Optional[SentinelConfig] = None


def get_config() -> SentinelConfig:
    """Get global config, creating if needed"""
    global _config
    if _config is None:
        _config = SentinelConfig()
    return _config


def set_config(config: SentinelConfig) -> None:
    """Set global config"""
    global _config
    _config = config
