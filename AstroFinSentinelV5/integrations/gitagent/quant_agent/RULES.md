# RULES.md — Quant Agent

## Absolute Rules (CANNOT Violate)

1. **EC-01 (Hubris Cap)**
   - NEVER report confidence > 95%
   - Require 20+ data points for momentum analysis

2. **V-06 (Validation Gate)**
   - If z-score > 2.5 (extreme) → cap confidence at 70%

3. **V-07 (Source Provenance)**
   - Only use OHLCV data from Binance public API
   - Flag estimated values as such

## Conditional Rules

4. **High Volatility Regime**
   - If regime = "high_vol_expanding" → reduce all LONG signals
   - Increase stop-loss width by 1.5x

5. **Mean Reversion Signal**
   - z-score < -2 → oversold (LONG bias)
   - z-score > 2 → overbought (SHORT bias)

6. **Minimum Data Requirement**
   - < 50 candles → return NEUTRAL, confidence 30%
