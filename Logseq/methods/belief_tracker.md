---
type:: method
id:: belief_tracker
tags:: [method, bayesian, accuracy-tracking, sqlite, _impl]
aliases:: [Bayesian Belief Tracker, Agent Performance Tracking, Beta Distribution]
related:: [thompson_sampling, volatility_engine, synthesis_agent]
created:: 2026-03-27
updated:: 2026-03-27
---

# Belief Tracker

> Bayesian отслеживание точности агентов через Beta-распределение.
> Файл: `core/belief.py`

## Концепция

Каждый агент имеет **posterior Beta-распределение** точности. После каждой сессии Beta-параметры обновляются. Thompson Sampling использует эти данные для выбора агентов.

```
Сессия → Агент сигнал == Финальный сигнал? → β += 1 (success)
                                           → α += 1 (failure)
```

---

## Beta Distribution

### Prior: Beta(1, 1) — Uniform

```
α = successes + 1
β = failures + 1
```

### Key Properties

| Property | Formula | Описание |
|----------|---------|---------|
| **Mean** | α / (α + β) | posterior mean accuracy |
| **Mode** | (α−1) / (α+β−2) | MAP estimate (при α, β > 1) |
| **Std** | √(αβ / n²(n+1)) | posterior std dev |
| **95% CI** | Wilson score interval | credible interval |

### Credibility Interval (Wilson Score)

```python
p = mean
z = 1.96  # 95%
n = α + β
center = (p + z²/(2n)) / (1 + z²/n)
margin = z × √(p(1−p)/n + z²/(4n²)) / (1 + z²/n)
ci_lo = max(0, center − margin)
ci_hi = min(1, center + margin)
```

---

## Success Criteria

```
is_success = (agent_signal == final_signal)
             AND final_signal ∈ {LONG, SHORT, BUY, SELL, STRONG_BUY, STRONG_SELL}
```

**NEUTRAL, HOLD, AVOID → не влияют на belief update.**

---

## Database Schema

### Table: `agent_beliefs`

```sql
agent_name      TEXT PRIMARY KEY
alpha           REAL DEFAULT 1.0
beta            REAL DEFAULT 1.0
total_sessions  INTEGER DEFAULT 0
updated_at      TEXT
```

### Table: `agent_belief_history`

```sql
id              PRIMARY KEY
agent_name      TEXT
session_id      TEXT
final_signal    TEXT
agent_signal    TEXT
is_success      INTEGER
posterior_alpha REAL
posterior_beta  REAL
created_at      TEXT
```

### Table: `agent_selection_log`

```sql
session_id      TEXT PRIMARY KEY
agent_name      TEXT
pool_name       TEXT
was_called      INTEGER (0/1)
success_flag    INTEGER (NULL if was_called=0)
created_at      TEXT
```

---

## Usage

```python
from core.belief import (
    BeliefTracker,
    get_belief_tracker,
    update_beliefs_from_session,
    BeliefState,
)

# Singleton
tracker = get_belief_tracker()

# После сессии
result = await run_sentinel_v5(...)
results = tracker.update_from_session(result)
# {"FundamentalAgent": True, "MacroAgent": False, ...}

# Leaderboard
leaderboard = tracker.leaderboard()
# [{agent, mean_accuracy, ci_95, total_sessions}, ...]

# История одного агента
history = tracker.get_agent_history("QuantAgent", limit=100)

# Reset
tracker.reset("QuantAgent")   # один агент
tracker.reset()               # все агенты
```

---

## BeliefState

```python
@dataclass
class BeliefState:
    agent_name:     str
    alpha:         float = 1.0
    beta:          float = 1.0
    total_sessions: int = 0

    @property
    def mean(self) -> float: ...
    @property
    def mode(self) -> Optional[float]: ...
    @property
    def std(self) -> float: ...
    def credibility_interval(self, level=0.95) -> tuple[float, float]: ...
    def to_dict(self) -> dict: ...
```

---

## Pool Map (Agent → Pool)

```python
_POOL_MAP = {
    "MarketAnalyst":     "technical",
    "BullResearcher":    "technical",
    "BearResearcher":    "technical",
    "TechnicalAgent":    "technical",
    "FundamentalAgent":  "macro",
    "MacroAgent":        "macro",
    "QuantAgent":        "macro",
    "OptionsFlowAgent":  "macro",
    "SentimentAgent":    "macro",
    "GannAgent":         "astro",
    "BradleyAgent":      "astro",
    "ElliotAgent":       "astro",
    "CycleAgent":        "astro",
    "TimeWindowAgent":   "astro",
    "MuhurtaAgent":      "astro",
    "ElectionAgent":     "astro",
    # ELECTORAL_POOL overlaps:
    "ElectionAgent":     "electoral",
    "MuhurtaAgent":      "electoral",
}
```

---

## Leaderboard Example

| Agent | mean_accuracy | ci_95 | sessions | α | β |
|-------|-------------|-------|----------|---|---|
| QuantAgent | 0.72 | [0.58, 0.83] | 20 | 15 | 6 |
| MacroAgent | 0.68 | [0.51, 0.81] | 15 | 11 | 5 |
| SentimentAgent | 0.55 | [0.35, 0.74] | 8 | 5 | 4 |
| FundamentalAgent | 0.50 | [0.22, 0.78] | 5 | 3 | 3 |

---

## Selection Log

После каждого `update_from_session()` логируются **все** агенты из известных пулов:

- **was_called = 1** — агент был выбран и вызван
- **was_called = 0** — агент НЕ был выбран в этой сессии

```
Session 2026-03-27-001:
  called:     FundamentalAgent (1, success=1), QuantAgent (1, success=0)
  not called: MacroAgent (0, NULL), SentimentAgent (0, NULL)
```

---

## Known Issues

| # | Описание | Статус |
|---|---------|--------|
| 1 | Pool map дублируется в thompson.py и belief.py | ⚠️ DRY violation |
| 2 | History limit = 100 — hardcoded | 📋 TODO: config |
| 3 | Success criteria — только направление, не учитывает magnitude | 📋 Future |

---

## TODO

- [ ] Извлечь pool map в отдельный конфиг
- [ ] Добавить confidence interval threshold alerts
- [ ] Агрегировать selection log в per-agent win rate

---

## См. также

- [[thompson_sampling]] — использует belief для отбора
- [[volatility_engine]] — управление рисками
- [[synthesis_agent]] — финальный синтез
- [[agents_index]] — все агенты
