---
type:: database
id:: belief_db
tags:: [database, bayesian, thompson-sampling, sqlite]
description:: SQLite — Bayesian Belief Tracker (Thompson Sampling)
role:: reinforcement_learning
related_to:: "[[history_db]]"
file:: "core/belief.db"
file_size:: "~40 KB"
row_count:: 3 (agents with belief data)
created:: 2026-03-26
last_modified:: 2026-03-27
---

## belief.db — Bayesian Belief Tracker

**Путь:** `core/belief.py` (~40 KB, 3 агента)

### Модель: Beta Distribution

Каждый агент имеет **Beta(α, β)** распределение:

```
α = successes + 1   (по умолчанию α=1, β=1 → uniform prior)
β = failures  + 1

mean   = α / (α + β)      — posterior mean accuracy
mode   = (α-1) / (α+β-2)  — MAP estimate
std    = √(αβ / (n²(n+1))) — posterior std dev
CI     = Wilson score interval (95%)
```

### Таблицы

#### agent_beliefs — текущие убеждения

```sql
CREATE TABLE agent_beliefs (
    agent_name      TEXT PRIMARY KEY,
    alpha           REAL NOT NULL DEFAULT 1.0,
    beta            REAL NOT NULL DEFAULT 1.0,
    total_sessions  INTEGER NOT NULL DEFAULT 0,
    updated_at      TEXT NOT NULL DEFAULT (datetime('now'))
)
```

#### agent_belief_history — история

```sql
CREATE TABLE agent_belief_history (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_name  TEXT NOT NULL,
    alpha       REAL NOT NULL,
    beta        REAL NOT NULL,
    outcome     INTEGER NOT NULL,  -- 1=success, 0=failure
    session_id  TEXT NOT NULL,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
)
```

#### agent_selection_log — кто кого выбирал

```sql
CREATE TABLE agent_selection_log (
    session_id  TEXT NOT NULL,
    agent_name  TEXT NOT NULL,
    pool_name   TEXT NOT NULL,
    was_called  INTEGER NOT NULL CHECK (was_called IN (0,1)),
    success_flag INTEGER,          -- NULL если не вызван, 0/1 если вызван
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (session_id, agent_name)
)
```

### Использование

```python
from core.belief import get_belief_tracker, update_beliefs_from_session

bt = get_belief_tracker()

# После каждой сессии
update_beliefs_from_session(final_output)

# Лидерборд по accuracy
bt.leaderboard()

# История одного агента
bt.get_agent_history("QuantAgent")

# Логи выборки
bt.get_selection_log(session_id="abc123")
bt.get_selection_log(agent_name="QuantAgent", limit=100)

# Сброс
bt.reset("QuantAgent")     # один агент
bt.reset()                 # все
```

### Интеграция с Thompson Sampling

```
ThompsonSampler:
  For each agent in pool:
      α, β = belief.get(agent_name)
      θ = sample Beta(α, β)
  Select top-K agents by θ
```

### Рекомендации

| α, β | Интерпретация |
|------|--------------|
| α=1, β=1 | Неизвестно — равномерный prior |
| α=10, β=5 | 65% accuracy, 10 наблюдений |
| α=50, β=30 | 62% accuracy, 80 наблюдений |

> Чем больше сессий — тем уже доверительный интервал.
