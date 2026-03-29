# AstroFin V5 - Database Setup

## Quick Start

```bash
# 1. Copy env
cp .env.db.example .env
# Edit .env with your password

# 2. Start PostgreSQL + Redis
docker-compose up -d postgres redis

# 3. Run schema
PGPASSWORD=your_password psql -h localhost -U astrofin -d astrofin -f schema/001_initial.sql

# 4. Verify
psql -h localhost -U astrofin -d astrofin -c "\dT"
```

## Schema (schema/001_initial.sql)

- TimescaleDB hypertables for time-series tables
- BRIN indexes on timestamps
- HNSW indexes for vector search
- HLL for cardinality estimation
- RLS policies for security
- Retention policies (90 days sessions, 2 years audit)
- Compression policies after 1 day

## Key Tables

| Table | Type | Retention |
|-------|------|----------|
| sessions | hypertable | 90 days |
| agent_signals | hypertable | 90 days |
| agent_selection_log | hypertable | 90 days |
| karl_decision_records | hypertable | 90 days |
| kpi_metrics | hypertable | 90 days |
| agent_beliefs | regular | permanent |
| agent_belief_history | regular | permanent |
| backtest_runs | regular | permanent |
| rag_embeddings | regular + hnsw | permanent |
| audit_log | hypertable | 2 years |

## Migrations

```bash
# Generate migration
alembic revision --autogenerate -m "Add new table"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Models (db/models.py)

SQLAlchemy 2.0 models with type-safe enums.

```python
from db.models import Session, AgentSignal, AgentBelief
from db import get_session

with get_session() as s:
    sessions = s.query(Session).limit(10).all()
```

## KARL Integration (db/karl_replay.py)

PostgreSQL-backed replay buffer for KARL trajectories.

```python
from db.karl_replay import PostgresReplayBuffer

buffer = PostgresReplayBuffer(max_size=10000)
buffer.add(decision_record)
similar = buffer.get_similar(trajectory, threshold=0.3)
```
