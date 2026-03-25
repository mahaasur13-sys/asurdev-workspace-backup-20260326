"""
AstroFin Sentinel Agents — мультиагентная система для алгоритмической торговли.

11 агентов системы:
1. MarketAnalyst — технический анализ (OHLCV, RSI, MACD, Bollinger)
2. BullResearcher — бычий кейс
3. BearResearcher — медвежий кейс
4. CycleAgent — анализ циклов (Gann, Bradley, Fibonacci)
5. AstroCouncil — астрологический совет (Moon, Aspects, Muhurta)
6. GannAgent — методы Ганна
7. ElliotAgent — волны Эллиотта
8. BradleyAgent — модель Брэдли
9. SentimentAgent — анализ настроений
10. RiskAgent — управление рисками
11. TimeWindowAgent — временные окна

Usage:
    from agents import AgentFactory, AgentTeam
    
    # Создать агент
    analyst = AgentFactory.get("MarketAnalyst")
    
    # Создать команду
    team = AgentTeam(mode="quick")  # or mode="full"
"""

import sys
from pathlib import Path

# Add project root to path for tools import
_project_root = Path(__file__).parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

# Base classes
from .base import AgentInput, AgentOutput, BaseAgent

# Agent Registry & Factory
from .agent_registry import (
    AGENTS_REGISTRY,
    AgentFactory,
    AgentTeam,
    QUICK_TEAM,
    FULL_TEAM,
)

# Core Agents
from .technical_analyst import TechnicalAnalyst
from .directional_agents import BullResearcher, BearResearcher, DebateModerator

# Cycle & Timing Agents
from .cycle_agent import CycleAgent, GannAgent, ElliotAgent, BradleyAgent

# Astro & Sentiment Agents
from .astro_council import AstroCouncil, SentimentAgent

# Risk & Execution Agents
from .risk_agent import RiskAgent, TimeWindowAgent

# Synthesis
from .synthesis_engine import SynthesisEngine

# LangChain integration
from .langchain_agents import (
    LangChainAgent,
    LangChainMarketAnalyst,
    LangChainAstroAdvisor,
    LangChainSynthesisEngine,
    get_tools,
)

# Orchestrator
from .orchestrator import Orchestrator, Alert

__all__ = [
    # Base
    "AgentInput",
    "AgentOutput",
    "BaseAgent",
    
    # Registry
    "AGENTS_REGISTRY",
    "AgentFactory",
    "AgentTeam",
    "QUICK_TEAM",
    "FULL_TEAM",
    
    # Core Agents
    "TechnicalAnalyst",
    "BullResearcher",
    "BearResearcher",
    "DebateModerator",
    
    # Cycle Agents
    "CycleAgent",
    "GannAgent",
    "ElliotAgent",
    "BradleyAgent",
    
    # Astro Agents
    "AstroCouncil",
    "SentimentAgent",
    
    # Risk Agents
    "RiskAgent",
    "TimeWindowAgent",
    
    # Synthesis
    "SynthesisEngine",
    
    # LangChain
    "LangChainAgent",
    "LangChainMarketAnalyst",
    "LangChainAstroAdvisor",
    "LangChainSynthesisEngine",
    "get_tools",
    
    # Orchestrator
    "Orchestrator",
    "Alert",
]
