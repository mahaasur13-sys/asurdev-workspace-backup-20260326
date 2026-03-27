---
type:: agent
id:: risk_agent
tags:: [agent, risk-management, position-sizing, stop-loss]
created:: 2026-03-27
weight:: 0.05
domain:: trading
source:: [[AstroFinSentinelV5/agents/_impl/risk_agent.py]]

## Назначение

RiskAgent — управление рисками и размером позиции.

## Обязанности

1. Расчёт оптимального размера позиции на основе волатильности
2. Определение max drawdown tolerance
3. Установка stop-loss уровней на основе ATR
4. Валидация risk/reward ratio

## Метрики

| Метрика | Формула |
|---------|---------|
| Position size | `capital × risk_pct / ATR` |
| Stop-loss | `entry × (1 ± ATR_mult)` |
| Max drawdown | 2× ATR |
| R/R ratio | `(target - entry) / (entry - stop)` |

## Интеграция

- Использует: [[volatility_engine]] → `VolatilityRisk`
- Stop-loss = `entry × (1 - REGIME_STOP_MULTIPLIER[regime])`
- Risk/reward = `1:2` базовое (2× ATR target)

## Backward reference

- Родитель: [[agents_index]]
- Входит в: [[synthesis_agent]] (minor agent)

## Реализация

```python
class RiskAgent(BaseAgent[AgentResponse]):
    weight = 0.05  # 5%
    domain = "trading"
```
