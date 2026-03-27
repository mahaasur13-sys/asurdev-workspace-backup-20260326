---
type:: database
id:: metrics_history_db
tags:: [database, backtest, sqlite]
description:: SQLite — результаты бэктестов (backtest runs)
role:: analytics
related_to:: "[[history_db]]"
file:: "backtest/metrics_history.db"
file_size:: "~110 KB"
row_count:: 12
created:: 2026-03-26
last_modified:: 2026-03-27
---

## metrics_history.db — Бэктесты

**Путь:** `backtest/metrics_agent.py` + `backtest/engine.py` (~110 KB, 12 строк)

### Схема

```sql
CREATE TABLE backtest_runs (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id          TEXT    NOT NULL UNIQUE,
    symbol              TEXT    NOT NULL,
    start_date          TEXT    NOT NULL,
    end_date            TEXT    NOT NULL,
    timeframe           TEXT    NOT NULL DEFAULT 'SWING',
    win_rate            REAL    NOT NULL DEFAULT 0.0,
    sharpe_ratio        REAL    NOT NULL DEFAULT 0.0,
    total_trades        INTEGER NOT NULL DEFAULT 0,
    winning_trades      INTEGER NOT NULL DEFAULT 0,
    losing_trades       INTEGER NOT NULL DEFAULT 0,
    avg_win_pct         REAL    NOT NULL DEFAULT 0.0,
    avg_loss_pct        REAL    NOT NULL DEFAULT 0.0,
    total_return_pct    REAL    NOT NULL DEFAULT 0.0,
    max_drawdown_pct    REAL    NOT NULL DEFAULT 0.0,
    avg_confidence      REAL    NOT NULL DEFAULT 0.0,
    initial_capital     REAL    NOT NULL DEFAULT 0.0,
    final_capital       REAL    NOT NULL DEFAULT 0.0,
    created_at          TEXT    NOT NULL DEFAULT (datetime('now'))
)
```

### Индексы

- `session_id` — UNIQUE
- `symbol`
- `created_at`

### Использование

```python
from backtest.metrics_agent import MetricsAgent, BacktestRun

agent = MetricsAgent()
agent.record_run(BacktestRun(
    session_id="abc123",
    symbol="BTCUSDT",
    start_date="2026-01-01",
    end_date="2026-03-27",
    win_rate=0.62,
    sharpe_ratio=1.45,
    total_trades=47,
    # ...
))
runs = agent.list()
summary = agent.summary()
```

### Аналитические запросы

```sql
-- Equity curve
SELECT created_at, final_capital
FROM backtest_runs
ORDER BY created_at;

-- Лучший символ по Sharpe
SELECT symbol, MAX(sharpe_ratio) as best_sharpe, AVG(win_rate) as avg_wr
FROM backtest_runs
GROUP BY symbol
ORDER BY best_sharpe DESC;

-- Max drawdown
SELECT symbol, MAX(max_drawdown_pct) as worst_dd
FROM backtest_runs
GROUP BY symbol;
```
