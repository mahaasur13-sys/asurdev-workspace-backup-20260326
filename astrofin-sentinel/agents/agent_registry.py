"""
Agent Registry — центральный реестр всех агентов AstroFin Sentinel.

Все 11 агентов системы:
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
"""

from typing import Type, Dict, List, Optional
from .base import BaseAgent, AgentInput, AgentOutput
from .technical_analyst import TechnicalAnalyst
from .directional_agents import BullResearcher, BearResearcher, DebateModerator
from .cycle_agent import CycleAgent, GannAgent, ElliotAgent, BradleyAgent
from .astro_council import AstroCouncil, SentimentAgent
from .risk_agent import RiskAgent, TimeWindowAgent
from .synthesis_engine import SynthesisEngine
import logging

logger = logging.getLogger(__name__)


# Registry — все агенты системы
AGENTS_REGISTRY: Dict[str, Type[BaseAgent]] = {
    # Core Agents
    "MarketAnalyst": TechnicalAnalyst,
    "BullResearcher": BullResearcher,
    "BearResearcher": BearResearcher,
    "DebateModerator": DebateModerator,
    
    # Cycle & Timing Agents
    "CycleAgent": CycleAgent,
    "GannAgent": GannAgent,
    "ElliotAgent": ElliotAgent,
    "BradleyAgent": BradleyAgent,
    
    # Astro & Sentiment Agents
    "AstroCouncil": AstroCouncil,
    "SentimentAgent": SentimentAgent,
    
    # Risk & Execution Agents
    "RiskAgent": RiskAgent,
    "TimeWindowAgent": TimeWindowAgent,
    
    # Synthesis
    "SynthesisEngine": SynthesisEngine,
}


class AgentFactory:
    """
    Фабрика агентов — создаёт и кэширует экземпляры агентов.
    """
    
    _instances: Dict[str, BaseAgent] = {}
    
    @classmethod
    def get(cls, name: str, **kwargs) -> BaseAgent:
        """
        Получить агент по имени (с кэшированием).
        
        Args:
            name: Имя агента из реестра
            **kwargs: Дополнительные параметры для конструктора
            
        Returns:
            Экземпляр агента
        """
        if name not in AGENTS_REGISTRY:
            raise ValueError(f"Unknown agent: {name}. Available: {list(AGENTS_REGISTRY.keys())}")
        
        # Кэшированный экземпляр
        cache_key = f"{name}_{id(kwargs)}"
        if cache_key not in cls._instances:
            agent_class = AGENTS_REGISTRY[name]
            cls._instances[cache_key] = agent_class(**kwargs)
            logger.info(f"[AgentFactory] Created new instance: {name}")
        
        return cls._instances[cache_key]
    
    @classmethod
    def get_all_agents(cls) -> Dict[str, Type[BaseAgent]]:
        """Возвращает полный реестр агентов."""
        return AGENTS_REGISTRY.copy()
    
    @classmethod
    def list_agents(cls) -> List[str]:
        """Возвращает список имён всех агентов."""
        return list(AGENTS_REGISTRY.keys())


class AgentTeam:
    """
    Команда агентов — группа агентов для совместной работы.
    
    Может быть:
    - Quick Team: MarketAnalyst + BullResearcher + BearResearcher
    - Full Team: Все 11 агентов
    - Custom: Выбранные агенты
    """
    
    def __init__(self, agents: List[str] | None = None, mode: str = "full"):
        """
        Инициализирует команду агентов.
        
        Args:
            agents: Список имён агентов (или None для预定义)
            mode: 'quick' | 'full' | 'custom'
        """
        self.mode = mode
        self.agents: Dict[str, BaseAgent] = {}
        
        if mode == "quick":
            default_agents = ["MarketAnalyst", "BullResearcher", "BearResearcher"]
        elif mode == "full":
            default_agents = list(AGENTS_REGISTRY.keys())
        else:
            default_agents = agents or []
        
        for name in default_agents:
            try:
                self.agents[name] = AgentFactory.get(name)
            except ValueError as e:
                logger.warning(f"[AgentTeam] Skipping {name}: {e}")
    
    def get_agent(self, name: str) -> Optional[BaseAgent]:
        """Получить агент из команды."""
        return self.agents.get(name)
    
    def get_agents(self) -> List[BaseAgent]:
        """Получить всех агентов команды."""
        return list(self.agents.values())
    
    def get_names(self) -> List[str]:
        """Получить имена всех агентов в команде."""
        return list(self.agents.keys())


# Предопределённые команды
QUICK_TEAM = AgentTeam(mode="quick")
FULL_TEAM = AgentTeam(mode="full")
