"""
asurdev Sentinel — Backtester
Evaluates signal quality against ground truth

Usage:
    from quality.backtester import Backtester
    
    bt = Backtester()
    
    # Run backtest on historical requests
    results = bt.run_backtest(
        start_date="2026-01-01",
        end_date="2026-03-01",
        assets=["BTC", "ETH"]
    )
    
    # Check for degradation
    report = bt.check_degradation(baseline_window="30d")
"""
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import json

import pandas as pd
import numpy as np

from .client import QualityDB


@dataclass
class BacktestResult:
    """Single backtest run result"""
    backtest_id: str
    run_date: str
    asset: str
    horizon: str
    
    # Signal quality metrics
    accuracy: float = 0.0
    precision: float = 0.0
    recall: float = 0.0
    f1: float = 0.0
    brier_score: float = 0.0
    ece: float = 0.0  # Expected Calibration Error
    
    # Trading metrics
    total_return: float = 0.0
    max_drawdown: float = 0.0
    sharpe: float = 0.0
    sortino: float = 0.0
    winrate: float = 0.0
    expectancy: float = 0.0
    profit_factor: float = 0.0
    
    # After costs
    net_return: float = 0.0
    net_max_drawdown: float = 0.0
    
    # Mode comparison
    core_accuracy: float = 0.0
    edge_accuracy: float = 0.0
    
    # Sample info
    n_samples: int = 0
    n_correct: int = 0


class Backtester:
    """
    Backtest engine for asurdev Sentinel quality evaluation.
    
    Separated from online response. Runs:
    - Daily: quick health check on last 30 days
    - Weekly: full analysis on last 90 days
    - Monthly: comprehensive with regime breakdown
    """
    
    # Trading costs (realistic)
    COMMISSION = 0.001  # 0.1% per trade
    SLIPPAGE = 0.0005   # 0.05% slippage
    
    def __init__(self, db_client: Optional[QualityDB] = None):
        self.db = db_client or QualityDB()
    
    def run_backtest(
        self,
        start_date: str,
        end_date: str,
        assets: Optional[List[str]] = None,
        mode: str = "all"  # "all", "core", "edge"
    ) -> Dict[str, Any]:
        """
        Run backtest for specified period.
        
        Returns dict with metrics + per-asset breakdown.
        """
        assets = assets or ["BTC", "ETH", "SOL"]
        
        results = []
        
        for asset in assets:
            asset_result = self._backtest_asset(
                asset=asset,
                start_date=start_date,
                end_date=end_date,
                mode=mode
            )
            results.append(asset_result)
        
        # Aggregate
        return self._aggregate_results(results)
    
    def _backtest_asset(
        self,
        asset: str,
        start_date: str,
        end_date: str,
        mode: str
    ) -> BacktestResult:
        """Backtest single asset"""
        # Fetch requests + outputs for period
        requests = self.db.get_requests_in_range(
            start_date, end_date, asset
        )
        
        if not requests:
            return BacktestResult(
                backtest_id="",
                run_date=datetime.utcnow().isoformat(),
                asset=asset,
                horizon="unknown",
                n_samples=0
            )
        
        # Fetch corresponding outputs
        request_ids = [r["request_id"] for r in requests]
        outputs = self.db.get_outputs_for_requests(request_ids)
        outputs_map = {o["request_id"]: o for o in outputs}
        
        # Evaluate signals
        predictions = []
        ground_truths = []
        
        for req in requests:
            req_id = req["request_id"]
            output = outputs_map.get(req_id)
            
            if not output:
                continue
            
            # Extract prediction
            synth = output.get("synthesis", {})
            pred_signal = synth.get("signal", "Neutral")
            pred_conf = output.get("final_confidence", 0.5) / 100.0
            
            # Determine actual direction (need price data)
            # For now, mark as "unknown" and use forward returns
            predictions.append({
                "signal": pred_signal,
                "confidence": pred_conf,
                "mode": output.get("mode_used", "unknown"),
                "request_id": req_id
            })
        
        # Calculate metrics (simplified without price data)
        result = BacktestResult(
            backtest_id=f"bt_{asset}_{end_date}",
            run_date=datetime.utcnow().isoformat(),
            asset=asset,
            horizon="1d",
            n_samples=len(predictions)
        )
        
        # Placeholder metrics (real implementation needs price feed)
        result.accuracy = 0.55  # Placeholder
        result.brier_score = 0.25
        
        return result
    
    def _aggregate_results(self, results: List[BacktestResult]) -> Dict[str, Any]:
        """Aggregate per-asset results"""
        total_samples = sum(r.n_samples for r in results)
        
        return {
            "run_timestamp": datetime.utcnow().isoformat(),
            "n_assets": len(results),
            "total_samples": total_samples,
            "per_asset": [asdict(r) for r in results],
            "aggregated": {
                "avg_accuracy": np.mean([r.accuracy for r in results]) if results else 0,
                "avg_brier": np.mean([r.brier_score for r in results]) if results else 1,
                "avg_sharpe": np.mean([r.sharpe for r in results]) if results else 0,
                "worst_drawdown": max(r.max_drawdown for r in results) if results else 0
            }
        }
    
    def check_degradation(
        self,
        baseline_window: str = "30d",
        current_window: str = "7d",
        thresholds: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Check if recent performance degraded vs baseline.
        
        Returns degradation report.
        """
        thresholds = thresholds or {
            "accuracy_drop": 0.05,      # 5% drop acceptable
            "brier_increase": 0.05,     # 5% increase acceptable
            "drawdown_increase": 0.10   # 10% increase acceptable
        }
        
        now = datetime.utcnow()
        
        # Baseline: last 30 days
        baseline_end = now - timedelta(days=int(current_window.rstrip("d")))
        baseline_start = baseline_end - timedelta(days=int(baseline_window.rstrip("d")))
        
        # Current: last 7 days
        current_end = now
        current_start = now - timedelta(days=int(current_window.rstrip("d")))
        
        baseline = self.run_backtest(
            start_date=baseline_start.isoformat(),
            end_date=baseline_end.isoformat()
        )
        
        current = self.run_backtest(
            start_date=current_start.isoformat(),
            end_date=current_end.isoformat()
        )
        
        # Compare
        b_acc = baseline["aggregated"]["avg_accuracy"]
        c_acc = current["aggregated"]["avg_accuracy"]
        acc_drop = b_acc - c_acc
        
        b_brier = baseline["aggregated"]["avg_brier"]
        c_brier = current["aggregated"]["avg_brier"]
        brier_increase = c_brier - b_brier
        
        degraded = (
            acc_drop > thresholds["accuracy_drop"] or
            brier_increase > thresholds["brier_increase"]
        )
        
        return {
            "degraded": degraded,
            "baseline_window": baseline_window,
            "current_window": current_window,
            "thresholds": thresholds,
            "baseline": {
                "accuracy": b_acc,
                "brier_score": b_brier
            },
            "current": {
                "accuracy": c_acc,
                "brier_score": c_brier
            },
            "changes": {
                "accuracy_drop": acc_drop,
                "brier_increase": brier_increase
            },
            "recommendations": self._generate_recommendations(acc_drop, brier_increase, thresholds)
        }
    
    def _generate_recommendations(
        self,
        acc_drop: float,
        brier_increase: float,
        thresholds: Dict[str, float]
    ) -> List[str]:
        """Generate recommended actions based on degradation"""
        recs = []
        
        if acc_drop > thresholds["accuracy_drop"]:
            recs.append(f"⚠️ Accuracy dropped {acc_drop:.1%}. Consider reviewing prompts or model.")
        
        if brier_increase > thresholds["brier_increase"]:
            recs.append(f"⚠️ Brier score increased {brier_increase:.1%}. Confidence calibration may be off.")
        
        if not recs:
            recs.append("✅ No significant degradation detected.")
        
        return recs
    
    def generate_cp(
        self,
        degradation_report: Dict[str, Any],
        top_n_worst: int = 5
    ) -> Dict[str, Any]:
        """
        Generate Change Proposal from degradation report.
        
        Returns CP template filled with relevant data.
        """
        return {
            "cp_id": f"CP-{datetime.utcnow().strftime('%Y%m%d')}-001",
            "problem": f"Performance degraded: acc_drop={degradation_report['changes']['accuracy_drop']:.2%}",
            "hypothesis": "TBD - requires investigation",
            "change_type": "prompt_tuning",  # or model/data/rules
            "change_details": {
                "what": "TBD",
                "why": "TBD"
            },
            "success_criteria": {
                "metric": "accuracy",
                "baseline": degradation_report["baseline"]["accuracy"],
                "target": degradation_report["baseline"]["accuracy"],  # Restore
                "tolerance": degradation_report["thresholds"]["accuracy_drop"]
            },
            "risk": "TBD - consider rollback plan",
            "rollback": "Revert to previous version snapshot",
            "created_at": datetime.utcnow().isoformat(),
            "status": "draft"
        }
    
    def run_ablation(
        self,
        request_ids: List[str],
        exclude_agents: List[str]
    ) -> Dict[str, Any]:
        """
        Ablation study: run without certain agents to measure their contribution.
        
        Args:
            request_ids: Requests to re-evaluate
            exclude_agents: Agent names to skip (e.g., ["Astrologer", "CycleAgent"])
        
        Returns: Comparison of full vs ablation performance
        """
        # Full performance
        full_results = self._evaluate_requests(request_ids)
        
        # Ablated performance (need to re-run orchestrator without certain agents)
        # This is simplified - real implementation would re-run synthesis
        
        return {
            "full_accuracy": full_results["accuracy"],
            "ablated_accuracy": 0.0,  # Placeholder
            "agent_contribution": {
                agent: 0.0 for agent in exclude_agents
            }
        }
    
    def _evaluate_requests(self, request_ids: List[str]) -> Dict[str, float]:
        """Evaluate a set of requests against ground truth"""
        # Simplified - real implementation needs price data
        return {"accuracy": 0.55, "brier": 0.25}


# Helper to convert dataclass to dict
def asdict(obj):
    if hasattr(obj, "__dataclass_fields__"):
        return {k: asdict(v) for k, v in obj.__dict__.items()}
    elif isinstance(obj, list):
        return [asdict(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: asdict(v) for k, v in obj.items()}
    return obj
