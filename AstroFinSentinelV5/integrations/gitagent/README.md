# GitAgent Integration — AstroFin Sentinel V5

**Status:** Phase 2 Complete ✅  
**ATOM:** ATOM-GITAGENT-036  
**Date:** 2026-03-29

---

## Overview

GitAgent integration enables bidirectional compatibility between AstroFin Sentinel V5's MASFactory and the emerging GitAgent open standard for multi-agent systems.

### Component Mapping

| GitAgent Concept | MASFactory Equivalent | Status |
|------------------|----------------------|--------|
| `agent.yaml` | `GitAgentManifest` | ✅ Direct |
| `SOUL.md` | Role capabilities | ✅ Direct |
| `RULES.md` | Guards | ✅ Direct |
| `DUTIES.md` | Role responsibilities | ✅ Direct |
| `sub_agents/` | `Role` | ✅ Direct |
| `workflows/` | `SwitchNode` | ✅ Direct |

---

## Exported Agents (Phase 2)

### 4 Key Agents Exported

1. **AstroCouncil** — Multi-tradition astrological analysis
   - Sub-agents: WesternAstrologer, VedicAstrologer, FinancialAstrologer
   - Weight: 20%
   - Key rules: Choghadiya check, Wellesley Score

2. **FundamentalAgent** — Financial statement & on-chain analysis
   - Metrics: MVRV ratio, ATH distance, volatility
   - Weight: 12%

3. **QuantAgent** — Backtesting & momentum analysis
   - Models: Momentum, Mean Reversion, Volatility Regime
   - Weight: 10%

4. **MacroAgent** — Macro indicators & risk sentiment
   - Indicators: VIX, DXY, Gold, Fear & Greed
   - Weight: 8%

---

## Usage

### CLI Commands

```bash
# Export agents to GitAgent package
python -m integrations.gitagent.adapters.cli export-agent <agent_names...>

# Import GitAgent package
python -m integrations.gitagent.adapters.cli import-agent <package_path>

# Test round-trip
python -m integrations.gitagent.adapters.cli roundtrip
```

### Python API

```python
from integrations.gitagent.adapters.gitagent_adapter import (
    export_masfactory_to_gitagent,
    load_gitagent_as_masfactory,
)

# Export
pkg_path = export_masfactory_to_gitagent(topology, "/output/dir", "my_agents")

# Import
engine = load_gitagent_as_masfactory("/path/to/package")
```

---

## Package Structure

```
integrations/gitagent/
├── adapters/
│   ├── __init__.py
│   ├── cli.py                    # CLI commands
│   └── gitagent_adapter.py      # MASFactory ↔ GitAgent adapter
├── astro_agent_synthesis/        # Pilot package (Phase 1)
│   ├── agent.yaml
│   ├── SOUL.md
│   ├── RULES.md
│   ├── DUTIES.md
│   └── sub_agents/synthesis_role/
├── astro_council/               # Phase 2 exports
│   ├── agent.yaml
│   ├── SOUL.md
│   ├── RULES.md
│   └── DUTIES.md
├── fundamental_agent/
├── quant_agent/
├── macro_agent/
├── atom_036_roundtrip_test.py  # Test suite
└── README.md
```

---

## Phase 2 Test Results

```
TEST 1: Package Structure Validation
  ✅ astro_council — valid
  ✅ fundamental_agent — valid
  ✅ quant_agent — valid
  ✅ macro_agent — valid

TEST 2: Round-trip Export/Import
  ✅ Round-trip VERIFIED: 4 agents

Result: ALL TESTS PASSED ✅
```

---

## Phase 3 (Future)

- [ ] Export remaining agents (TechnicalAgent, BullResearcher, BearResearcher, etc.)
- [ ] Add `gitagent validate` CLI command
- [ ] Update Model Spec with GitAgent support
- [ ] Test interoperability with external GitAgent packages
