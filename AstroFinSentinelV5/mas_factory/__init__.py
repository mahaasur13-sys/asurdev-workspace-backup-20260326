"""mas_factory/ - MAS Factory: Declarative Agent Architecture (ATOM-R-023a)

Modules:
    architect.py  - MASFactoryArchitect: generates topology.json from intention
    engine.py     - TopologyExecutor: runs agents from declarative blueprint
    topology.py   - Topology models (Role, Connection, SwitchNode, Adapter)
    adapters.py  - Context adapters between agents
    registry.py  - Agent registry with capabilities and constraints

Migration from SkillMD to MAS Factory:
    OLD: Hard-coded if/else in sentinel_v5.py
    NEW: Declarative topology.json + dynamic execution

Usage:
    from mas_factory import MASFactoryArchitect, TopologyExecutor
    
    architect = MASFactoryArchitect()
    topology = await architect.build("Analyze BTC for swing trade")
    
    executor = TopologyExecutor(topology)
    result = await executor.run()
"""
from mas_factory.architect import MASFactoryArchitect, Intention
from mas_factory.topology import Topology, Role, Connection, SwitchNode, Adapter
from mas_factory.engine import TopologyExecutor
from mas_factory.registry import AgentRegistry, get_registry

__all__ = [
    "MASFactoryArchitect", "Intention",
    "Topology", "Role", "Connection", "SwitchNode", "Adapter",
    "TopologyExecutor",
    "AgentRegistry", "get_registry",
]


# Meta-Questioning Engine
def get_meta_questioning_engine():
    from agents._impl.amre.meta_questioning import MetaQuestioningEngine
    return MetaQuestioningEngine()


