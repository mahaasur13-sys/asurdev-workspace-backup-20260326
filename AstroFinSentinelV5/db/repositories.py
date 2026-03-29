"""db/repositories.py — PostgreSQL CRUD Repositories (ATOM-019)
Decision records, agent signals, astro positions, audit log.
"""
import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from db.session import pg_session
from db.models import (
    KARLDecisionRecord, AgentSignal, AstroPosition,
    AuditLogRecord, AgentBelief, BacktestRun,
)

class DecisionRecordRepository:
    @staticmethod
    def save(record: Dict[str, Any]) -> str:
        with pg_session() as s:
            # Extract scalar fields
            dr = KARLDecisionRecord(
                decision_id=record["decision_id"],
                session_id=record.get("session_id"),
                symbol=record.get("symbol", "BTCUSDT"),
                price=record.get("price", 0),
                timeframe=record.get("timeframe", "SWING"),
                regime=record.get("regime", "NORMAL"),
                state_hash=record.get("state_hash"),
                # Trajectories JSON
                top_trajectories_json=json.dumps(record.get("top_trajectories", [])),
                # Ensemble JSON
                selected_ensemble_json=json.dumps(record.get("selected_ensemble", [])),
                q_values_json=json.dumps(record.get("q_values", [])),
                q_star=record.get("q_star", 0.5),
                advantage=record.get("advantage", 0),
                uncertainty_aleatoric=record.get("uncertainty_aleatoric", 0.5),
                uncertainty_epistemic=record.get("uncertainty_epistemic", 0.5),
                uncertainty_total=record.get("uncertainty_total", 0.5),
                confidence_raw=record.get("confidence_raw", 50),
                confidence_final=record.get("confidence_final", 50),
                confidence_adjustments_json=json.dumps(record.get("confidence_adjustments", [])),
                final_action=record.get("final_action", "NEUTRAL"),
                position_pct=record.get("position_pct", 0),
                grounding_passed=record.get("grounding_passed", True),
                reward_estimate=record.get("reward_estimate", 0),
                metadata_json=json.dumps(record.get("metadata", {})),
            )
            s.add(dr)
            return record["decision_id"]

    @staticmethod
    def get_recent(limit: int = 10) -> List[Dict]:
        with pg_session() as s:
            rows = s.query(KARLDecisionRecord).order_by(
                KARLDecisionRecord.created_at.desc()
            ).limit(limit).all()
            return [DecisionRecordRepository._row_to_dict(r) for r in rows]

    @staticmethod
    def get_by_symbol(symbol: str, limit: int = 100) -> List[Dict]:
        with pg_session() as s:
            rows = s.query(KARLDecisionRecord).filter(
                KARLDecisionRecord.symbol == symbol
            ).order_by(KARLDecisionRecord.created_at.desc()).limit(limit).all()
            return [DecisionRecordRepository._row_to_dict(r) for r in rows]

    @staticmethod
    def get_by_regime(regime: str, limit: int = 50) -> List[Dict]:
        with pg_session() as s:
            rows = s.query(KARLDecisionRecord).filter(
                KARLDecisionRecord.regime == regime
            ).order_by(KARLDecisionRecord.created_at.desc()).limit(limit).all()
            return [DecisionRecordRepository._row_to_dict(r) for r in rows]

    @staticmethod
    def count_by_action() -> Dict[str, int]:
        with pg_session() as s:
            from sqlalchemy import func
            rows = s.query(
                KARLDecisionRecord.final_action,
                func.count(KARLDecisionRecord.id)
            ).group_by(KARLDecisionRecord.final_action).all()
            return {r[0]: r[1] for r in rows}

    @staticmethod
    def _row_to_dict(row) -> dict:
        return {
            "decision_id": row.decision_id,
            "session_id": row.session_id,
            "symbol": row.symbol,
            "price": row.price,
            "timeframe": row.timeframe,
            "regime": row.regime,
            "state_hash": row.state_hash,
            "top_trajectories": json.loads(row.top_trajectories_json or "[]"),
            "selected_ensemble": json.loads(row.selected_ensemble_json or "[]"),
            "q_values": json.loads(row.q_values_json or "[]"),
            "q_star": row.q_star,
            "advantage": row.advantage,
            "uncertainty_aleatoric": row.uncertainty_aleatoric,
            "uncertainty_epistemic": row.uncertainty_epistemic,
            "uncertainty_total": row.uncertainty_total,
            "confidence_raw": row.confidence_raw,
            "confidence_final": row.confidence_final,
            "confidence_adjustments": json.loads(row.confidence_adjustments_json or "[]"),
            "final_action": row.final_action,
            "position_pct": row.position_pct,
            "grounding_passed": row.grounding_passed,
            "reward_estimate": row.reward_estimate,
            "metadata": json.loads(row.metadata_json or "{}"),
            "created_at": row.created_at.isoformat() if row.created_at else None,
        }


class AgentSignalRepository:
    @staticmethod
    def save(session_id: str, agent_name: str, signal: str,
             confidence: int, reasoning: str, metadata: Optional[Dict] = None) -> None:
        with pg_session() as s:
            ag = AgentSignal(
                session_id=session_id,
                agent_name=agent_name,
                signal=signal,
                confidence=confidence,
                reasoning=reasoning,
                metadata_json=json.dumps(metadata or {}),
            )
            s.add(ag)

    @staticmethod
    def get_by_session(session_id: str) -> List[Dict]:
        with pg_session() as s:
            rows = s.query(AgentSignal).filter(
                AgentSignal.session_id == session_id
            ).order_by(AgentSignal.created_at).all()
            return [AgentSignalRepository._row_to_dict(r) for r in rows]

    @staticmethod
    def _row_to_dict(row) -> dict:
        return {
            "id": row.id,
            "session_id": row.session_id,
            "agent_name": row.agent_name,
            "signal": row.signal,
            "confidence": row.confidence,
            "reasoning": row.reasoning,
            "metadata": json.loads(row.metadata_json or "{}"),
            "created_at": row.created_at.isoformat() if row.created_at else None,
        }


class AstroPositionRepository:
    @staticmethod
    def save(session_id: str, planet: str, longitude: float,
             latitude: float, speed: float, nakshatra: str,
             rashi: str, metadata: Optional[Dict] = None) -> None:
        with pg_session() as s:
            ap = AstroPosition(
                session_id=session_id,
                planet=planet,
                longitude=longitude,
                latitude=latitude,
                speed=speed,
                nakshatra=nakshatra,
                rashi=rashi,
                metadata_json=json.dumps(metadata or {}),
            )
            s.add(ap)

    @staticmethod
    def get_by_session(session_id: str) -> List[Dict]:
        with pg_session() as s:
            rows = s.query(AstroPosition).filter(
                AstroPosition.session_id == session_id
            ).all()
            return [AstroPositionRepository._row_to_dict(r) for r in rows]

    @staticmethod
    def get_by_time_range(start: datetime, end: datetime) -> List[Dict]:
        with pg_session() as s:
            rows = s.query(AstroPosition).filter(
                AstroPosition.created_at >= start,
                AstroPosition.created_at <= end
            ).all()
            return [AstroPositionRepository._row_to_dict(r) for r in rows]

    @staticmethod
    def _row_to_dict(row) -> dict:
        return {
            "id": row.id,
            "session_id": row.session_id,
            "planet": row.planet,
            "longitude": row.longitude,
            "latitude": row.latitude,
            "speed": row.speed,
            "nakshatra": row.nakshatra,
            "rashi": row.rashi,
            "metadata": json.loads(row.metadata_json or "{}"),
            "created_at": row.created_at.isoformat() if row.created_at else None,
        }


class AuditLogRepository:
    @staticmethod
    def save(session_id: str, decision_id: str, action: str,
             details: Optional[Dict] = None) -> None:
        with pg_session() as s:
            al = AuditLogRecord(
                session_id=session_id,
                decision_id=decision_id,
                action=action,
                details_json=json.dumps(details or {}),
            )
            s.add(al)

    @staticmethod
    def get_recent(limit: int = 100) -> List[Dict]:
        with pg_session() as s:
            rows = s.query(AuditLogRecord).order_by(
                AuditLogRecord.created_at.desc()
            ).limit(limit).all()
            return [AuditLogRepository._row_to_dict(r) for r in rows]

    @staticmethod
    def get_by_decision(decision_id: str) -> List[Dict]:
        with pg_session() as s:
            rows = s.query(AuditLogRecord).filter(
                AuditLogRecord.decision_id == decision_id
            ).all()
            return [AuditLogRepository._row_to_dict(r) for r in rows]

    @staticmethod
    def _row_to_dict(row) -> dict:
        return {
            "id": row.id,
            "session_id": row.session_id,
            "decision_id": row.decision_id,
            "action": row.action,
            "details": json.loads(row.details_json or "{}"),
            "created_at": row.created_at.isoformat() if row.created_at else None,
        }


def get_all_stats() -> dict:
    """Aggregate stats across all repositories."""
    stats = {}
    try:
        stats["postgres_available"] = is_postgres_available()
        if stats["postgres_available"]:
            with pg_session() as s:
                from sqlalchemy import func
                stats["decision_records"] = s.query(KARLDecisionRecord).count()
                stats["agent_signals"] = s.query(AgentSignal).count()
                stats["astro_positions"] = s.query(AstroPosition).count()
                stats["audit_records"] = s.query(AuditLogRecord).count()
                stats["db_pool"] = get_db_stats()
        else:
            stats["postgres_available"] = False
    except Exception as e:
        stats["error"] = str(e)
    return stats
