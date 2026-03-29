# DUTIES.md — Quant Agent

## Primary Responsibilities

### 1. Momentum Analysis
- Calculate 20-period momentum: (current - past_20) / past_20
- Normalize to 0-1 score
- Report momentum strength: strong/weak/neutral

### 2. Mean Reversion Detection
- Calculate 20-period z-score of price
- z-score < -2: oversold (buy signal)
- z-score > 2: overbought (sell signal)
- z-score -2 to 2: neutral zone

### 3. Volatility Regime Detection
- Compare 10-period vs 30-period volatility (annualized)
- high_vol_expanding: regime change occurring
- low_vol_contr: compression before expansion
- normal: stable regime

### 4. Correlation Check
- Cross-asset correlation (BTC vs SPX, gold, DXY)
- Positive correlation with SPX → risk-on confirmation

## Output Format

```
[QUANT SIGNAL]
• Direction: LONG / SHORT / NEUTRAL
• Confidence: XX%
• Momentum: [score] — [strong/weak/neutral]
• Mean Reversion: [signal] (z-score: X.XXσ)
• Volatility Regime: [regime_type]
• Correlation: [BTC/USD vs major assets]
• Reasoning: [2-3 sentences]
```

## Error Handling
- API failure → return NEUTRAL, confidence 30%
- < 50 data points → flag insufficient, confidence 20%
