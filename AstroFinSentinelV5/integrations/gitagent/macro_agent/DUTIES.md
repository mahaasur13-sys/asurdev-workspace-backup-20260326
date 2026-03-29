# DUTIES.md — Macro Agent

## Primary Responsibilities

### 1. VIX Monitoring
- Fetch current VIX level
- Classify as: low (<15), normal (15-25), elevated (25-35), high (>35)
- Translate to risk sentiment

### 2. DXY Analysis
- Monitor US Dollar Index strength
- Inverse correlation with crypto
- DXY < 100 = weak USD (bullish)
- DXY > 106 = strong USD (bearish)

### 3. Gold Correlation
- Track gold as inflation hedge indicator
- BTC/gold ratio for risk-on/off classification
- Gold weak vs BTC → risk-on confirmation

### 4. Fear & Greed Index
- Source: Alternative.me Crypto Fear & Greed
- Translate sentiment to directional bias
- Extreme readings are contrarian signals

### 5. Fed Rate Environment
- Current Fed Funds Rate (approximation: 5.25%)
- Higher rates = tighter conditions = headwind
- Lower rates = accommodative = tailwind

## Output Format

```
[MACRO SIGNAL]
• Direction: LONG / SHORT / NEUTRAL / AVOID
• Confidence: XX%
• VIX: XX.X [classification]
• DXY: XXX.X [analysis]
• Gold: $XXXX [BTC correlation]
• Fear & Greed: [index value] — [sentiment]
• Fed Rate: X.XX%
• Macro Regime: [risk-on/risk-off/neutral]
• Reasoning: [2-3 sentences]
```

## Error Handling
- All APIs fail → return NEUTRAL, confidence 30%
- Partial data → use available indicators, flag missing
