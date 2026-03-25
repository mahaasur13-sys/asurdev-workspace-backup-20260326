"""
Quality Database Client для asurdev Sentinel
ORM для работы с asurdev_quality schema
"""
import os
import json
import uuid
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

import psycopg2
from psycopg2.extras import RealDictCursor, Json


def get_db_config() -> dict:
    """Конфиг из environment / secrets"""
    return {
        "host": os.getenv("asurdev_DB_HOST", "192.168.30.100"),
        "port": int(os.getenv("asurdev_DB_PORT", "5432")),
        "database": os.getenv("asurdev_DB_NAME", "postgres"),
        "schema": "asurdev_quality",
        "user": os.getenv("asurdev_DB_USER", "sentinel_qa"),
        "password": os.getenv("asurdev_DB_PASSWORD", ""),
    }


@contextmanager
def get_cursor():
    """Курсор с автокоммитом"""
    config = get_db_config()
    conn = psycopg2.connect(
        host=config["host"],
        port=config["port"],
        dbname=config["database"],
        user=config["user"],
        password=config["password"],
        options=f"-c search_path={config['schema']},public"
    )
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


class QualityDB:
    """Основной клиент для Quality DB"""
    
    # ========================
    # REQUESTS
    # ========================
    
    def log_request(self, req: Dict[str, Any]) -> str:
        """Log request event"""
        request_id = req.get("request_id", str(uuid.uuid4()))
        
        with get_cursor() as cur:
            cur.execute("""
                INSERT INTO requests (
                    request_id, timestamp, user_id, asset, horizon, mode,
                    version_snapshot, snapshot_checksum, latitude, longitude, status
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'completed')
                ON CONFLICT (request_id) DO NOTHING
            """, (
                request_id,
                req.get("timestamp", datetime.utcnow().isoformat()),
                req.get("user_id", "local"),
                req.get("asset"),
                req.get("horizon", "1d"),
                req.get("mode", "core_preferred"),
                Json(req.get("version_snapshot", {})),
                req.get("snapshot_checksum", ""),
                req.get("latitude"),
                req.get("longitude")
            ))
        
        return request_id
    
    def get_requests_in_range(
        self,
        start_date: str,
        end_date: str,
        asset: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get requests in date range"""
        with get_cursor() as cur:
            query = """
                SELECT * FROM requests
                WHERE timestamp BETWEEN %s AND %s
            """
            params = [start_date, end_date]
            
            if asset:
                query += " AND asset = %s"
                params.append(asset)
            
            query += " ORDER BY timestamp"
            cur.execute(query, params)
            return list(cur.fetchall())
    
    def get_request(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Get single request"""
        with get_cursor() as cur:
            cur.execute("SELECT * FROM requests WHERE request_id = %s", (request_id,))
            row = cur.fetchone()
            return dict(row) if row else None
    
    # ========================
    # AGENT RUNS
    # ========================
    
    def log_agent_run(self, run: Dict[str, Any]) -> str:
        """Log agent decision"""
        with get_cursor() as cur:
            cur.execute("""
                INSERT INTO agent_runs (
                    agent_run_id, request_id, agent_name, agent_version,
                    input_state_checksum, input_state, rag_refs,
                    output_recommendation, output_confidence, rationale,
                    risk_flags, latency_ms, tokens_used, error, timestamp
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                run.get("agent_run_id", str(uuid.uuid4())),
                run["request_id"],
                run["agent_name"],
                run["agent_version"],
                run.get("input_state_checksum", ""),
                Json(run.get("input_state", {})),
                run.get("rag_refs", []),
                run["output_recommendation"],
                run.get("output_confidence", 0.0),
                run.get("rationale", ""),
                run.get("risk_flags", []),
                run.get("latency_ms", 0),
                run.get("tokens_used", 0),
                run.get("error"),
                run.get("timestamp", datetime.utcnow().isoformat())
            ))
        return run.get("agent_run_id", "")
    
    def get_agent_runs_for_request(self, request_id: str) -> List[Dict[str, Any]]:
        """Get all runs for request"""
        with get_cursor() as cur:
            cur.execute("""
                SELECT * FROM agent_runs
                WHERE request_id = %s
                ORDER BY timestamp
            """, (request_id,))
            return [dict(row) for row in cur.fetchall()]
    
    # ========================
    # FINAL OUTPUTS
    # ========================
    
    def log_final_output(self, output: Dict[str, Any]) -> str:
        """Log final synthesis"""
        with get_cursor() as cur:
            cur.execute("""
                INSERT INTO final_outputs (
                    output_id, request_id, synthesis, final_confidence,
                    mode_used, execution_time_ms, what_would_change_mind, timestamp
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                output.get("output_id", str(uuid.uuid4())),
                output["request_id"],
                Json(output.get("synthesis", {})),
                output.get("final_confidence", 0.0),
                output.get("mode_used", "unknown"),
                output.get("execution_time_ms", 0),
                output.get("what_would_change_mind", []),
                output.get("timestamp", datetime.utcnow().isoformat())
            ))
        return output.get("output_id", "")
    
    def get_outputs_for_requests(self, request_ids: List[str]) -> List[Dict[str, Any]]:
        """Get outputs for multiple requests"""
        if not request_ids:
            return []
        
        with get_cursor() as cur:
            cur.execute("""
                SELECT * FROM final_outputs
                WHERE request_id = ANY(%s)
            """, (request_ids,))
            return [dict(row) for row in cur.fetchall()]
    
    # ========================
    # DATA LINEAGE
    # ========================
    
    def log_data_lineage(self, lineage: Dict[str, Any]) -> str:
        """Log data context"""
        with get_cursor() as cur:
            cur.execute("""
                INSERT INTO data_lineage (
                    lineage_id, request_id, source, params, fetched_at,
                    checksum, features_version, data_sample
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                lineage.get("lineage_id", str(uuid.uuid4())),
                lineage["request_id"],
                lineage["source"],
                Json(lineage.get("params", {})),
                lineage["fetched_at"],
                lineage.get("checksum", ""),
                lineage.get("features_version", "unset"),
                Json(lineage.get("data_sample", {}))
            ))
        return lineage.get("lineage_id", "")
    
    # ========================
    # VERSIONS
    # ========================
    
    def log_version(
        self,
        component: str,
        version: str,
        changes: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Log version snapshot"""
        version_id = str(uuid.uuid4())
        
        with get_cursor() as cur:
            cur.execute("""
                INSERT INTO versions (version_id, component, version_name, changes, metadata)
                VALUES (%s, %s, %s, %s, %s)
            """, (version_id, component, version, changes, Json(metadata or {})))
        
        return version_id
    
    def get_current_versions(self) -> Dict[str, str]:
        """Get latest version per component"""
        with get_cursor() as cur:
            cur.execute("""
                SELECT DISTINCT ON (component) component, version_name
                FROM versions
                ORDER BY component, created_at DESC
            """)
            return {row["component"]: row["version_name"] for row in cur.fetchall()}
    
    # ========================
    # METRICS
    # ========================
    
    def log_metrics(
        self,
        period_start: str,
        period_end: str,
        accuracy: float,
        precision: float = 0.0,
        recall: float = 0.0,
        f1: float = 0.0,
        brier_score: float = 0.0,
        total_return: float = 0.0,
        max_drawdown: float = 0.0,
        sharpe: float = 0.0,
        mode_used: str = "core",
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Log aggregated metrics"""
        metric_id = str(uuid.uuid4())
        
        with get_cursor() as cur:
            cur.execute("""
                INSERT INTO metrics (
                    metric_id, period_start, period_end, accuracy, precision,
                    recall, f1, brier_score, total_return, max_drawdown,
                    sharpe, mode_used, metadata
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                metric_id, period_start, period_end, accuracy, precision,
                recall, f1, brier_score, total_return, max_drawdown,
                sharpe, mode_used, Json(metadata or {})
            ))
        
        return metric_id
    
    def get_metrics_history(
        self,
        mode: Optional[str] = None,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """Get metrics history"""
        with get_cursor() as cur:
            query = """
                SELECT * FROM metrics
                WHERE period_end > NOW() - INTERVAL '%s days'
            """
            params = [days]
            
            if mode:
                query += " AND mode_used = %s"
                params.append(mode)
            
            query += " ORDER BY period_end DESC"
            cur.execute(query, params)
            return [dict(row) for row in cur.fetchall()]
    
    # ========================
    # CHANGE PROPOSALS
    # ========================
    
    def log_change_proposal(self, cp: Dict[str, Any]) -> str:
        """Log change proposal"""
        with get_cursor() as cur:
            cur.execute("""
                INSERT INTO change_proposals (
                    cp_id, problem, hypothesis, change_type, change_details,
                    success_criteria, risk, rollback, status, metrics_before,
                    version_snapshot_before, version_snapshot_after, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (cp_id) DO UPDATE SET
                    status = EXCLUDED.status,
                    metrics_after = EXCLUDED.metrics_after,
                    verified_at = NOW()
            """, (
                cp["cp_id"],
                cp["problem"],
                cp["hypothesis"],
                cp["change_type"],
                Json(cp.get("change_details", {})),
                Json(cp.get("success_criteria", {})),
                cp.get("risk", "medium"),
                cp.get("rollback", ""),
                cp.get("status", "draft"),
                Json(cp.get("metrics_before", {})),
                Json(cp.get("version_snapshot_before", {})),
                Json(cp.get("version_snapshot_after", {})),
                cp.get("created_at", datetime.utcnow().isoformat())
            ))
        return cp["cp_id"]
    
    def get_change_proposals(
        self,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get change proposals"""
        with get_cursor() as cur:
            query = "SELECT * FROM change_proposals"
            params = []
            
            if status:
                query += " WHERE status = %s"
                params.append(status)
            
            query += " ORDER BY created_at DESC LIMIT %s"
            params.append(limit)
            
            cur.execute(query, params)
            return [dict(row) for row in cur.fetchall()]
    
    # ========================
    # BACKTEST
    # ========================
    
    def log_backtest_run(
        self,
        reason: str,
        period_start: str,
        period_end: str,
        assets: List[str],
        modes: List[str],
        results: Dict[str, Any],
        decision: Optional[str] = None,
        related_cp_id: Optional[str] = None
    ) -> str:
        """Log backtest run"""
        run_id = str(uuid.uuid4())
        
        with get_cursor() as cur:
            cur.execute("""
                INSERT INTO backtest_runs (
                    run_id, reason, period_start, period_end,
                    assets, horizons, modes, results, decision, related_cp_id
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                run_id, reason, period_start, period_end,
                assets, None, modes, Json(results), decision, related_cp_id
            ))
        
        return run_id
    
    # ========================
    # EXTERNAL SIGNALS (Timing Solution)
    # ========================
    
    def log_external_signal(
        self,
        asset: str,
        source: str,
        signal_type: str,
        signal_data: Dict[str, Any],
        generated_at: str,
        quality_flags: Optional[Dict[str, Any]] = None
    ) -> str:
        """Log external signal (e.g., from Timing Solution)"""
        signal_id = str(uuid.uuid4())
        
        with get_cursor() as cur:
            cur.execute("""
                INSERT INTO external_signals (
                    signal_id, asset, source, signal_type, signal_data,
                    generated_at, quality_flags
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                signal_id, asset, source, signal_type,
                Json(signal_data), generated_at, Json(quality_flags or {})
            ))
        
        return signal_id
    
    def get_latest_signals(
        self,
        asset: str,
        source: Optional[str] = None,
        hours: int = 24
    ) -> List[Dict[str, Any]]:
        """Get recent external signals"""
        with get_cursor() as cur:
            query = """
                SELECT * FROM external_signals
                WHERE asset = %s AND generated_at > NOW() - INTERVAL '%s hours'
            """
            params = [asset, hours]
            
            if source:
                query += " AND source = %s"
                params.append(source)
            
            query += " ORDER BY generated_at DESC"
            cur.execute(query, params)
            return [dict(row) for row in cur.fetchall()]


# Singleton
_db = None

def get_quality_db() -> QualityDB:
    global _db
    if _db is None:
        _db = QualityDB()
    return _db
