---
type:: method
id:: volatility_engine
tags:: [method, risk-management, position-sizing, kelly-criterion, _impl]
aliases:: [R-07, Volatility-Adjusted Risk, Dynamic Risk Engine]
related:: [thompson_sampling, belief_tracker, synthesis_agent]
created:: 2026-03-27
updated:: 2026-03-27
---

# Volatility Engine (R-07)

> Динамический расчёт риска на основе волатильности рынка.
> Файл: `core/volatility.py`

## Концепция

Система адаптирует размер позиции и стоп-лосс в зависимости от текущего режима волатильности, измеряемого через ATR (Average True Range).

```
Цена + ATR → Режим волатильности → risk_pct + Kelly + Stop Distance
```

**Зачем:** в периоды высокой волатильности обычные стратегии с фиксированным риском 2% приводят к катастрофическим потерям.

---

## Режимы волатильности

| Режим | ATR% | risk_pct | Kelly mult | Conf drop | Поведение |
|-------|------|----------|-----------|-----------|-----------|
| **LOW** | <1.5% | **3.0%** | 1.0× | 0 | Спокойный рынок — можно увеличивать позицию |
| **NORMAL** | 1.5–3% | **2.0%** | 0.75× | 0 | Базовый риск |
| **HIGH** | 3–5% | **1.0%** | 0.50× | −10 | Волатильный — снижаем экспозицию |
| **EXTREME** | ≥5% | **0.5%** | 0.20× | −25 | Чёрный лебедь — **AVOID** |

---

## R-07 Guards

### V-06: Confidence Drop (HIGH/EXTREME)

```
adjusted_confidence = raw_confidence − REGIME_CONFIDENCE_DROP[regime]
```

| Режим | Drop | Мин. confidence |
|-------|------|----------------|
| LOW | 0 | raw |
| NORMAL | 0 | raw |
| HIGH | **−10** | max(30, raw−10) |
| EXTREME | **−25** | max(30, raw−25) |

### V-07: AVOID Signal (EXTREME)

Если режим = EXTREME → synthesis должен вернуть `SignalDirection.AVOID`, несмотря на сигналы агентов.

---

## Kelly Criterion

```
W = win_rate
L = avg_loss_pct
W/L = reward/risk ratio
Kelly = (W × (W/L) − (1−W)) / (W/L)
```

**Capped:** min=1%, max=20%

```
kelly_adjusted = max(MIN_KELLY, min(kelly_raw × REGIME_MULT[regime], MAX_KELLY))
```

| Режим | Kelly mult |
|-------|-----------|
| LOW | 1.0× |
| NORMAL | 0.75× |
| HIGH | 0.50× |
| EXTREME | 0.20× |

---

## Stop-Loss Distance

```
stop_distance_pct = REGIME_STOP_MULTIPLIER[regime]
stop_loss = entry × (1 ± stop_distance_pct)
```

| Режим | Stop distance | Примечание |
|-------|--------------|-----------|
| LOW | 2.5% | Умеренный стоп |
| NORMAL | 2.0% | Базовый |
| HIGH | **3.0%** | Шире — ложные всплески |
| EXTREME | **5.0%** | Очень шире — волатильность |

---

## Usage

```python
from core.volatility import (
    VolatilityEngine,
    get_volatility_risk,
    VolatilityRegime,
    calculate_atr,
)

# Полный анализ
engine = VolatilityEngine()
risk = engine.analyze(
    symbol="BTCUSDT",
    price=97000,
    atr=2500,          # абсолютный ATR
)
# risk.risk_pct        = 0.02   (2%)
# risk.position_size   = 0.10   (10%)
# risk.stop_distance   = 0.02   (2%)
# risk.confidence_drop = 0
# risk.regime          = NORMAL

# Stop-loss и targets
entry = 97000
sl = risk.stop_loss_long(entry)      # 95060
tp = risk.target_long(entry, rr=2)  # 99080

# Direct regime override
engine = VolatilityEngine.from_regime(VolatilityRegime.HIGH)
risk = engine.analyze(symbol="BTCUSDT", price=97000)

# V-06 apply
adjusted_conf, label = engine.apply_volatility_guard(75, VolatilityRegime.HIGH)
# adjusted_conf = 65, label = "V-06(dr=10)"
```

---

## ATR Calculation

```python
# From Binance klines
from core.volatility import calculate_atr

klines = [[high, low, close], ...]  # 15+ свечей
atr = calculate_atr(klines, period=14)

# Direct from Binance
atr = atr_from_binance("BTCUSDT", interval="1h", limit=30)
```

---

## Caching

```python
from core.volatility import get_volatility_risk, clear_volatility_cache

# Кэшируется по symbol — повторные вызовы за сессию не делают пересчёт
risk = get_volatility_risk("BTCUSDT", price=97000, atr=2500)

# Очистка между сессиями
clear_volatility_cache()
```

---

## Dataclass: VolatilityRisk

```python
@dataclass
class VolatilityRisk:
    regime: VolatilityRegime
    risk_pct: float              # 0.02 = 2%
    position_size: float         # Kelly-adjusted
    atr_pct: float              # ATR as % of price
    stop_distance_pct: float    # для расчёта SL/TP
    confidence_drop: int        # V-06 penalty
    kelly_raw: float            # до dampening
    kelly_adjusted: float       # после dampening
    reasoning: str              # человекочитаемое описание

    def stop_loss_long(self, entry: float) -> float
    def stop_loss_short(self, entry: float) -> float
    def target_long(self, entry: float, rr: float = 2.0) -> float
    def target_short(self, entry: float, rr: float = 2.0) -> float
```

---

## R-07 Integration

```
Оркестратор → вызывает VolatilityEngine
                         │
             ┌───────────┴───────────┐
             │ ATR% → Regime → риск-параметры
             └───────────┬───────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
    risk_pct      stop_distance    confidence_drop
         │               │               │
    Позиция           SL/TP         V-06 penalty
         │               │               │
         └───────────────┼───────────────┘
                         │
                    Synthesis Agent
                         │
             ┌───────────┴───────────┐
             │  V-07: EXTREME = AVOID │
             └─────────────────────────┘
```

---

## Known Issues

| # | Описание | Статус |
|---|---------|--------|
| 1 | Kelly default params (55% win rate) — предположение | ⚠️ TODO: вынести в config |
| 2 | ATR с Binance public API — rate limit | ⚠️ TODO: кэшировать |
| 3 | Нет real-time regime monitoring | 📋 Future |

---

## TODO

- [ ] Вынести default win_rate / avg_win / avg_loss в config
- [ ] Добавить real-time regime alerts
- [ ] Интегрировать V-07 в LangGraph synthesis node

---

## См. также

- [[thompson_sampling]] — выбор агентов
- [[belief_tracker]] — отслеживание точности агентов
- [[synthesis_agent]] — финальный синтез
- [[agents_index]] — все агенты
