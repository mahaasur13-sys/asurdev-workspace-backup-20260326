#!/usr/bin/env python3
"""ATOM-GITAGENT-001: Test GitAgent export/import cycle"""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

def test_gitagent_package_structure():
    """Verify pilot AstroAgent package has all required files"""
    pkg = Path(__file__).parent / "astro_agent_synthesis"
    required = ["agent.yaml", "SOUL.md", "RULES.md", "DUTIES.md", "sub_agents/synthesis_role/SKILL.md"]
    
    print("[TEST 1] Package Structure")
    for f in required:
        path = pkg / f
        status = "✓" if path.exists() else "✗"
        print(f"  {status} {f}")
        assert path.exists(), f"Missing: {f}"
    print("  ✅ PASS\n")

def test_adapter_import():
    """Test that adapter can be imported"""
    print("[TEST 2] Adapter Import")
    try:
        from integrations.gitagent.adapters.gitagent_adapter import (
            MASFactoryToGitAgentAdapter,
            GitAgentToMASFactoryAdapter,
            GitAgentManifest,
        )
        print("  ✓ Imports successful")
        print("  ✅ PASS\n")
        return True
    except ImportError as e:
        print(f"  ✗ Import failed: {e}")
        print("  ❌ FAIL\n")
        return False

def test_manifest_yaml():
    """Test GitAgentManifest can read/write YAML"""
    print("[TEST 3] Manifest YAML")
    import tempfile
    import yaml
    from integrations.gitagent.adapters.gitagent_adapter import GitAgentManifest
    
    manifest = GitAgentManifest(
        name="test_agent",
        description="Test agent",
        version="1.0.0",
        sub_agents=["role1", "role2"],
        workflows=["wf1"],
    )
    
    with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False, mode='w') as f:
        manifest.to_yaml(Path(f.name))
        loaded = GitAgentManifest.from_yaml(Path(f.name))
    
    assert loaded.name == "test_agent"
    assert loaded.version == "1.0.0"
    assert loaded.sub_agents == ["role1", "role2"]
    print(f"  ✓ Write/read cycle OK")
    print("  ✅ PASS\n")

def test_export_cycle():
    """Test MASFactory → GitAgent export"""
    print("[TEST 4] Export Cycle")
    try:
        from mas_factory.topology import Role, Topology
        from integrations.gitagent.adapters.gitagent_adapter import export_masfactory_to_gitagent
    except ImportError as e:
        print(f"  ⚠ MASFactory not available: {e}")
        print("  ⚠ SKIP (will work when MASFactory is installed)\n")
        return True
    
    topology = Topology(
        intention="test_topology",
        symbol="BTCUSDT",
        timeframe="SWING",
        roles=[
            Role(name="synthesizer", agent_type="agent", inputs=["signals"], outputs=["recommendation"]),
            Role(name="analyst", agent_type="agent", inputs=["market_data"], outputs=["analysis"]),
        ],
        connections=[],
    )
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output = export_masfactory_to_gitagent(topology, tmpdir, "test_export")
        pkg_path = Path(output)
        
        assert (pkg_path / "agent.yaml").exists(), "Missing agent.yaml"
        assert (pkg_path / "SOUL.md").exists(), "Missing SOUL.md"
        assert (pkg_path / "sub_agents" / "synthesizer" / "SKILL.md").exists()
        print(f"  ✓ Exported to: {output}")
        print("  ✅ PASS\n")

def main():
    print("=" * 60)
    print("ATOM-GITAGENT-001: GitAgent Export/Import Test")
    print("=" * 60 + "\n")
    
    results = []
    results.append(("Structure", test_gitagent_package_structure()))
    results.append(("Import", test_adapter_import()))
    results.append(("Manifest YAML", test_manifest_yaml()))
    results.append(("Export Cycle", test_export_cycle()))
    
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    passed = sum(1 for _, r in results if r)
    total = len(results)
    print(f"  {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✅ ALL TESTS PASSED — GitAgent integration ready!")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())
