"""GitAgent CLI — export-agent, import-agent commands for MASFactory."""
import sys
import argparse
import asyncio
from pathlib import Path
from typing import Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from integrations.gitagent.adapters.gitagent_adapter import (
    GitAgentManifest,
    MASFactoryToGitAgentAdapter,
    GitAgentToMASFactoryAdapter,
    export_masfactory_to_gitagent,
    load_gitagent_as_masfactory,
)


def cmd_export_agent(args):
    """Export a MASFactory agent/Topology to GitAgent package."""
    output_dir = Path(args.output_dir) if args.output_dir else Path.cwd()
    
    # Import the actual topology from AstroFinSentinel
    try:
        from mas_factory.topology import Topology, Role, Connection
        from mas_factory.engine import ProductionMASEngine
    except ImportError as e:
        print(f"ERROR: Failed to import MASFactory: {e}")
        return 1
    
    # Build the topology from AstroCouncil agents
    topology = build_astrofin_topology(args.agents)
    
    # Export
    adapter = MASFactoryToGitAgentAdapter(args.package_name, str(output_dir))
    pkg_path = adapter.from_topology(topology)
    
    print(f"✅ Exported {len(args.agents)} agents to GitAgent package:")
    for agent in args.agents:
        print(f"   - {agent}")
    print(f"   Package: {pkg_path}")
    return 0


def cmd_import_agent(args):
    """Import a GitAgent package as MASFactory engine."""
    pkg_path = Path(args.package_path)
    if not pkg_path.exists():
        print(f"ERROR: Package path does not exist: {pkg_path}")
        return 1
    
    engine = load_gitagent_as_masfactory(str(pkg_path))
    if engine is None:
        print(f"❌ Failed to load GitAgent package: {pkg_path}")
        print("   (MASFactory may not be available)")
        return 1
    
    manifest = GitAgentManifest.from_yaml(pkg_path / "agent.yaml")
    print(f"✅ Loaded GitAgent package: {manifest.name}")
    print(f"   Version: {manifest.version}")
    print(f"   Description: {manifest.description}")
    print(f"   Sub-agents: {len(manifest.sub_agents or [])}")
    return 0


def cmd_roundtrip(args):
    """Test round-trip: export → import → verify."""
    import tempfile
    
    output_dir = Path(tempfile.mkdtemp())
    package_name = args.package_name or "test_roundtrip"
    
    # Export
    try:
        from mas_factory.topology import Topology, Role, Connection
        topology = build_astrofin_topology(args.agents if args.agents else DEFAULT_AGENTS)
        adapter = MASFactoryToGitAgentAdapter(package_name, str(output_dir))
        pkg_path = adapter.from_topology(topology)
    except Exception as e:
        print(f"❌ Export failed: {e}")
        return 1
    
    # Import
    engine = load_gitagent_as_masfactory(str(pkg_path))
    if engine is None:
        print(f"❌ Import failed")
        return 1
    
    manifest = GitAgentManifest.from_yaml(pkg_path / "agent.yaml")
    original_roles = set(args.agents if args.agents else DEFAULT_AGENTS)
    imported_roles = set(manifest.sub_agents or [])
    
    if original_roles == imported_roles:
        print(f"✅ Round-trip PASSED")
        print(f"   Original: {sorted(original_roles)}")
        print(f"   Imported: {sorted(imported_roles)}")
        return 0
    else:
        print(f"❌ Round-trip FAILED: mismatch")
        print(f"   Original: {sorted(original_roles)}")
        print(f"   Imported: {sorted(imported_roles)}")
        return 1


# Default 4 key agents for AstroFin
DEFAULT_AGENTS = [
    "AstroCouncil",
    "FundamentalAgent",
    "QuantAgent",
    "MacroAgent",
    "AstroCouncil",  # Synthesis is the orchestrator
]


def build_astrofin_topology(agent_names: list) -> 'Topology':
    """Build a MASFactory Topology from agent names."""
    from mas_factory.topology import Topology, Role, Connection
    
    # Import actual agent classes
    try:
        from agents._impl.astro_council import AstroCouncilAgent
        from agents._impl.fundamental_agent import FundamentalAgent
        from agents._impl.quant_agent import QuantAgent
        from agents._impl.macro_agent import MacroAgent
        from agents._impl.synthesis_agent import SynthesisAgent
    except ImportError:
        pass
    
    roles = []
    connections = []
    
    for name in agent_names:
        weight_map = {
            "AstroCouncil": 0.20,
            "FundamentalAgent": 0.12,
            "QuantAgent": 0.10,
            "MacroAgent": 0.08,
            "SynthesisAgent": 0.0,  # orchestrator
        }
        
        role = Role(
            name=name,
            agent_type=name,
            weight=weight_map.get(name, 0.1),
            capabilities=[f"analyze_{name.lower()}"],
            inputs=["market_state"],
            outputs=["signal"],
            timeout_ms=30000,
        )
        roles.append(role)
    
    # Connect all to synthesis
    for name in agent_names:
        if name != "SynthesisAgent":
            connections.append(Connection(from_node=name, to_node="SynthesisAgent"))
    
    # Input router
    connections.append(Connection(from_node="input", to_node="SynthesisAgent"))
    # Exit
    connections.append(Connection(from_node="SynthesisAgent", to_node="end"))
    
    topology = Topology(
        intention="AstroFin Sentinel V5 Multi-Agent Analysis",
        symbol="BTCUSDT",
        timeframe="SWING",
        version="5.0",
        roles=roles,
        connections=connections,
        entry_point="input",
        exit_point="end",
        metadata={
            "description": "AstroFin Sentinel V5 with KARL-AMRE loop and GitAgent export",
            "author": "AstroFin Team",
            "exported_from": "MASFactory",
        },
    )
    
    return topology


def main():
    parser = argparse.ArgumentParser(description="GitAgent CLI for MASFactory")
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # export-agent
    export_parser = subparsers.add_parser("export-agent", help="Export MASFactory agents to GitAgent")
    export_parser.add_argument("agents", nargs="+", help="Agent names to export")
    export_parser.add_argument("--package-name", "-n", default="astrofin_agents", help="Package name")
    export_parser.add_argument("--output-dir", "-o", help="Output directory")
    export_parser.set_defaults(func=cmd_export_agent)
    
    # import-agent
    import_parser = subparsers.add_parser("import-agent", help="Import GitAgent package to MASFactory")
    import_parser.add_argument("package_path", help="Path to GitAgent package")
    import_parser.set_defaults(func=cmd_import_agent)
    
    # roundtrip
    roundtrip_parser = subparsers.add_parser("roundtrip", help="Test export → import → verify")
    roundtrip_parser.add_argument("--package-name", "-n", default="test_roundtrip", help="Package name")
    roundtrip_parser.add_argument("--agents", nargs="+", help="Agent names (default: 4 key agents)")
    roundtrip_parser.set_defaults(func=cmd_roundtrip)
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        return 0
    
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
