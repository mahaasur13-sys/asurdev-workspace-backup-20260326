-- AstroFin Sentinel — Quality Schema
-- PostgreSQL @ Acer-2011
-- Schema: astrofin_quality

CREATE SCHEMA IF NOT EXISTS astrofin_quality;

-- ============================================
-- 1) VERSIONS — версии всего что влияет на результат
-- ============================================
CREATE TABLE astrofin_quality.versions (
    version_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    component       TEXT NOT NULL,      -- 'prompt' / 'model' / 'embed' / 'index' / 'code'
    version_name    TEXT NOT NULL,
    version_hash    TEXT,               -- git commit или hash промпта
    description     TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_versions_component ON astrofin_quality.versions(component, created_at DESC);

-- ============================================
-- 2) REQUESTS — карточка каждого запуска
-- ============================================
CREATE TABLE astrofin_quality.requests (
    request_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp       TIMESTAMPTZ DEFAULT NOW(),
    
    -- Идентификация
    user_id         TEXT,               -- псевдоним
    session_id      TEXT,
    
    -- Параметры запроса
    asset           TEXT NOT NULL,       -- BTC, ETH, etc
    horizon         TEXT NOT NULL,      -- 1d, 7d, 1w, 1m
    mode            TEXT NOT NULL,      -- edge_only, core_preferred, core_only
    latitude        FLOAT,
    longitude       FLOAT,
    
    -- Версии (FK)
    prompt_version_id      UUID REFERENCES astrofin_quality.versions(version_id),
    model_version_id       UUID REFERENCES astrofin_quality.versions(version_id),
    embed_version_id       UUID REFERENCES astrofin_quality.versions(version_id),
    index_version_id       UUID REFERENCES astrofin_quality.versions(version_id),
    code_version_hash      TEXT,       -- git commit
    
    -- Статус пайплайна
    status          TEXT DEFAULT 'pending',  -- pending, running, completed, failed
    error_message   TEXT,
    
    -- Мета
    client_ip       TEXT,
    user_agent      TEXT
);

CREATE INDEX idx_requests_asset_time ON astrofin_quality.requests(asset, timestamp DESC);
CREATE INDEX idx_requests_user ON astrofin_quality.requests(user_id, timestamp DESC);
CREATE INDEX idx_requests_status ON astrofin_quality.requests(status);

-- ============================================
-- 3) AGENT_RUNS — вывод каждого агента
-- ============================================
CREATE TABLE astrofin_quality.agent_runs (
    run_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id      UUID NOT NULL REFERENCES astrofin_quality.requests(request_id),
    
    agent_name      TEXT NOT NULL,      -- MarketAnalyst, Astrologer, etc
    agent_version   TEXT,
    
    -- Входы
    inputs_summary  JSONB,              -- что агент видел (state summary)
    rag_doc_ids     TEXT[],             -- какие RAG документы использовал
    data_refs       JSONB,              -- ссылки на данные
    
    -- Выходы
    signal          TEXT NOT NULL,      -- Bullish, Bearish, Neutral
    confidence      INTEGER CHECK (confidence BETWEEN 0 AND 100),
    rationale       TEXT,
    risk_flags      TEXT[],
    
    -- Рантайм
    latency_ms      INTEGER,
    tokens_in       INTEGER,
    tokens_out      INTEGER,
    errors          TEXT,
    
    -- Оценка агента
    agent_confidence_self INTEGER,      -- что агент сам думает о своей уверенности
    
    started_at      TIMESTAMPTZ DEFAULT NOW(),
    completed_at    TIMESTAMPTZ
);

CREATE INDEX idx_agent_runs_request ON astrofin_quality.agent_runs(request_id);
CREATE INDEX idx_agent_runs_agent ON astrofin_quality.agent_runs(agent_name, timestamp DESC);

-- ============================================
-- 4) FINAL_OUTPUTS — итоговый ответ системы
-- ============================================
CREATE TABLE astrofin_quality.final_outputs (
    output_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id      UUID UNIQUE NOT NULL REFERENCES astrofin_quality.requests(request_id),
    
    -- C.L.E.A.R. формат
    verdict         TEXT NOT NULL,      -- BUY, SELL, HOLD, WAIT
    action          TEXT,               -- конкретное действие
    confidence      INTEGER CHECK (confidence BETWEEN 0 AND 100),
    
    -- Уровни
    entry_zone      TEXT,
    stop_loss       TEXT,
    take_profit_1   TEXT,
    take_profit_2   TEXT,
    timeframe       TEXT,
    
    -- Синтез
    summary         TEXT,
    conditions      TEXT[],             -- условия пересмотра (invalidations)
    
    -- Агент voting
    votes           JSONB,              -- {"MarketAnalyst": "Bullish", "Astrologer": "Neutral", ...}
    agreement_score FLOAT,             -- доля согласия агентов (0-1)
    
    -- Fallback флаг
    used_fallback   BOOLEAN DEFAULT FALSE,
    fallback_from   TEXT,              -- core -> edge
    
    -- Версия синтезатора
    synthesizer_version TEXT,
    
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_final_outputs_request ON astrofin_quality.final_outputs(request_id);
CREATE INDEX idx_final_outputs_verdict ON astrofin_quality.final_outputs(verdict, created_at DESC);

-- ============================================
-- 5) DATA_LINEAGE — воспроизводимость данных
-- ============================================
CREATE TABLE astrofin_quality.data_lineage (
    lineage_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id      UUID REFERENCES astrofin_quality.requests(request_id),
    
    source          TEXT NOT NULL,     -- 'coingecko' / 'binance' / 'local'
    source_params   JSONB,             -- параметры запроса
    fetched_at      TIMESTAMPTZ,
    
    -- Снапшот
    data_hash       TEXT,              -- checksum данных
    data_sample     JSONB,              -- небольшой семпл для отладки
    
    -- Версии
    feature_pipeline_version TEXT,
    
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_data_lineage_request ON astrofin_quality.data_lineage(request_id);

-- ============================================
-- 6) FEEDBACK — обратная связь
-- ============================================
CREATE TABLE astrofin_quality.feedback (
    feedback_id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id      UUID NOT NULL REFERENCES astrofin_quality.requests(request_id),
    
    -- Тип feedback
    source          TEXT NOT NULL,      -- 'user' / 'validator' / 'market' / 'system'
    user_id         TEXT,
    
    -- Оценка качества (0-10)
    usefulness      INTEGER CHECK (usefulness BETWEEN 0 AND 10),
    accuracy        INTEGER CHECK (accuracy BETWEEN 0 AND 10),
    
    -- Что именно оцениваем
    feedback_type   TEXT,               -- 'overall' / 'signal' / 'timing' / 'levels'
    
    -- Текстовый feedback
    comment         TEXT,
    
    -- Рыночный исход (для backtest)
    market_outcome  JSONB,              -- {"direction": "up", "return_pct": 5.2, "hit_sl": false}
    
    -- Валидация
    validated       BOOLEAN DEFAULT FALSE,
    validated_by    TEXT,
    
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_feedback_request ON astrofin_quality.feedback(request_id);
CREATE INDEX idx_feedback_user ON astrofin_quality.feedback(user_id, created_at DESC);

-- ============================================
-- 7) BACKTEST_RUNS — результаты прогонов
-- ============================================
CREATE TABLE astrofin_quality.backtest_runs (
    run_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Контекст
    reason          TEXT NOT NULL,      -- 'scheduled' / 'post_cp' / 'incident'
    related_cp_id   TEXT,               -- ссылка на CP в Obsidian
    related_btr_id  UUID REFERENCES astrofin_quality.backtest_runs(run_id),  -- для A/B
    
    -- Параметры
    period_start    TIMESTAMPTZ NOT NULL,
    period_end      TIMESTAMPTZ NOT NULL,
    assets          TEXT[],
    horizons        TEXT[],
    modes           TEXT[],             -- 'core' / 'edge' / 'both'
    
    -- Trading params
    commission_pct  FLOAT DEFAULT 0.1,
    slippage_pct    FLOAT DEFAULT 0.05,
    
    -- Версии
    prompt_version_id      UUID REFERENCES astrofin_quality.versions(version_id),
    model_version_id       UUID REFERENCES astrofin_quality.versions(version_id),
    embed_version_id       UUID REFERENCES astrofin_quality.versions(version_id),
    index_version_id       UUID REFERENCES astrofin_quality.versions(version_id),
    code_version_hash      TEXT,
    
    -- Результаты (JSONB для гибкости)
    results         JSONB,              -- детальные результаты
    summary         JSONB,              -- агрегированные KPIs
    
    -- Решение
    decision        TEXT,               -- 'release' / 'iterate' / 'reject' / 'rollback'
    notes           TEXT,
    
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_btr_reason ON astrofin_quality.backtest_runs(reason, created_at DESC);

-- ============================================
-- 8) METRICS — агрегаты метрик
-- ============================================
CREATE TABLE astrofin_quality.metrics (
    metric_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Измерение
    metric_name     TEXT NOT NULL,      -- 'accuracy' / 'brier_score' / 'sharpe' / etc
    asset           TEXT,
    horizon         TEXT,
    mode            TEXT,               -- 'core' / 'edge'
    
    -- Время
    window_start    TIMESTAMPTZ NOT NULL,
    window_end      TIMESTAMPTZ NOT NULL,
    window_type     TEXT NOT NULL,      -- 'daily' / 'weekly' / 'monthly'
    
    -- Значение
    value           FLOAT NOT NULL,
    sample_size     INTEGER,            -- N наблюдений
    
    -- Дополнительно
    confidence_interval JSONB,
    tags            TEXT[],
    
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_metrics_name_time ON astrofin_quality.metrics(metric_name, mode, window_end DESC);
CREATE INDEX idx_metrics_asset ON astrofin_quality.metrics(asset, metric_name, window_end DESC);

-- ============================================
-- 9) CHANGE_PROPOSALS — для отслеживания CP
-- ============================================
CREATE TABLE astrofin_quality.change_proposals (
    cp_id           TEXT PRIMARY KEY,  -- 'CP-20260108-1430'
    
    -- Статус
    status          TEXT DEFAULT 'draft',  -- draft / testing / released / rejected / rolled_back
    
    -- Компонент
    component       TEXT NOT NULL,
    risk_level      TEXT DEFAULT 'low',
    
    -- Описание
    problem         TEXT,
    change_summary  TEXT,
    
    -- Тестирование
    backtest_run_id UUID REFERENCES astrofin_quality.backtest_runs(run_id),
    
    -- Результат
    decision        TEXT,
    decision_notes  TEXT,
    
    -- Версии до/после
    version_before  UUID REFERENCES astrofin_quality.versions(version_id),
    version_after   UUID REFERENCES astrofin_quality.versions(version_id),
    
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    decided_at      TIMESTAMPTZ
);

CREATE INDEX idx_cp_status ON astrofin_quality.change_proposals(status, created_at DESC);

-- ============================================
-- 10) INCIDENTS — деградации
-- ============================================
CREATE TABLE astrofin_quality.incidents (
    incident_id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Триггер
    trigger_metric  TEXT NOT NULL,
    threshold_value FLOAT,
    actual_value    FLOAT,
    
    -- Статус
    status          TEXT DEFAULT 'open',  -- open / investigating / resolved / escalated
    
    -- Детали
    description     TEXT,
    affected_modes  TEXT[],
    affected_assets TEXT[],
    
    -- Действия
    actions_taken   TEXT[],
    related_cp_id   TEXT REFERENCES astrofin_quality.change_proposals(cp_id),
    
    resolved_at     TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_incidents_status ON astrofin_quality.incidents(status, created_at DESC);

-- ============================================================
-- 10) EXTERNAL_SIGNALS — Timing Solution integration (Вариант B)
-- ============================================================
CREATE TABLE IF NOT EXISTS astrofin_quality.external_signals (
    signal_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id      UUID REFERENCES astrofin_quality.requests(request_id),
    source          TEXT NOT NULL,  -- 'timing_solution', 'tradingview', etc.
    method          TEXT NOT NULL,  -- 'TS_Spectrum', 'Wavelet', 'Chaos'
    asset           TEXT NOT NULL,
    generated_at    TIMESTAMPTZ NOT NULL,  -- Когда TS сгенерировал
    received_at     TIMESTAMPTZ DEFAULT NOW(),  -- Когда мы получили
    data_hash       TEXT NOT NULL,  -- SHA256 контента для версионирования
    
    -- Циклические данные
    phase           TEXT,           -- peak/trough/ascending/descending
    cycle_strength  FLOAT CHECK (cycle_strength BETWEEN 0 AND 1),
    cycle_score     FLOAT CHECK (cycle_score BETWEEN 0 AND 1),  -- quality
    
    -- Направление
    direction       TEXT,           -- up/down/neutral
    confidence      INTEGER CHECK (confidence BETWEEN 0 AND 100),
    
    -- Окна разворота (JSONB для массива)
    turning_windows JSONB DEFAULT '[]',
    
    -- Дополнительные данные
    raw_data        JSONB,          -- полный JSON от источника
    metadata        JSONB DEFAULT '{}',
    
    -- Контроль качества
    is_stale        BOOLEAN DEFAULT FALSE,  -- data_age > threshold
    repaint_flag    BOOLEAN DEFAULT FALSE,  -- подозрение на repainting
    used_in_output  BOOLEAN DEFAULT FALSE   -- был ли использован
);

CREATE INDEX IF NOT EXISTS idx_external_signals_asset_time 
    ON astrofin_quality.external_signals(asset, generated_at DESC);
CREATE INDEX IF NOT EXISTS idx_external_signals_source 
    ON astrofin_quality.external_signals(source, generated_at DESC);

COMMENT ON TABLE astrofin_quality.external_signals IS 
'Eternal signal sources: Timing Solution, TradingView indicators, etc.';
