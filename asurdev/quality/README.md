# Quality Schema — Связи и Usage

## Схема связей (Entity-Relationship)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        QUALITY PROTOCOL ← → POSTGRES                   │
└─────────────────────────────────────────────────────────────────────────┘

    ┌──────────────┐         ┌──────────────────┐
    │   Quality    │         │  Obsidian Note   │
    │   Protocol   │────────▶│  (MD file)       │
    │  (шаблон)   │         │  cp_id = BTR-id  │
    └──────────────┘         └──────────────────┘
            │                          │
            │ создать                  │ ссылается на
            ▼                          ▼
    ┌──────────────┐         ┌──────────────────┐
    │ change_      │         │  backtest_      │
    │ proposals    │────────▶│  runs            │
    │ (cp_id)      │         │  (run_id)        │
    └──────┬───────┘         └────────┬─────────┘
           │                          │
           │ связан с                  │ наполняет
           ▼                          ▼
    ┌──────────────┐         ┌──────────────────┐
    │  incidents   │         │     metrics       │
    │ (если дегра)│         │ (KPI по окнам)   │
    └──────────────┘         └──────────────────┘

───────────────────────────────────────────────────────────────────────────

                    PRIMARY KEY CHAIN: request_id
                    ══════════════════════════════

    ┌─────────────────────────────────────────────────────────────────────┐
    │                                                                     │
    │   requests ────────────────────────────────────────────────────┐   │
    │       │                                                       │   │
    │       │ request_id                                            │   │
    │       ▼                                                       │   │
    │   agent_runs ──────────────────────────────────────────────┐   │   │
    │       │                                                     │   │   │
    │       │ request_id (FK)                                     │   │   │
    │       ▼                                                     │   │   │
    │   final_outputs ────────────────────────────────────────┐   │   │   │
    │       │                                                   │   │   │
    │       │ request_id (FK)                                   │   │   │
    │       ▼                                                   │   │   │
    │   data_lineage ──────────────────────────────────────┐   │   │   │
    │       │                                                 │   │   │
    │       │ request_id (FK)                                 │   │   │
    │       ▼                                                 │   │   │
    │   feedback ─────────────────────────────────────────┘   │   │   │
    │       │                                                   │   │   │
    └───────┼───────────────────────────────────────────────────┘   │   │
            │                                                       │   │
            └───────────────────────────────────────────────────────┘   │
                                                                        │
    versions ──────────────────────────────────────────────────────► FK  │
        │                                                             │
        │ version_id (PK)                                             │
        ▼                                                             │
    prompt_version_id / model_version_id / embed_version_id / index_version_id
    │
    └─▶ component + version_name + version_hash (git commit)
                                                                     │
─────────────────────────────────────────────────────────────────────
                                                                     │
                 VERSION TRACKING WORKFLOW                            │
                 ════════════════════════════                        │
                                                                     │
    1) DEVELOPER меняет промпт / модель / индекс                     │
                              │                                       │
                              ▼                                       │
    2) INSERT INTO versions (component, version_name, version_hash)  │
                       │                                             │
                       │ version_id                                  │
                       ▼                                             │
    3) request.prompt_version_id = NEW version_id                     │
                       │                                             │
                       ▼                                             │
    4) Весь pipeline теперь отслежен                                  │
```

## Как request_id проходит через систему

```
┌─────────────────────────────────────────────────────────────────────┐
│                         REQUEST LIFECYCLE                          │
└─────────────────────────────────────────────────────────────────────┘

UI (Streamlit)                          Orchestrator
    │                                        │
    │  1) user clicks "Analyze BTC"          │
    │     user_id = "mahasur"                │
    │     asset = "BTC"                      │
    │     horizon = "7d"                      │
    │────────────────────────────────────────▶
    │                                        │
    │                                        │ 2) INSERT requests
    │                                        │    → request_id = UUID-xxx
    │                                        │
    │                                        │ 3) Spawn agents:
    │                                        │    - MarketAnalyst
    │                                        │    - BullResearcher  
    │                                        │    - BearResearcher
    │                                        │    - Astrologer
    │                                        │    - Synthesizer
    │                                        │
    │                                        │ 4) INSERT agent_runs
    │                                        │    (каждый с request_id)
    │                                        │
    │                                        │ 5) INSERT final_outputs
    │                                        │    (verdict, levels)
    │                                        │
    │◀────────────────────────────────────────
    │                                        │
    │  6) Display C.L.E.A.R. result          │
    │     with request_id shown               │
    │                                        │
    │────────────────────────────────────────▶
    │                                        │
    │  Later: User feedback                  │
    │  7) INSERT feedback (request_id)        │
    │                                        │
```

## Version Snapshot в каждом Request

```sql
-- При каждом запросе фиксируем версии
INSERT INTO asurdev_quality.requests (
    request_id,
    asset,
    horizon,
    mode,
    prompt_version_id,      -- FK → versions
    model_version_id,      -- FK → versions
    embed_version_id,      -- FK → versions
    index_version_id,       -- FK → versions
    code_version_hash       -- git commit
) VALUES (
    gen_random_uuid(),
    'BTC',
    '7d',
    'core_preferred',
    (SELECT version_id FROM asurdev_quality.versions 
     WHERE component = 'prompt' ORDER BY created_at DESC LIMIT 1),
    (SELECT version_id FROM asurdev_quality.versions 
     WHERE component = 'model' AND version_name = 'qwen2.5-coder:32b' LIMIT 1),
    (SELECT version_id FROM asurdev_quality.versions 
     WHERE component = 'embed' ORDER BY created_at DESC LIMIT 1),
    (SELECT version_id FROM asurdev_quality.versions 
     WHERE component = 'index' ORDER BY created_at DESC LIMIT 1),
    'a3f2c1d'  -- git commit hash
);
```

## Version Increment Workflow

```
ПРОБЛЕМА: Accuracy упал на 15% за неделю
═════════════════════════════════════════

1) OBSIDIAN: Создать CP-20260320-1700
   - problem: accuracy ↓ 15%
   - hypothesis: промпт Astrologer даёт противоречивые сигналы

2) POSTGRES: Записать CP
   INSERT INTO change_proposals (cp_id, problem, component)
   VALUES ('CP-20260320-1700', 'accuracy drop', 'prompt');

3) РАЗРАБОТКА: Изменить промпт astrologer
   - Новый промпт = "Be more conservative with Neptune aspects"

4) POSTGRES: Записать новую версию
   INSERT INTO versions (component, version_name, description)
   VALUES ('prompt', 'v2.1.0', 'Conservative Neptune');

5) BACKTEST: Прогнать A/B
   - Старый промпт: accuracy = 0.52
   - Новый промпт: accuracy = 0.61 ✓

6) POSTGRES: Записать результат
   INSERT INTO backtest_runs (
       reason, related_cp_id, 
       prompt_version_id (old), prompt_version_id (new),
       results, decision
   ) VALUES (
       'post_cp', 'CP-20260320-1700',
       version_id_v2.0.0, version_id_v2.1.0,
       '{"accuracy_before": 0.52, "accuracy_after": 0.61}',
       'release'
   );

7) ОБНОВИТЬ CP:
   UPDATE change_proposals 
   SET status = 'released', 
       backtest_run_id = NEW_run_id,
       version_before = v2.0.0,
       version_after = v2.1.0,
       decision = 'release',
       decided_at = NOW()
   WHERE cp_id = 'CP-20260320-1700';

8) METRICS: После внедрения новой версии
   INSERT INTO metrics (metric_name, mode, window_start, window_end, value)
   VALUES ('accuracy', 'core', '2026-03-20', '2026-04-20', 0.61);
```

## Monitoring Queries

```sql
-- Accuracy за последние 30 дней по режимам
SELECT 
    mode,
    AVG((feedback.market_outcome->>'correct')::int) as accuracy,
    COUNT(*) as n_requests
FROM asurdev_quality.feedback f
JOIN asurdev_quality.requests r ON f.request_id = r.request_id
WHERE f.created_at > NOW() - INTERVAL '30 days'
GROUP BY mode;

-- Доля edge fallback
SELECT 
    DATE_TRUNC('week', created_at) as week,
    COUNT(*) FILTER (WHERE used_fallback = true) * 100.0 / COUNT(*) as fallback_pct
FROM asurdev_quality.final_outputs
GROUP BY week
ORDER BY week DESC;

-- Худшие кейсы (большие ошибки)
SELECT 
    r.request_id,
    r.asset,
    fo.verdict,
    f.market_outcome->>'return_pct' as actual_return,
    ABS((f.market_outcome->>'return_pct')::float) as abs_error
FROM asurdev_quality.feedback f
JOIN asurdev_quality.requests r ON f.request_id = r.request_id
JOIN asurdev_quality.final_outputs fo ON f.request_id = fo.request_id
WHERE f.market_outcome IS NOT NULL
ORDER BY abs_error DESC
LIMIT 10;
```

## Trigger для auto-versioning

```sql
-- Автоматически повышать версию при изменении промпта
CREATE OR REPLACE FUNCTION check_version_change()
RETURNS TRIGGER AS $$
BEGIN
    -- Если изменился component или version_name
    IF NEW.component = 'prompt' 
       AND OLD.version_name IS DISTINCT FROM NEW.version_name THEN
        -- Логировать в change_proposals
        INSERT INTO asurdev_quality.change_proposals (
            cp_id, component, change_summary, status
        ) VALUES (
            'AUTO-' || TO_CHAR(NOW(), 'YYYYMMDD-HH24MI'),
            NEW.component,
            'Auto-bumped: ' || OLD.version_name || ' → ' || NEW.version_name,
            'draft'
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_version_change
AFTER UPDATE ON asurdev_quality.versions
FOR EACH ROW EXECUTE FUNCTION check_version_change();
```
