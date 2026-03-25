"""
asurdev Sentinel — Change Proposal Manager
Tracks and manages system improvements

Usage:
    from quality.cp_manager import CPManager
    
    cpm = CPManager()
    
    # Create CP
    cp = cpm.create_cp(
        problem="Accuracy dropped 8%",
        hypothesis="Astro prompts too aggressive",
        change_type="prompt_tuning",
        success_criteria={...}
    )
    
    # Approve and apply
    cpm.approve_cp(cp["cp_id"])
    
    # Monitor metrics after change
    cpm.check_cp_success(cp["cp_id"])
"""
import os
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path

from .client import QualityDB


class CPStatus(Enum):
    DRAFT = "draft"
    APPROVED = "approved"
    APPLIED = "applied"
    VERIFIED = "verified"
    REJECTED = "rejected"
    ROLLED_BACK = "rolled_back"


class ChangeType(Enum):
    PROMPT_TUNING = "prompt_tuning"
    MODEL_CHANGE = "model_change"
    RULES = "rules"
    FEATURES = "features"
    RAG = "rag"
    LORA = "lora"
    CODE = "code"


@dataclass
class ChangeProposal:
    """Change Proposal record"""
    cp_id: str
    problem: str
    hypothesis: str
    change_type: str
    change_details: Dict[str, Any]
    success_criteria: Dict[str, Any]
    risk: str
    rollback: str
    status: str
    created_at: str
    approved_at: Optional[str] = None
    applied_at: Optional[str] = None
    verified_at: Optional[str] = None
    metrics_before: Optional[Dict[str, float]] = None
    metrics_after: Optional[Dict[str, float]] = None
    version_snapshot_before: Optional[Dict[str, str]] = None
    version_snapshot_after: Optional[Dict[str, str]] = None


class CPManager:
    """
    Change Proposal lifecycle manager.
    
    Ensures all changes are tracked, tested, and reversible.
    """
    
    def __init__(
        self,
        db_client: Optional[QualityDB] = None,
        cp_dir: str = "/home/workspace/asurdevSentinel/quality/cps"
    ):
        self.db = db_client or QualityDB()
        self.cp_dir = Path(cp_dir)
        self.cp_dir.mkdir(parents=True, exist_ok=True)
        
        # JSONL for all CPs
        self._cp_log = self.cp_dir / "change_proposals.jsonl"
    
    def create_cp(
        self,
        problem: str,
        hypothesis: str,
        change_type: str,
        change_details: Dict[str, Any],
        success_criteria: Dict[str, Any],
        risk: str = "medium",
        rollback: str = "revert to previous version",
        metrics_before: Optional[Dict[str, float]] = None,
        version_snapshot: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Create a new Change Proposal.
        
        Returns CP dict.
        """
        # Generate ID
        date_str = datetime.utcnow().strftime("%Y%m%d")
        existing = self._get_cp_count_today()
        cp_id = f"CP-{date_str}-{existing + 1:03d}"
        
        cp = {
            "cp_id": cp_id,
            "problem": problem,
            "hypothesis": hypothesis,
            "change_type": change_type,
            "change_details": change_details,
            "success_criteria": success_criteria,
            "risk": risk,
            "rollback": rollback,
            "status": CPStatus.DRAFT.value,
            "created_at": datetime.utcnow().isoformat(),
            "approved_at": None,
            "applied_at": None,
            "verified_at": None,
            "metrics_before": metrics_before,
            "metrics_after": None,
            "version_snapshot_before": version_snapshot,
            "version_snapshot_after": None
        }
        
        # Save to JSONL
        self._append_cp(cp)
        
        # Save to PostgreSQL
        self.db.log_change_proposal(cp)
        
        return cp
    
    def approve_cp(self, cp_id: str) -> Dict[str, Any]:
        """Approve a CP for application"""
        cp = self._load_cp(cp_id)
        
        if not cp:
            raise ValueError(f"CP {cp_id} not found")
        
        if cp["status"] != CPStatus.DRAFT.value:
            raise ValueError(f"CP {cp_id} is {cp['status']}, cannot approve")
        
        cp["status"] = CPStatus.APPROVED.value
        cp["approved_at"] = datetime.utcnow().isoformat()
        
        self._update_cp(cp)
        
        return cp
    
    def apply_cp(
        self,
        cp_id: str,
        new_version_snapshot: Dict[str, str],
        actor: str = "system"
    ) -> Dict[str, Any]:
        """
        Apply an approved CP.
        
        This is where the actual change happens (prompt update, model swap, etc.)
        """
        cp = self._load_cp(cp_id)
        
        if not cp:
            raise ValueError(f"CP {cp_id} not found")
        
        if cp["status"] not in [CPStatus.APPROVED.value, CPStatus.APPLIED.value]:
            raise ValueError(f"CP {cp_id} is {cp['status']}, cannot apply")
        
        # Record before snapshot
        if not cp.get("version_snapshot_before"):
            cp["version_snapshot_before"] = self._get_current_versions()
        
        cp["status"] = CPStatus.APPLIED.value
        cp["applied_at"] = datetime.utcnow().isoformat()
        cp["version_snapshot_after"] = new_version_snapshot
        
        # Increment version
        new_version = self._bump_version(cp["change_type"], new_version_snapshot)
        cp["version_snapshot_after"] = new_version
        
        self._update_cp(cp)
        
        return cp
    
    def verify_cp(
        self,
        cp_id: str,
        metrics_after: Dict[str, float],
        success_criteria: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Verify CP success based on metrics.
        
        Compares metrics_after against success_criteria.
        """
        cp = self._load_cp(cp_id)
        
        if not cp:
            raise ValueError(f"CP {cp_id} not found")
        
        if cp["status"] != CPStatus.APPLIED.value:
            raise ValueError(f"CP {cp_id} is {cp['status']}, cannot verify")
        
        # Evaluate success
        success = True
        details = {}
        
        if success_criteria:
            criteria = success_criteria
        else:
            criteria = cp.get("success_criteria", {})
        
        for metric, target in criteria.items():
            if metric in metrics_after:
                actual = metrics_after[metric]
                tolerance = criteria.get(f"{metric}_tolerance", 0.05)
                
                if metric.startswith("drop") or metric == "drawdown_increase":
                    # Lower is better
                    improved = actual <= target + tolerance
                else:
                    # Higher is better
                    improved = actual >= target - tolerance
                
                details[metric] = {
                    "target": target,
                    "actual": actual,
                    "tolerance": tolerance,
                    "passed": improved
                }
                
                if not improved:
                    success = False
        
        cp["status"] = CPStatus.VERIFIED.value if success else CPStatus.REJECTED.value
        cp["verified_at"] = datetime.utcnow().isoformat()
        cp["metrics_after"] = metrics_after
        cp["verification_details"] = details
        
        self._update_cp(cp)
        
        return {
            "cp": cp,
            "success": success,
            "details": details
        }
    
    def rollback_cp(self, cp_id: str) -> Dict[str, Any]:
        """
        Rollback a CP to previous state.
        """
        cp = self._load_cp(cp_id)
        
        if not cp:
            raise ValueError(f"CP {cp_id} not found")
        
        if not cp.get("version_snapshot_before"):
            raise ValueError(f"CP {cp_id} has no version to rollback to")
        
        cp["status"] = CPStatus.ROLLED_BACK.value
        cp["rollback_at"] = datetime.utcnow().isoformat()
        
        # Restore previous version
        self._restore_version(cp["version_snapshot_before"])
        
        self._update_cp(cp)
        
        return cp
    
    def get_cp_history(
        self,
        status: Optional[str] = None,
        change_type: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get CP history with filters"""
        cps = self._load_all_cps()
        
        if status:
            cps = [c for c in cps if c.get("status") == status]
        
        if change_type:
            cps = [c for c in cps if c.get("change_type") == change_type]
        
        return cps[-limit:]
    
    # ========================
    # Private Helpers
    # ========================
    
    def _append_cp(self, cp: Dict[str, Any]) -> None:
        """Append CP to JSONL"""
        with open(self._cp_log, "a") as f:
            f.write(json.dumps(cp, default=str) + "\n")
    
    def _update_cp(self, cp: Dict[str, Any]) -> None:
        """Update CP in JSONL (rewrite file)"""
        cps = self._load_all_cps()
        
        for i, existing in enumerate(cps):
            if existing["cp_id"] == cp["cp_id"]:
                cps[i] = cp
                break
        else:
            cps.append(cp)
        
        # Rewrite file
        with open(self._cp_log, "w") as f:
            for c in cps:
                f.write(json.dumps(c, default=str) + "\n")
    
    def _load_cp(self, cp_id: str) -> Optional[Dict[str, Any]]:
        """Load single CP by ID"""
        cps = self._load_all_cps()
        for cp in cps:
            if cp["cp_id"] == cp_id:
                return cp
        return None
    
    def _load_all_cps(self) -> List[Dict[str, Any]]:
        """Load all CPs from JSONL"""
        if not self._cp_log.exists():
            return []
        
        cps = []
        with open(self._cp_log) as f:
            for line in f:
                if line.strip():
                    cps.append(json.loads(line))
        return cps
    
    def _get_cp_count_today(self) -> int:
        """Count CPs created today"""
        today = datetime.utcnow().strftime("%Y%m%d")
        cps = self._load_all_cps()
        return sum(1 for c in cps if c["cp_id"].startswith(f"CP-{today}"))
    
    def _get_current_versions(self) -> Dict[str, str]:
        """Get current version snapshot"""
        # This would read from the versions table
        return {
            "prompt_version": "1.0.0",
            "model_version": "qwen2.5-coder:32b",
            "embed_version": "unset",
            "index_version": "unset"
        }
    
    def _bump_version(self, change_type: str, snapshot: Dict[str, str]) -> Dict[str, str]:
        """Bump version based on change type"""
        result = snapshot.copy()
        
        if change_type == ChangeType.PROMPT_TUNING.value:
            old = snapshot.get("prompt_version", "1.0.0")
            parts = old.split(".")
            parts[-1] = str(int(parts[-1]) + 1)
            result["prompt_version"] = ".".join(parts)
        
        elif change_type == ChangeType.MODEL_CHANGE.value:
            result["model_version"] = "new_model"
        
        # Log new version
        self.db.log_version(
            component=change_type,
            version=result.get(f"{change_type}_version", "1.0.0"),
            changes=f"Applied via CP"
        )
        
        return result
    
    def _restore_version(self, version_snapshot: Dict[str, str]) -> None:
        """Restore previous version"""
        # This would restore files/prompts/models
        pass
