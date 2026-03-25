"""
Agent registry for lazy loading
"""
from typing import Dict, Type, Optional, Callable
from dataclasses import dataclass

from ._impl.base_agent import BaseAgent


@dataclass
class AgentSpec:
    """Agent specification for registry"""
    cls: Type[BaseAgent]
    init_kwargs: dict
    description: str = ""


class AgentRegistry:
    """
    Registry for managing agent instances.
    Enables lazy loading and dependency injection.
    """
    
    _agents: Dict[str, AgentSpec] = {}
    _instances: Dict[str, BaseAgent] = {}
    
    @classmethod
    def register(
        cls,
        name: str,
        cls_type: Type[BaseAgent],
        init_kwargs: dict = None,
        description: str = ""
    ) -> Callable:
        """Decorator to register an agent"""
        def decorator(agent_cls: Type[BaseAgent]) -> Type[BaseAgent]:
            cls._agents[name] = AgentSpec(
                cls=agent_cls,
                init_kwargs=init_kwargs or {},
                description=description
            )
            return agent_cls
        return decorator
    
    @classmethod
    def get(cls, name: str) -> Optional[BaseAgent]:
        """Get agent instance, creating if needed"""
        if name not in cls._instances:
            if name not in cls._agents:
                return None
            spec = cls._agents[name]
            cls._instances[name] = spec.cls(**spec.init_kwargs)
        return cls._instances[name]
    
    @classmethod
    def list_agents(cls) -> Dict[str, str]:
        """List all registered agents"""
        return {
            name: spec.description 
            for name, spec in cls._agents.items()
        }
    
    @classmethod
    def reset(cls) -> None:
        """Clear all instances (for testing)"""
        cls._instances.clear()


# Decorator for easy registration
def register_agent(name: str, description: str = "", **init_kwargs):
    """Register agent with registry"""
    def decorator(cls: Type[BaseAgent]) -> Type[BaseAgent]:
        AgentRegistry._agents[name] = AgentSpec(
            cls=cls,
            init_kwargs=init_kwargs,
            description=description
        )
        return cls
    return decorator
