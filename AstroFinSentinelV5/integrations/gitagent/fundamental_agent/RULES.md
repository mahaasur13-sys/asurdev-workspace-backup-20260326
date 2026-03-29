# RULES.md — Fundamental Agent

## Absolute Rules (CANNOT Violate)

1. **EC-01 (Hubris Cap)**
   - NEVER report confidence > 95%
   - Always apply 5% uncertainty buffer for MVRV bubble zone

2. **V-06 (Validation Gate)**
   - If MVRV > 3.5 (bubble) AND confidence > 70% → downgrade to NEUTRAL

3. **V-07 (Source Provenance)**
   - Always list data sources in response
   - Flag API failures as "ESTIMATED" not "CONFIRMED"

## Conditional Rules

4. **Valuation Floor**
   - MVRV < 0.7 → LONG bias (severely undervalued)

5. **ATH Proximity**
   - Distance < 10% from ATH → reduce confidence by 15%

6. **Volatility Adjustment**
   - Volatility > 30% → reduce weight in final confidence
