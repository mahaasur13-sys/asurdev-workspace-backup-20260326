"""
asurdev Sentinel — Quality Logger
4-layer logging: Request → Agent Decisions → Data Lineage → Final Output

Usage:
    from quality.logger import QualityLogger
    
    logger = QualityLogger()
    
    # Request
    request_id = logger.log_request(
        asset="BTC",
        horizon="1d",
        mode="core_preferred",
        version_snapshot={...}
    )
    
    # Agent decisions
    logger.log_agent_run(
        request_id=request_id,
        agent_name="MarketAnalyst",
        agent_version="1.0.0",
        input_state={...},
        output_recommendation="buy",
        output_confidence=0.75,
        rationale="...",
        risk_flags=["high_vol"],
        latency_ms=1234,
        tokens_used=500
    )
    
    # Final output
    logger.log_final_output(
        request_id=request_id,
        synthesis={...},
        final_confidence=0.72,
        mode_used="core",
        execution_time_ms=5000
    )
"""
import os
import json
import uuid
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field, asdict
from pathlib import Path
import asyncio

from .client import QualityDB


@dataclass
class VersionSnapshot:
    """Snapshot of all versions at request time"""
    prompt_version: str = "unset"
    model_version: str = "unset"
    embed_version: str = "unset"
    index_version: str = "unset"
    code_version: str = "unset"
    repo_commit: str = "unset"
    
    def to_dict(self) -> Dict[str, str]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, d: Dict[str, str]) -> "VersionSnapshot":
        return cls(**d)
    
    def checksum(self) -> str:
        """Generate checksum for this snapshot"""
        data = json.dumps(self.to_dict(), sort_keys=True)
        return hashlib.sha256(data.encode()).hexdigest()[:8]


@dataclass
class AgentDecision:
    """Single agent decision record"""
    agent_name: str
    agent_version: str
    input_state: Dict[str, Any]
    rag_refs: List[str] = field(default_factory=list)
    output_recommendation: str = ""
    output_confidence: float = 0.0
    rationale: str = ""
    risk_flags: List[str] = field(default_factory=list)
    latency_ms: int = 0
    tokens_used: int = 0
    error: Optional[str] = None


@dataclass  
class DataLineage:
    """Data context for reproducibility"""
    source: str
    params: Dict[str, Any]
    fetched_at: str
    checksum: str = ""
    features_version: str = "unset"
    
    @classmethod
    def compute_checksum(cls, data: Dict[str, Any]) -> str:
        """Compute hash of data batch"""
        serialized = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode()).hexdigest()[:16]


class QualityLogger:
    """
    4-layer quality logger for asurdev Sentinel
    
    Layer 1: Request Event
    Layer 2: Agent Decision Logs  
    Layer 3: Data Lineage
    Layer 4: Final Output
    """
    
    def __init__(
        self,
        db_client: Optional[QualityDB] = None,
        log_dir: str = "/home/workspace/asurdevSentinel/data/logs"
    ):
        self.db = db_client or QualityDB()
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # JSONL files for raw logs (backup/quick access)
        self._request_log = self.log_dir / "requests.jsonl"
        self._agent_log = self.log_dir / "agent_runs.jsonl"
        self._output_log = self.log_dir / "outputs.jsonl"
    
    # ========================
    # Layer 1: Request Events
    # ========================
    
    def log_request(
        self,
        asset: str,
        horizon: str = "1d",
        mode: str = "core_preferred",
        user_id: str = "local",
        version_snapshot: Optional[Dict[str, str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Log a request event (Layer 1).
        
        Returns request_id for linking subsequent logs.
        """
        request_id = str(uuid.uuid4())
        snapshot = VersionSnapshot.from_dict(version_snapshot or {})
        
        request_record = {
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "asset": asset,
            "horizon": horizon,
            "mode": mode,
            "version_snapshot": snapshot.to_dict(),
            "snapshot_checksum": snapshot.checksum(),
            "metadata": metadata or {}
        }
        
        # Write to JSONL (raw backup)
        self._append_jsonl(self._request_log, request_record)
        
        # Write to PostgreSQL
        self.db.log_request(request_record)
        
        return request_id
    
    # ========================
    # Layer 2: Agent Decisions
    # ========================
    
    def log_agent_run(
        self,
        request_id: str,
        agent_name: str,
        agent_version: str,
        input_state: Dict[str, Any],
        output_recommendation: str,
        output_confidence: float,
        rationale: str = "",
        risk_flags: Optional[List[str]] = None,
        rag_refs: Optional[List[str]] = None,
        latency_ms: int = 0,
        tokens_used: int = 0,
        error: Optional[str] = None
    ) -> str:
        """
        Log an agent decision (Layer 2).
        
        Returns agent_run_id.
        """
        agent_run_id = str(uuid.uuid4())
        
        # Compute input state checksum for RAG/debugging
        input_checksum = DataLineage.compute_checksum(input_state)
        
        agent_record = {
            "agent_run_id": agent_run_id,
            "request_id": request_id,
            "agent_name": agent_name,
            "agent_version": agent_version,
            "input_state_checksum": input_checksum,
            "input_state": self._truncate_dict(input_state, max_len=2000),
            "rag_refs": rag_refs or [],
            "output_recommendation": output_recommendation,
            "output_confidence": output_confidence,
            "rationale": rationale[:1000] if rationale else "",  # Cap length
            "risk_flags": risk_flags or [],
            "latency_ms": latency_ms,
            "tokens_used": tokens_used,
            "error": error,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Write to JSONL
        self._append_jsonl(self._agent_log, agent_record)
        
        # Write to PostgreSQL
        self.db.log_agent_run(agent_record)
        
        return agent_run_id
    
    # ========================
    # Layer 3: Data Lineage
    # ========================
    
    def log_data_lineage(
        self,
        request_id: str,
        source: str,
        params: Dict[str, Any],
        data: Dict[str, Any],
        features_version: str = "unset"
    ) -> str:
        """
        Log data context for reproducibility (Layer 3).
        
        Returns lineage_id.
        """
        lineage_id = str(uuid.uuid4())
        fetched_at = datetime.utcnow().isoformat()
        checksum = DataLineage.compute_checksum(data)
        
        lineage_record = {
            "lineage_id": lineage_id,
            "request_id": request_id,
            "source": source,
            "params": params,
            "fetched_at": fetched_at,
            "checksum": checksum,
            "features_version": features_version,
            "data_sample": self._truncate_dict(data, max_len=500)  # Store sample, not full
        }
        
        # Only to PostgreSQL (too large for JSONL)
        self.db.log_data_lineage(lineage_record)
        
        return lineage_id
    
    # ========================
    # Layer 4: Final Output
    # ========================
    
    def log_final_output(
        self,
        request_id: str,
        synthesis: Dict[str, Any],
        final_confidence: float,
        mode_used: str,
        execution_time_ms: int,
        what_would_change_mind: Optional[List[str]] = None
    ) -> str:
        """
        Log final synthesis output (Layer 4).
        
        Returns output_id.
        """
        output_id = str(uuid.uuid4())
        
        output_record = {
            "output_id": output_id,
            "request_id": request_id,
            "synthesis": synthesis,
            "final_confidence": final_confidence,
            "mode_used": mode_used,
            "execution_time_ms": execution_time_ms,
            "what_would_change_mind": what_would_change_mind or [],
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Write to JSONL
        self._append_jsonl(self._output_log, output_record)
        
        # Write to PostgreSQL
        self.db.log_final_output(output_record)
        
        return output_id
    
    # ========================
    # Convenience Methods
    # ========================
    
    def log_full_request(
        self,
        asset: str,
        horizon: str,
        agent_decisions: List[AgentDecision],
        data_lineage: Dict[str, Any],
        synthesis: Dict[str, Any],
        final_confidence: float,
        mode: str = "core_preferred",
        version_snapshot: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Convenience: log a complete request with all 4 layers.
        
        Returns request_id.
        """
        # Layer 1: Request
        request_id = self.log_request(
            asset=asset,
            horizon=horizon,
            mode=mode,
            version_snapshot=version_snapshot
        )
        
        # Layer 2: Agent decisions
        for decision in agent_decisions:
            self.log_agent_run(
                request_id=request_id,
                agent_name=decision.agent_name,
                agent_version=decision.agent_version,
                input_state=decision.input_state,
                output_recommendation=decision.output_recommendation,
                output_confidence=decision.output_confidence,
                rationale=decision.rationale,
                risk_flags=decision.risk_flags,
                rag_refs=decision.rag_refs,
                latency_ms=decision.latency_ms,
                tokens_used=decision.tokens_used,
                error=decision.error
            )
        
        # Layer 3: Data lineage
        self.log_data_lineage(
            request_id=request_id,
            source=data_lineage.get("source", "unknown"),
            params=data_lineage.get("params", {}),
            data=data_lineage.get("data", {}),
            features_version=data_lineage.get("features_version", "unset")
        )
        
        # Layer 4: Final output
        self.log_final_output(
            request_id=request_id,
            synthesis=synthesis,
            final_confidence=final_confidence,
            mode_used=mode
        )
        
        return request_id
    
    # ========================
    # Helpers
    # ========================
    
    def _append_jsonl(self, path: Path, record: Dict[str, Any]) -> None:
        """Append record to JSONL file"""
        with open(path, "a") as f:
            f.write(json.dumps(record, default=str) + "\n")
    
    def _truncate_dict(self, d: Dict[str, Any], max_len: int = 1000) -> Dict[str, Any]:
        """Truncate dict values to prevent huge logs"""
        result = {}
        for k, v in d.items():
            if isinstance(v, str) and len(v) > max_len:
                result[k] = v[:max_len] + "...[truncated]"
            elif isinstance(v, dict):
                result[k] = self._truncate_dict(v, max_len)
            else:
                result[k] = v
        return result


# Singleton instance
_logger: Optional[QualityLogger] = None

def get_logger() -> QualityLogger:
    global _logger
    if _logger is None:
        _logger = QualityLogger()
    return _logger
