---
type:: moc
id:: databases_index
tags:: [moc, databases, sqlite, knowledge-base]
description:: Индекс всех баз данных AstroFin Sentinel V5
---

# 🗄️ Databases Index

> AstroFin Sentinel V5 использует **3 SQLite БД** для разных целей.

## Обзор

| БД | Файл | Таблиц | Строк | Назначение |
|----|------|--------|-------|-----------|
| [[history_db]] | `core/history.db` | 8 | 33 | **Сессии** — каждый запуск `run_sentinel_v5()` |
| [[metrics_history_db]] | `backtest/metrics_history.db` | 1+ | 12 | **Бэктесты** — результаты прогонов на исторических данных |
| [[belief_db]] | `core/belief.db` | 3 | 3 | **Thompson Sampling** — Bayesian Belief Tracker |

## Связи между БД

```
history_db (sessions)
       │
       ├── записывает сессию
       │         │
       │         └──► update_beliefs_from_session()
       │                        │
       │                        ▼
       │              belief_db (agent_beliefs)
       │                        │
       ▼                        ▼
metrics_history_db ◄───────── записывает результат бэктеста
(backtest_runs)
```

## Инструменты

### Мониторинг
```bash
python tools/db_monitor.py       # размер, число строк, последние записи
```

### Миграции
```bash
python migrations/migrate.py --status   # версия схемы
python migrations/migrate.py --plan      # pending миграции
python migrations/migrate.py             # применить
```

### Thompson CLI
```bash
python tools/thompson_cli.py scores      # текущие убеждения
python tools/thompson_cli.py leaderboard # ранжирование
python tools/thompson_cli.py simulate    # симуляция
```

## Дополнительные таблицы

| БД | Таблица | Назначение |
|----|---------|-----------|
| `history.db` | `_schema_version` | Версия миграций |
| `history.db` | `_row_count_snapshots` | Снапшоты для мониторинга |
| `belief.db` | `agent_belief_history` | История обновлений убеждений |
| `belief.db` | `agent_selection_log` | Лог — кто был выбран в каждой сессии |

## Правила

1. **history_db** — primary storage, всегда пишется после `run_sentinel_v5()`
2. **belief_db** — обновляется после каждой сессии с результатом
3. **metrics_history_db** — только после завершения бэктеста
4. **Не удалять** строки вручную — только через API модулей
