"""mas_factory — ATOM-R-033: Production MAS Factory"""
from mas_factory.topology import (
    Role, SwitchNode, Connection, Topology,
    NodeType, SwitchStrategy, SwitchAction,
    TopologyChange, TopologyVersion, TopologyUpdater
)
from mas_factory.architect import MASFactoryArchitect, get_architect
from mas_factory.registry import AgentRegistry, get_registry

from mas_factory.engine import ProductionMASEngine, MASFactoryConfig, get_production_engine
from mas_factory.visualizer import TopologyVisualizer

__all__ = [
    "Role", "SwitchNode", "Connection", "Topology",
    "NodeType", "SwitchStrategy", "SwitchAction",
    "TopologyChange", "TopologyVersion", "TopologyUpdater",
    "MASFactoryArchitect", "get_architect",
    "AgentRegistry", "get_registry",
    "get_agent_runner",
    "ProductionMASEngine", "MASFactoryConfig", "get_production_engine",
    "TopologyVisualizer",
]
