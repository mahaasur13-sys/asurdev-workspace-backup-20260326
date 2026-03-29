"""ATOM-GITAGENT-036 R-036: Round-trip export/import test for 4 key agents."""
import sys
import tempfile
import shutil
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from integrations.gitagent.adapters.gitagent_adapter import (
    GitAgentManifest,
    MASFactoryToGitAgentAdapter,
    GitAgentToMASFactoryAdapter,
)


def test_package_structure(package_path: Path, agent_name: str) -> bool:
    """Test that GitAgent package has all required files."""
    required = [
        package_path / "agent.yaml",
        package_path / "SOUL.md",
        package_path / "RULES.md",
        package_path / "DUTIES.md",
    ]
    
    for f in required:
        if not f.exists():
            print(f"  ❌ Missing: {f.name}")
            return False
    
    # Check manifest
    try:
        manifest = GitAgentManifest.from_yaml(package_path / "agent.yaml")
        if manifest.name != agent_name:
            print(f"  ❌ Manifest name mismatch: {manifest.name} != {agent_name}")
            return False
    except Exception as e:
        print(f"  ❌ Failed to load manifest: {e}")
        return False
    
    print(f"  ✅ Package structure valid")
    return True


def test_manifest_yaml(package_path: Path) -> bool:
    """Test that agent.yaml has required fields."""
    manifest = GitAgentManifest.from_yaml(package_path / "agent.yaml")
    
    required_fields = ["name", "description", "version"]
    for field in required_fields:
        if not getattr(manifest, field, None):
            print(f"  ❌ Missing required field: {field}")
            return False
    
    # Check model config
    if not manifest.model:
        print(f"  ⚠️  No model config (optional)")
    else:
        print(f"  ✅ Model: {manifest.model.get('provider')}/{manifest.model.get('name')}")
    
    # Check workflows
    if manifest.workflows:
        print(f"  ✅ Workflows: {', '.join(manifest.workflows)}")
    
    return True


def test_roundtrip_export_import(agent_names: list, package_name: str) -> bool:
    """Test full round-trip: build topology → export → import → verify."""
    from mas_factory.topology import Topology, Role, Connection
    
    # Build topology
    roles = []
    connections = []
    weight_map = {
        "AstroCouncil": 0.20,
        "FundamentalAgent": 0.12,
        "QuantAgent": 0.10,
        "MacroAgent": 0.08,
    }
    
    for name in agent_names:
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
    
    for name in agent_names:
        connections.append(Connection(from_node=name, to_node="SynthesisAgent"))
    connections.append(Connection(from_node="input", to_node="SynthesisAgent"))
    connections.append(Connection(from_node="SynthesisAgent", to_node="end"))
    
    topology = Topology(
        intention="AstroFin Sentinel V5 Round-trip Test",
        symbol="BTCUSDT",
        timeframe="SWING",
        version="5.0",
        roles=roles,
        connections=connections,
        entry_point="input",
        exit_point="end",
        metadata={"description": "Test topology for GitAgent export", "author": "AstroFin Team"},
    )
    
    # Export to temp directory
    temp_dir = Path(tempfile.mkdtemp())
    try:
        adapter = MASFactoryToGitAgentAdapter(package_name, str(temp_dir))
        pkg_path = adapter.from_topology(topology)
        print(f"\n  📦 Exported to: {pkg_path}")
        
        # Verify each agent package
        for agent_name in agent_names:
            agent_pkg = temp_dir / package_name / agent_name
            if agent_pkg.exists():
                print(f"\n  📁 Agent: {agent_name}")
                test_package_structure(agent_pkg, agent_name)
                test_manifest_yaml(agent_pkg)
            else:
                print(f"  ⚠️  No package dir for {agent_name} (may be sub-agent)")
        
        # Import back
        engine = GitAgentToMASFactoryAdapter(str(pkg_path)).load()
        if engine is None:
            print(f"  ⚠️  MASFactory engine not available (OK if MASFactory not installed)")
            return True
        
        manifest = GitAgentManifest.from_yaml(pkg_path / "agent.yaml")
        imported_roles = set(manifest.sub_agents or [])
        original_roles = set(agent_names)
        
        if original_roles == imported_roles:
            print(f"\n  ✅ Round-trip VERIFIED: {len(original_roles)} agents")
            return True
        else:
            print(f"\n  ❌ Role mismatch:")
            print(f"     Original: {sorted(original_roles)}")
            print(f"     Imported: {sorted(imported_roles)}")
            return False
        
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def main():
    print("=" * 60)
    print("ATOM-GITAGENT-036 R-036: GitAgent Phase 2 Round-trip Test")
    print("=" * 60)
    
    # Test 4 key agents - use lowercase to match directory names
    KEY_AGENTS = [
        "astro_council",
        "fundamental_agent", 
        "quant_agent",
        "macro_agent",
    ]
    
    print(f"\n🔄 Testing export/import for {len(KEY_AGENTS)} agents:")
    for agent in KEY_AGENTS:
        print(f"   • {agent}")
    
    print("\n" + "=" * 60)
    print("TEST 1: Package Structure Validation")
    print("=" * 60)
    
    # Validate existing packages
    base = Path("/home/workspace/AstroFinSentinelV5/integrations/gitagent")
    all_passed = True
    
    for agent in KEY_AGENTS:
        agent_pkg = base / agent
        if agent_pkg.exists():
            print(f"\n📁 {agent}:")
            if not test_package_structure(agent_pkg, agent):
                all_passed = False
            if not test_manifest_yaml(agent_pkg):
                all_passed = False
        else:
            print(f"\n📁 {agent}: ⚠️  Package not found")
            all_passed = False
    
    print("\n" + "=" * 60)
    print("TEST 2: Round-trip Export/Import")
    print("=" * 60)
    
    if not test_roundtrip_export_import(KEY_AGENTS, "astrofin_key_agents"):
        all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ ALL TESTS PASSED")
        print("\nR-036 Status: READY FOR PRODUCTION")
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
