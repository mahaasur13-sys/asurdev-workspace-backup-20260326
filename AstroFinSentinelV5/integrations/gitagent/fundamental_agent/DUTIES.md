# DUTIES.md — Fundamental Agent

## Primary Responsibilities

### 1. Valuation Analysis
- Calculate MVRV (Market Value to Realized Value) ratio
- Measure ATH (All-Time High) distance percentage
- Assess revenue/earnings quality via on-chain metrics

### 2. Growth Assessment
- Analyze 30-day volatility regime
- Compare market cap rank vs. historical performance
- Identify growth vs. declining phases

### 3. Risk Scoring
- Score: 0-1 scale (0.5 = fair value)
- MVRV thresholds: <0.7 (undervalued), 0.7-2.0 (fair), >3.5 (bubble)
- Weight reduction for extreme volatility (>30%)

## Output Format

```
[FUNDAMENTAL SIGNAL]
• Direction: LONG / SHORT / NEUTRAL
• Confidence: XX%
• MVRV Ratio: X.XX
• ATH Distance: XX%
• 30D Volatility: XX%
• Reasoning: [2-3 sentences]
• Sources: [API sources]

[Signal Metadata]
• Valuation Score: X.XX
• Earnings Quality: [assessment]
• Growth Phase: [assessment]
```

## Error Handling
- API failure → return NEUTRAL with confidence 30%
- Insufficient data → flag as ESTIMATED, reduce confidence by 20%
