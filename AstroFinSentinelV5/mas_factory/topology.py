"""mas_factory/topology.py - Declarative topology models"""
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional, Callable
from enum import Enum
import hashlib, json

class NodeType(Enum):
    AGENT = "agent"
    SWITCH = "switch"
    MERGE = "merge"
    ROUTER = "router"
    ADAPTER = "adapter"
    END = "end"

class SwitchStrategy(Enum):
    THOMPSON = "thompson"
    GREEDY = "greedy"
    ROUND_ROBIN = "round_robin"
    CONFIDENCE_WEIGHTED = "confidence_weighted"

@dataclass
class Adapter:
    """Context adapter between agents"""
    source: str
    target: str
    transform: str  # "passthrough" | "extract_signal" | "merge_confidences"
    field_mapping: Dict[str, str] = field(default_factory=dict)
    
    def apply(self, data: Any) -> Any:
        if self.transform == "passthrough":
            return data
        elif self.transform == "extract_signal":
            if isinstance(data, dict):
                return {k: data.get(k) for k in ["signal", "confidence", "reasoning"]}
            return data
        elif self.transform == "merge_confidences":
            if isinstance(data, list):
                signals = [d.get("signal", "NEUTRAL") for d in data if isinstance(d, dict)]
                confs = [d.get("confidence", 50) for d in data if isinstance(d, dict)]
                return {"signal": signals[0] if signals else "NEUTRAL",
                        "confidence": sum(confs) / len(confs) if confs else 50}
            return data
        return data

@dataclass
class SwitchNode:
    """Conditional routing node"""
    id: str
    strategy: SwitchStrategy = SwitchStrategy.THOMPSON
    condition: Optional[str] = None  # e.g., "confidence > 70"
    candidates: List[str] = field(default_factory=list)  # agent names
    k: int = 3  # select top-k
    weights: Optional[Dict[str, float]] = None
    
    def decide(self, context: Dict[str, Any]) -> List[str]:
        if self.strategy == SwitchStrategy.THOMPSON:
            # Thompson sampling - TODO: integrate with belief tracker
            import random
            scores = {a: random.random() * (self.weights.get(a, 1.0)) for a in self.candidates}
            sorted_agents = sorted(scores.items(), key=lambda x: x[1], reverse=True)
            return [a for a, _ in sorted_agents[:self.k]]
        elif self.strategy == SwitchStrategy.GREEDY:
            return self.candidates[:self.k]
        elif self.strategy == SwitchStrategy.CONFIDENCE_WEIGHTED:
            scores = {a: self.weights.get(a, 1.0) for a in self.candidates}
            return sorted(scores.items(), key=lambda x: x[1], reverse=True)[:self.k]
        return self.candidates[:self.k]

@dataclass
class Role:
    """Agent role definition"""
    name: str
    agent_type: str  # e.g., "FundamentalAgent", "AstroCouncil"
    weight: float = 0.1
    constraints: Dict[str, Any] = field(default_factory=dict)
    # Capability tags for dynamic matching
    capabilities: List[str] = field(default_factory=list)
    inputs: List[str] = field(default_factory=list)  # what this role expects
    outputs: List[str] = field(default_factory=list)  # what this role produces
    timeout_ms: int = 30000

@dataclass
class Connection:
    """Directed edge in topology"""
    from_node: str
    to_node: str
    adapter: Optional[Adapter] = None
    condition: Optional[str] = None  # e.g., "signal != NEUTRAL"

@dataclass


@dataclass
class Message:
    from_node: str
    to_node: str
    payload: Any
    timestamp: str

@dataclass
class Topology:
    """Declarative agent topology blueprint"""
    intention: str
    symbol: str
    timeframe: str
    version: str = "1.0"
    roles: List[Role] = field(default_factory=list)
    connections: List[Connection] = field(default_factory=list)
    switch_nodes: List[SwitchNode] = field(default_factory=list)
    entry_point: str = "router"
    exit_point: str = "synthesis"
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_role(self, name: str) -> Optional[Role]:
        for r in self.roles:
            if r.name == name:
                return r
        return None
    
    def get_outgoing(self, node: str) -> List[Connection]:
        return [c for c in self.connections if c.from_node == node]
    
    @property
    def hash(self) -> str:
        return self.compute_hash()

    def validate(self) -> List[str]:
        errors = []
        node_ids = {r.name for r in self.roles} | {s.id for s in self.switch_nodes}
        special_nodes = {"input", "end"}
        for c in self.connections:
            if c.from_node not in node_ids and c.from_node not in special_nodes:
                errors.append(f"Connection from unknown node: {c.from_node}")
            if c.to_node not in node_ids and c.to_node not in special_nodes:
                errors.append(f"Connection to unknown node: {c.to_node}")
        if self.entry_point not in node_ids and self.entry_point not in special_nodes:
            errors.append(f"Entry point not in topology: {self.entry_point}")
        return errors
    
    def compute_hash(self) -> str:
        data = json.dumps({
            "intention": self.intention,
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "roles": sorted([r.name for r in self.roles]),
            "version": self.version,
        }, sort_keys=True)
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    def to_dict(self) -> dict:
        d = asdict(self)
        d["_hash"] = self.compute_hash()
        return d
    
    @classmethod
    def from_dict(cls, data: dict) -> "Topology":
        data.pop("_hash", None)
        return cls(**data)

    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Quick local execution (for testing)"""
        from mas_factory.engine import TopologyExecutor
        executor = TopologyExecutor(self)
        return executor.run_sync(context)
