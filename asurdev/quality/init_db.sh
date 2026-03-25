#!/bin/bash
# asurdev Sentinel — Initialize Quality Database
# Run on Acer-2011: psql -h localhost -U postgres -d postgres -f init_quality.sql

set -e

echo "=== asurdev Sentinel Quality DB Init ==="

psql -v ON_ERROR_STOP=1 <<-'EOSQL'

-- Создать схему
CREATE SCHEMA IF NOT EXISTS asurdev_quality;

-- Создать роль для приложения (только INSERT/SELECT)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'sentinel_qa') THEN
        CREATE ROLE sentinel_qa WITH LOGIN PASSWORD 'CHANGE_ME';
    END IF;
END
$$;

-- Grant permissions
GRANT USAGE ON SCHEMA asurdev_quality TO sentinel_qa;
GRANT INSERT, SELECT ON ALL TABLES IN SCHEMA asurdev_quality TO sentinel_qa;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA asurdev_quality TO sentinel_qa;

-- ============================================================
-- TABLES (упрощённая версия для инициализации)
-- ============================================================

-- VERSIONS
CREATE TABLE IF NOT EXISTS asurdev_quality.versions (
    version_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    component       TEXT NOT NULL,
    version_name    TEXT NOT NULL,
    version_hash    TEXT,
    description     TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- REQUESTS
CREATE TABLE IF NOT EXISTS asurdev_quality.requests (
    request_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp       TIMESTAMPTZ DEFAULT NOW(),
    user_id         TEXT,
    session_id      TEXT,
    asset           TEXT NOT NULL,
    horizon         TEXT NOT NULL,
    mode            TEXT NOT NULL,
    latitude        FLOAT,
    longitude       FLOAT,
    prompt_version_id      UUID REFERENCES asurdev_quality.versions(version_id),
    model_version_id       UUID REFERENCES asurdev_quality.versions(version_id),
    embed_version_id       UUID REFERENCES asurdev_quality.versions(version_id),
    index_version_id       UUID REFERENCES asurdev_quality.versions(version_id),
    code_version_hash     TEXT,
    status          TEXT DEFAULT 'pending',
    error_message   TEXT,
    client_ip       TEXT,
    user_agent      TEXT
);

-- AGENT_RUNS
CREATE TABLE IF NOT EXISTS asurdev_quality.agent_runs (
    run_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id      UUID NOT NULL REFERENCES asurdev_quality.requests(request_id),
    agent_name      TEXT NOT NULL,
    agent_version   TEXT,
    inputs_summary  JSONB,
    rag_doc_ids     TEXT[],
    data_refs       JSONB,
    signal          TEXT NOT NULL,
    confidence      INTEGER CHECK (confidence BETWEEN 0 AND 100),
    rationale       TEXT,
    risk_flags      TEXT[],
    latency_ms      INTEGER,
    tokens_in       INTEGER,
    tokens_out      INTEGER,
    errors          TEXT,
    agent_confidence_self INTEGER,
    started_at      TIMESTAMPTZ DEFAULT NOW(),
    completed_at    TIMESTAMPTZ
);

-- FINAL_OUTPUTS
CREATE TABLE IF NOT EXISTS asurdev_quality.final_outputs (
    output_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id       UUID UNIQUE NOT NULL REFERENCES asurdev_quality.requests(request_id),
    verdict          TEXT NOT NULL,
    action           TEXT,
    confidence       INTEGER CHECK (confidence BETWEEN 0 AND 100),
    entry_zone       TEXT,
    stop_loss        TEXT,
    take_profit_1    TEXT,
    take_profit_2    TEXT,
    timeframe        TEXT,
    summary          TEXT,
    conditions       TEXT[],
    votes            JSONB,
    agreement_score  FLOAT,
    used_fallback    BOOLEAN DEFAULT FALSE,
    fallback_from    TEXT,
    synthesizer_version TEXT,
    created_at       TIMESTAMPTZ DEFAULT NOW()
);

-- DATA_LINEAGE
CREATE TABLE IF NOT EXISTS asurdev_quality.data_lineage (
    lineage_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id      UUID REFERENCES asurdev_quality.requests(request_id),
    source          TEXT NOT NULL,
    source_params   JSONB,
    fetched_at      TIMESTAMPTZ,
    data_hash       TEXT,
    data_sample     JSONB,
    feature_pipeline_version TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- FEEDBACK
CREATE TABLE IF NOT EXISTS asurdev_quality.feedback (
    feedback_id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id      UUID NOT NULL REFERENCES asurdev_quality.requests(request_id),
    source          TEXT NOT NULL,
    user_id         TEXT,
    usefulness      INTEGER CHECK (usefulness BETWEEN 0 AND 10),
    accuracy        INTEGER CHECK (accuracy BETWEEN 0 AND 10),
    feedback_type   TEXT,
    comment         TEXT,
    market_outcome  JSONB,
    validated       BOOLEAN DEFAULT FALSE,
    validated_by    TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- BACKTEST_RUNS
CREATE TABLE IF NOT EXISTS asurdev_quality.backtest_runs (
    run_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    reason          TEXT NOT NULL,
    related_cp_id   TEXT,
    related_btr_id  UUID REFERENCES asurdev_quality.backtest_runs(run_id),
    period_start    TIMESTAMPTZ NOT NULL,
    period_end      TIMESTAMPTZ NOT NULL,
    assets          TEXT[],
    horizons        TEXT[],
    modes           TEXT[],
    commission_pct  FLOAT DEFAULT 0.1,
    slippage_pct    FLOAT DEFAULT 0.05,
    prompt_version_id      UUID REFERENCES asurdev_quality.versions(version_id),
    model_version_id       UUID REFERENCES asurdev_quality.versions(version_id),
    embed_version_id       UUID REFERENCES asurdev_quality.versions(version_id),
    index_version_id       UUID REFERENCES asurdev_quality.versions(version_id),
    code_version_hash     TEXT,
    results         JSONB,
    summary         JSONB,
    decision        TEXT,
    notes           TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- METRICS
CREATE TABLE IF NOT EXISTS asurdev_quality.metrics (
    metric_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    metric_name     TEXT NOT NULL,
    asset           TEXT,
    horizon         TEXT,
    mode            TEXT,
    window_start    TIMESTAMPTZ NOT NULL,
    window_end      TIMESTAMPTZ NOT NULL,
    window_type     TEXT NOT NULL,
    value           FLOAT NOT NULL,
    sample_size     INTEGER,
    confidence_interval JSONB,
    tags            TEXT[],
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- CHANGE_PROPOSALS
CREATE TABLE IF NOT EXISTS asurdev_quality.change_proposals (
    cp_id           TEXT PRIMARY KEY,
    status          TEXT DEFAULT 'draft',
    component       TEXT NOT NULL,
    risk_level      TEXT DEFAULT 'low',
    problem         TEXT,
    change_summary  TEXT,
    backtest_run_id UUID REFERENCES asurdev_quality.backtest_runs(run_id),
    decision        TEXT,
    decision_notes  TEXT,
    version_before  UUID REFERENCES asurdev_quality.versions(version_id),
    version_after   UUID REFERENCES asurdev_quality.versions(version_id),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    decided_at      TIMESTAMPTZ
);

-- INCIDENTS
CREATE TABLE IF NOT EXISTS asurdev_quality.incidents (
    incident_id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trigger_metric  TEXT NOT NULL,
    threshold_value FLOAT,
    actual_value    FLOAT,
    status          TEXT DEFAULT 'open',
    description     TEXT,
    affected_modes  TEXT[],
    affected_assets TEXT[],
    actions_taken   TEXT[],
    related_cp_id   TEXT REFERENCES asurdev_quality.change_proposals(cp_id),
    resolved_at     TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- INDEXES
CREATE INDEX IF NOT EXISTS idx_requests_asset_time ON asurdev_quality.requests(asset, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_requests_user ON asurdev_quality.requests(user_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_agent_runs_request ON asurdev_quality.agent_runs(request_id);
CREATE INDEX IF NOT EXISTS idx_final_outputs_verdict ON asurdev_quality.final_outputs(verdict, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_feedback_request ON asurdev_quality.feedback(request_id);
CREATE INDEX IF NOT EXISTS idx_metrics_name_time ON asurdev_quality.metrics(metric_name, mode, window_end DESC);
CREATE INDEX IF NOT EXISTS idx_versions_component ON asurdev_quality.versions(component, created_at DESC);

-- ============================================================
-- INITIAL DATA: Versions
-- ============================================================

INSERT INTO asurdev_quality.versions (component, version_name, description) VALUES
    ('prompt', 'v1.0.0', 'Initial prompt set'),
    ('model', 'qwen2.5-coder:32b', 'Main reasoning model'),
    ('model', 'gemma:2b', 'Lightweight model for edge'),
    ('embed', 'nomic-embed-text', 'Embeddings for RAG'),
    ('index', 'v1.0.0', 'Initial RAG index')
ON CONFLICT DO NOTHING;

-- ============================================================
-- FUNCTION: Auto-version trigger
-- ============================================================

CREATE OR REPLACE FUNCTION asurdev_quality.log_version_change()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'UPDATE' AND NEW.version_name IS DISTINCT FROM OLD.version_name THEN
        INSERT INTO asurdev_quality.change_proposals (
            cp_id, component, change_summary, status
        ) VALUES (
            'AUTO-' || TO_CHAR(NOW(), 'YYYYMMDD-HH24MI') || '-' || NEW.component,
            NEW.component,
            'Auto-bumped: ' || OLD.version_name || ' → ' || NEW.version_name,
            'draft'
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_version_change ON asurdev_quality.versions;
CREATE TRIGGER trg_version_change
AFTER UPDATE ON asurdev_quality.versions
FOR EACH ROW EXECUTE FUNCTION asurdev_quality.log_version_change();

-- ============================================================
-- VIEW: Recent quality metrics
-- ============================================================

CREATE OR REPLACE VIEW asurdev_quality.recent_quality AS
WITH recent AS (
    SELECT 
        r.mode,
        COUNT(*) as n_requests,
        COUNT(*) FILTER (WHERE fo.verdict IS NOT NULL) as n_outputs,
        AVG(fo.confidence)::int as avg_confidence,
        COUNT(*) FILTER (WHERE fo.used_fallback) as n_fallbacks
    FROM asurdev_quality.requests r
    LEFT JOIN asurdev_quality.final_outputs fo ON r.request_id = fo.request_id
    WHERE r.timestamp > NOW() - INTERVAL '7 days'
    GROUP BY r.mode
)
SELECT 
    mode,
    n_requests,
    n_outputs,
    avg_confidence,
    (n_fallbacks * 100.0 / NULLIF(n_requests, 0))::int as fallback_pct
FROM recent;

COMMENT ON VIEW asurdev_quality.recent_quality IS 'Quick quality check for last 7 days';

-- Grant read access to monitoring role
GRANT SELECT ON asurdev_quality.recent_quality TO sentinel_qa;

EOSQL

echo "=== Done ==="
echo "Schema created. Run as: psql -h 192.168.30.100 -U sentinel_qa -d postgres -f init_quality.sql"
