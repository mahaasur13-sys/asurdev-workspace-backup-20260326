---
name: synthesis_role
description: Multi-agent synthesis with KARL AMRE loop
type: agent_role
version: 1.0.0
---

# Synthesis Role — Skill Module

## Purpose
Coordinate multiple agent signals into a unified trading recommendation with uncertainty quantification.

## Inputs
- `signals`: List of agent signals (AgentResponse objects)
- `state`: Market state (price, regime, timeframe)
- `topology_context`: Role relationships from MASFactory topology

## Process
1. **Group by Category** — Aggregate signals by category (fundamental, quant, macro, astro, sentiment, technical)
2. **Detect Conflicts** — Check for Astro vs Fundamental+Quant conflicts
3. **Apply Weights** — Weighted voting with category weights
4. **Apply Guards** — EC-01 (hubris cap), V-06 (volatility), V-07 (EXTREME block)
5. **Uncertainty Quantification** — Calculate aleatoric + epistemic uncertainty
6. **Generate DecisionRecord** — Full audit trail for KARL

## Output
- `signal`: LONG | SHORT | NEUTRAL | AVOID
- `confidence`: 0-92 (never higher due to EC-01)
- `reasoning`: Human-readable explanation
- `uncertainty`: {aleatoric, epistemic, total}
- `metadata`: Entry levels, position size, regime

## Usage in MASFactory
```python
from mas_factory.engine import MASFactoryEngine

engine = MASFactoryEngine(topology)
result = await engine.run({"action": "synthesize", "state": market_state})
```

## Dependencies
- karll-amre (uncertainty, grounding, audit)
- astro-timing (Muhurta, Choghadiya, Nakshatra)
- market-synthesis (weighted voting, conflict resolution)
