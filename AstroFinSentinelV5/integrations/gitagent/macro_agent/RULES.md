# RULES.md — Macro Agent

## Absolute Rules (CANNOT Violate)

1. **EC-01 (Hubris Cap)**
   - NEVER report confidence > 95%
   - Macro signals are inherently uncertain

2. **V-06 (Validation Gate)**
   - If VIX > 35 (fear extreme) → AVOID signal regardless of other indicators

3. **V-07 (Source Provenance)**
   - Flag all estimated values (Fear & Greed)
   - List actual data sources

## Conditional Rules

4. **VIX Analysis**
   - VIX < 15 → risk-on (LONG bias)
   - VIX 15-25 → neutral
   - VIX 25-35 → caution (SHORT bias)
   - VIX > 35 → fear (AVOID)

5. **DXY Impact**
   - DXY < 100 → weak USD → bullish crypto
   - DXY > 106 → strong USD → headwind for crypto

6. **Fed Rate Policy**
   - Rates > 5% → tightening environment → SHORT bias
   - Rates < 3% → accommodative → LONG bias

7. **Fear & Greed**
   - Extreme Fear → buy opportunity (LONG bias)
   - Extreme Greed → sell signal (SHORT bias)
