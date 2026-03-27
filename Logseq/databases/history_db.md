---
type:: database
id:: history_db
tags:: [database, sessions, sqlite]
description:: SQLite — все сессии run_sentinel_v5()
role:: operational
related_to::
  - "[[metrics_history_db]]"
  - "[[belief_db]]"
file:: "core/history_db"
file_size:: "~240 KB"
row_count:: 33
created:: 2026-03-25
last_modified:: 2026-03-27
---

## history.db — Сессии торговых сигналов

**Путь:** `core/history_db.py` (~240 KB, 33 строки)

### Схема

```sql
CREATE TABLE sessions (
    id                       INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id               TEXT    NOT NULL UNIQUE,
    symbol                   TEXT    NOT NULL,
    timeframe                TEXT    NOT NULL,
    query_type               TEXT    NOT NULL,
    current_price            REAL    NOT NULL DEFAULT 0.0,
    flows_run                TEXT    NOT NULL DEFAULT '{}',   -- JSON: {technical, astro, electional}
    agent_count              INTEGER NOT NULL DEFAULT 0,
    final_signal             TEXT    NOT NULL DEFAULT 'NEUTRAL',
    final_confidence         INTEGER NOT NULL DEFAULT 50,
    final_reasoning          TEXT    NOT NULL DEFAULT '',
    final_output             TEXT    NOT NULL DEFAULT '{}',  -- JSON: полный вывод
    started_at               TEXT    NOT NULL DEFAULT '',
    finished_at              TEXT    NOT NULL DEFAULT '',
    created_at               TEXT    NOT NULL DEFAULT (datetime('now')),
    thompson_selections      TEXT    NOT NULL DEFAULT '{}',  -- JSON: выбранные агенты
    technical_agent_count    INTEGER NOT NULL DEFAULT 0,
    astro_agent_count        INTEGER NOT NULL DEFAULT 0,
    electoral_agent_count    INTEGER NOT NULL DEFAULT 0
)
```

### Дополнительные таблицы

| Таблица | Назначение |
|---------|-----------|
| `_schema_version` | Версия схемы миграций |
| `_row_count_snapshots` | Снапшоты числа строк (мониторинг) |

### Индексы

- `session_id` — UNIQUE
- `symbol`
- `timeframe`
- `created_at`
- `final_signal`

### Использование

```python
from core.history_db import save_session, get_session, list_sessions

# Сохранить после каждого запуска
save_session(symbol, timeframe, query_type, result)

# Получить последнюю
session = get_session(session_id)

# Статистика
stats = list_sessions(symbol="BTCUSDT", limit=10)
```

### Аналитические запросы

```sql
-- Последние 10 сессий по BTC
SELECT session_id, final_signal, final_confidence, created_at
FROM sessions
WHERE symbol = 'BTCUSDT'
ORDER BY created_at DESC
LIMIT 10;

-- Распределение сигналов
SELECT final_signal, COUNT(*) as cnt
FROM sessions
GROUP BY final_signal
ORDER BY cnt DESC;

-- Лучший конфиденс по символу
SELECT symbol, MAX(final_confidence) as max_conf
FROM sessions
GROUP BY symbol;
```

---

## Связи

- `→ metrics_history.db` — результаты бэктестов
- `→ belief.db` — обновление убеждений после каждой сессии
- `→ thompson.py` — логирование выборки агентов
