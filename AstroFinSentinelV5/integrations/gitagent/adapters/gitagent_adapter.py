"""GitAgent Adapter — MASFactory ↔ GitAgent compatibility layer"""
from typing import Dict, List, Any, Optional
from pathlib import Path
import yaml
from dataclasses import dataclass, asdict

from mas_factory.topology import Role, SwitchNode, Topology
from mas_factory.engine import ProductionMASEngine as MASFactoryEngine

@dataclass
class GitAgentManifest:
    """GitAgent agent.yaml manifest"""
    name: str
    description: str
    version: str = "1.0.0"
    model: Optional[Dict[str, Any]] = None
    skills: Optional[List[str]] = None
    tools: Optional[List[str]] = None
    compliance: Optional[Dict[str, Any]] = None
    sub_agents: Optional[List[str]] = None
    workflows: Optional[List[str]] = None
    
    def to_yaml(self, path: Path):
        with open(path, 'w') as f:
            yaml.dump(asdict(self), f, default_flow_style=False)
    
    @classmethod
    def from_yaml(cls, path: Path) -> 'GitAgentManifest':
        with open(path) as f:
            data = yaml.safe_load(f) or {}
        return cls(**{k: v for k, v in data.items()})

class MASFactoryToGitAgentAdapter:
    """Convert MASFactory Topology → GitAgent package structure"""
    
    def __init__(self, package_name: str, package_path: str = "."):
        self.package_name = package_name
        self.package_path = Path(package_path)
    
    def from_topology(self, topology: Topology) -> Path:
        """Export MASFactory Topology as GitAgent package"""
        
        
        pkg = self.package_path / self.package_name
        pkg.mkdir(parents=True, exist_ok=True)
        (pkg / "sub_agents").mkdir(exist_ok=True)
        
        manifest = GitAgentManifest(
            name=self.package_name,
            description=topology.metadata.get("description", f"MASFactory topology: {topology.intention}"),
            version="1.0.0",
            sub_agents=[r.name for r in topology.roles],
            workflows=["synthesize", "route", "aggregate"],
        )
        manifest.to_yaml(pkg / "agent.yaml")
        
        soul = f"""# {topology.intention}

{topology.metadata.get("description", "MASFactory-based agent") or 'MASFactory-based agent.'}

## KARL Integration
- Uncertainty quantification enabled
- Meta-questioning enabled
- Self-improvement loop active
"""
        (pkg / "SOUL.md").write_text(soul)
        
        rules = """# RULES.md

## Core Rules
1. Always quantify uncertainty before reporting confidence
2. Apply AMRE validation to all decisions
3. Use KARL drift detection in production
4. Respect volatility regime guards
"""
        (pkg / "RULES.md").write_text(rules)
        
        duties = f"""# DUTIES.md

## Role: {topology.intention}

### Responsibilities
- Coordinate multi-agent synthesis
- Apply AMRE uncertainty estimation
- Generate DecisionRecords for audit trail
- Report confidence with proper guards
"""
        (pkg / "DUTIES.md").write_text(duties)
        
        for role in topology.roles:
            role_dir = pkg / "sub_agents" / role.name
            role_dir.mkdir(parents=True, exist_ok=True)
            skill_md = f"""# {role.name}

{role.capabilities or f'Agent role: {role.name}'}

## Output Schema
- signal: LONG | SHORT | NEUTRAL | AVOID
- confidence: 0-100
- reasoning: str
- sources: list
"""
            (role_dir / "SKILL.md").write_text(skill_md)
            (role_dir / "manifest.yaml").write_text(f"name: {role.name}\ntype: agent_role\n")
        
        return pkg

class GitAgentToMASFactoryAdapter:
    """Wrap GitAgent package as MASFactory engine"""
    
    def __init__(self, package_path: str):
        self.package_path = Path(package_path)
    
    def load(self) -> Optional['MASFactoryEngine']:
        """Load GitAgent package as MASFactory engine"""
        if not MASFACTORY:
            return None
        
        manifest = GitAgentManifest.from_yaml(self.package_path / "agent.yaml")
        
        roles = []
        sub_agents_dir = self.package_path / "sub_agents"
        if sub_agents_dir.exists():
            for role_dir in sorted(sub_agents_dir.iterdir()):
                if role_dir.is_dir():
                    skill_md = role_dir / "SKILL.md"
                    instructions = skill_md.read_text() if skill_md.exists() else ""
                    roles.append(Role(
                        name=role_dir.name,
                        agent_type=role_dir.name,
                        instructions=instructions,
                        input_schema={},
                        output_schema={},
                    ))
        
        nodes = []
        for agent_name in (manifest.sub_agents or []):
            nodes.append(Node(id=agent_name, type="agent", config={}))
        for wf_name in (manifest.workflows or []):
            nodes.append(SwitchNode(id=wf_name, type="switch", config={}, branches=[]))
        
        topology = Topology(
            name=manifest.name,
            instructions=manifest.description,
            roles=roles,
            nodes=nodes,
        )
        return MASFactoryEngine(topology)


def export_masfactory_to_gitagent(topology: 'Topology', output_dir: str, package_name: str) -> str:
    """Export MASFactory Topology as GitAgent package"""
    adapter = MASFactoryToGitAgentAdapter(package_name, output_dir)
    return str(adapter.from_topology(topology))

def load_gitagent_as_masfactory(package_dir: str) -> Optional['MASFactoryEngine']:
    """Load GitAgent package as MASFactory engine"""
    adapter = GitAgentToMASFactoryAdapter(package_dir)
    return adapter.load()
