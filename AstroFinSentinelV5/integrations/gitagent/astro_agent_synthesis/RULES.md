# RULES.md — Synthesis Agent Rules

## Absolute Rules
1. **Never report confidence > 92** (EC-01 hubris cap)
2. **Block all trades in EXTREME volatility regime**
3. **Always include uncertainty metrics** (aleatoric + epistemic + total)
4. **Generate DecisionRecord** for every decision
5. **Respect conflict resolution** — if Astro contradicts Fundamental+Quant, reduce Astro weight by 30%

## Volatility Guards (V-06/V-07)
| Regime | Confidence Drop | Position Limit |
|--------|-----------------|----------------|
| LOW | 0 | 3.0% |
| NORMAL | 0 | 2.0% |
| HIGH | -10 | 1.0% |
| EXTREME | -25 + AVOID | 0.5% |

## AMRE Validation Rules
1. **Grounding** — High confidence + low signal quality = reject
2. **Self-Questioning** — Challenge consensus above 3 high-confidence agents
3. **Uncertainty Threshold** — Total uncertainty > 0.6 = reduce position by 50%
