# AstroFin Sentinel V5 — Database Architecture Research (2026)

## Role
Senior Database Architect & AI Systems Engineer with 15+ years experience designing high-performance, time-series, and vector-enabled databases for financial and AI-agent systems.

---

## Project Context

**AstroFinSentinelV5** — multi-agent trading system combining:

- **Real-time + historical data**: Metals (Gold, Silver, Nickel, etc.) and cryptocurrencies (BTC, ETH, XMR)
- **Astrological data**: Planetary positions, aspects, retrogrades, lunar phases via Swiss Ephemeris
- **KARL approach**: OAP + TTC + DecisionRecord + AuditLog + replay buffer
- **Multi-agent architecture**: Semantic memory, grounding, uncertainty estimation, self-questioning

### Current State (SQLite → PostgreSQL migration needed)

| DB | Tables | Rows | Size | Issue |
|----|--------|------|------|-------|
| `core/belief.db` | agent_beliefs, agent_belief_history, agent_selection_log | 3 agents, 6 history, 0 selections | <1MB | No MACRO_POOL tracking |
| `core/history.db` | sessions, backtest_runs | 71 sessions | ~2MB | ALL NEUTRAL (bug fixed in ATOM-017) |
| `backtest/metrics_history.db` | backtest_runs | 12 runs | ~1MB | Separate DB = no joins |

### Critical Bug Found (ATOM-017 Fixed)
**Problem**: All 71 sessions = NEUTRAL 50 confidence. Root cause = only 4 agents running (Technical pool only). **FIXED**: Now all 8+ agents running.

---

## Research Sections

### 1. Requirements Analysis

#### Data Types & Loads

| Category | Data Type | Volume (1Y) | Volume (3Y) | Access Pattern |
|----------|-----------|-------------|-------------|----------------|
| **Market OHLCV** | Time-series | ~500MB | ~2GB | Read-heavy, daily aggregation |
| **Agent Signals** | Relational + JSON | ~50MB | ~200MB | Random access, full scans |
| **Planetary Positions** | Time-series | ~100MB | ~300MB | Read-heavy, interpolation |
| **Decision Records** | Audit (append-only) | ~200MB | ~1GB | Sequential writes, rare updates |
| **Vector Embeddings** | Vector (1536-dim) | ~500MB | ~2GB | ANN search, HNSW |
| **Thompson Beliefs** | Relational | <1MB | <1MB | Random access, per-session updates |
| **Backtest Results** | Analytical | ~20MB | ~100MB | Full table scans |

#### Critical Use Cases (Priority Order)

1. **Real-time signals**: <100ms latency, current planetary positions + agent synthesis
2. **Backtesting**: Full table scans across sessions, historical OHLCV joins
3. **KARL learning**: Replay buffer queries, similar trajectory search
4. **RAG for agents**: ANN vector search for context retrieval
5. **Audit & reproducibility**: Immutable DecisionRecord with state hash
6. **Thompson sampling**: Random access to agent beliefs, Bayesian updates

---

### 2. Technology Comparison (2026)

#### Comparison Table

| Technology | Time-Series | Vector Search | ACID | Cost | LangGraph | Python |
|-----------|-------------|---------------|------|------|-----------|--------|
| **PostgreSQL + pgvector + TimescaleDB** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ✅ Full | $ | ✅ Native | ✅ Excellent |
| **ClickHouse** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⚠️ | $$$ | ⚠️ | ⚠️ |
| **Cassandra / ScyllaDB** | ⭐⭐⭐⭐ | ❌ | ⚠️ | $ | ❌ | ⚠️ |
| **DuckDB / MotherDuck** | ⭐⭐⭐ | ⭐⭐⭐ | ⚠️ | $ | ⚠️ | ✅ |
| **Qdrant** | N/A | ⭐⭐⭐⭐⭐ | ⚠️ | $$ | ⚠️ | ✅ |
| **Weaviate** | N/A | ⭐⭐⭐⭐⭐ | ⚠️ | $$ | ⚠️ | ✅ |
| **Pinecone** | N/A | ⭐⭐⭐⭐⭐ | ⚠️ | $$$ | ⚠️ | ✅ |
| **Milvus** | N/A | ⭐⭐⭐⭐ | ⚠️ | $ | ⚠️ | ✅ |

#### Winner: PostgreSQL + pgvector + TimescaleDB

**Reasons:**
1. **Unified architecture**: Single DB for relational, time-series, and vector data
2. **TimescaleDB**: Native hypertables, automatic partitioning, 10-100x compression
3. **pgvector**: HNSW index support v0.5+, competitive with specialized vector DBs
4. **ACID**: Critical for financial audit requirements
5. **LangGraph**: Native checkpointing support
6. **Cost**: $20-500/month vs $1000+ for managed alternatives

---

### 3. Recommended Architecture

#### Primary Stack
- **PostgreSQL 16** (latest features: logical replication, JSON Path)
- **TimescaleDB 2.14** (hypertable compression, continuous aggregates)
- **pgvector 0.7** (HNSW + IVF-PQ for memory efficiency)

#### Hot / Warm / Cold Strategy

| Tier | Data | Retention | Compression |
|------|------|-----------|-------------|
| **Hot** (SSD NVMe) | sessions, agent_beliefs, current month decisions | 0-30 days | 3-5x |
| **Warm** (HDD) | older decisions, replay_buffer | 30-365 days | 10-20x |
| **Cold** (S3/Glacier) | OHLCV history, planetary positions | 1-5 years | 20-50x |

---

### 4. Schema Design (Key Tables)

```sql
-- Sessions hypertable
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id TEXT UNIQUE NOT NULL,
    symbol TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    final_signal TEXT NOT NULL,
    final_confidence INTEGER NOT NULL DEFAULT 50,
    final_output JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
SELECT create_hypertable('sessions', 'created_at', chunk_time_interval => INTERVAL '1 day');

-- Agent beliefs (Thompson sampling)
CREATE TABLE agent_beliefs (
    agent_name TEXT PRIMARY KEY,
    pool_name TEXT NOT NULL,
    alpha REAL NOT NULL DEFAULT 1.0,
    beta REAL NOT NULL DEFAULT 1.0,
    total_sessions INTEGER DEFAULT 0
);

-- Decision records (immutable audit)
CREATE TABLE decision_records (
    id SERIAL PRIMARY KEY,
    decision_id TEXT UNIQUE NOT NULL,
    session_id TEXT REFERENCES sessions(session_id),
    state_hash TEXT NOT NULL,
    q_star REAL NOT NULL,
    confidence_final INTEGER NOT NULL,
    final_action TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
) PARTITION BY RANGE (created_at);

-- Replay buffer (vector embeddings)
CREATE TABLE replay_buffer (
    id SERIAL PRIMARY KEY,
    trajectory_id TEXT NOT NULL,
    embedding VECTOR(1536),
    outcome REAL NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX ON replay_buffer USING ivfflat (embedding vector_cosine_ops);

-- Planetary positions (hypertable)
CREATE TABLE planetary_positions (
    timestamp TIMESTAMPTZ NOT NULL,
    planet TEXT NOT NULL,
    longitude REAL NOT NULL,
    nakshatra INTEGER,
    PRIMARY KEY (timestamp, planet)
) PARTITION BY RANGE (timestamp);
```

---

### 5. Integration with KARL

```python
# LangGraph checkpointing → PostgreSQL
from langgraph.checkpoint.postgres import PostgresSaver

checkpointer = PostgresSaver.from_conn_string(DATABASE_URL)
graph.compile(checkpointer=checkpointer)

# Thompson sampling → agent_beliefs
async def thompson_select(agents: list[Agent]) -> Agent:
    sampled = {a.name: beta.rvs(a.alpha, a.beta) for a in agents}
    winner = max(sampled, key=sampled.get)
    # Update beliefs
    await db.execute(
        "UPDATE agent_beliefs SET alpha = alpha + 1 WHERE agent_name = $1",
        winner
    )
```

---

### 6. Migration Plan

| Step | Action | Effort | Risk |
|------|--------|--------|------|
| 1 | Export SQLite → PostgreSQL (pgloader) | 2h | Low |
| 2 | Create hypertables with compression | 1h | Low |
| 3 | Add pgvector for embeddings | 1h | Medium |
| 4 | Update KARL to use new schema | 4h | Medium |
| 5 | Performance testing & indexing | 2h | Low |
| 6 | Production cutover | 1h | High |

---

### 7. Risks & Alternatives

**Risks:**
- PostgreSQL vector search slower than specialized DBs at scale (>1M vectors)
- TimescaleDB licensing (Apache 2, but enterprise features require license)

**Alternatives:**
- Add **Qdrant** as sidecar for embeddings only (if >1M vectors)
- Use **Neon** for serverless PostgreSQL (if，不想管理基础设施)

---

## Recommendations

### Immediate (Week 1)
1. Export current SQLite data to PostgreSQL
2. Create hypertables with compression
3. Update KARL code to use PostgreSQL

### Short-term (Month 1)
1. Add pgvector HNSW index for replay buffer
2. Implement continuous aggregates for OHLCV
3. Set up monitoring (Prometheus + Grafana)

### Long-term (Year 1)
1. Consider Qdrant if vector search becomes bottleneck
2. Implement data tiering (hot/warm/cold)
3. Add read replicas for horizontal scaling

---

**Priority Implementation Plan:**

1. **Step 1**: `pip install psycopg2-binary sqlalchemy alembic timescaledb`
2. **Step 2**: Create `migrations/001_sqlite_to_postgres.py` using pgloader
3. **Step 3**: Update `core/history_db.py` to use SQLAlchemy + PostgreSQL
