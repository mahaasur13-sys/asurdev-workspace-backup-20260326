# DUTIES.md — Synthesis Agent Responsibilities

## Primary Duty
Coordinate all agent signals into a unified trading recommendation.

## Responsibilities

### 1. Signal Collection
- Gather outputs from: FundamentalAgent, QuantAgent, MacroAgent, OptionsFlowAgent, SentimentAgent, TechnicalAgent
- Gather outputs from: AstroCouncil (Bradley, Gann, Cycle, Electoral, TimeWindow agents)
- Weight signals according to category_weights configuration

### 2. Uncertainty Quantification (AMRE)
For every synthesis:
- Calculate aleatoric uncertainty (data noise)
- Calculate epistemic uncertainty (model uncertainty)
- Report total uncertainty

### 3. Decision Record Generation
For every decision:
- Create DecisionRecord with full audit trail
- Include Q* values, trajectories, KPI snapshots
- Sync to PostgreSQL via KARL Replay Buffer

### 4. Conflict Resolution
When Astro disagrees with Fundamental+Quant:
- Reduce Astro category weight by 30%
- Boost Fundamental by +18%
- Boost Quant by +12%
- Always explain the conflict in reasoning

### 5. Output Format
```json
{
  "signal": "LONG|SHORT|NEUTRAL|AVOID",
  "confidence": 0-92,
  "reasoning": "string",
  "uncertainty": {
    "aleatoric": 0.0-1.0,
    "epistemic": 0.0-1.0,
    "total": 0.0-1.0
  },
  "metadata": {
    "entry_zone": [low, high],
    "stop_loss": price,
    "targets": [t1, t2, t3],
    "position_size": 0.0-1.0,
    "regime": "LOW|NORMAL|HIGH|EXTREME"
  }
}
```
