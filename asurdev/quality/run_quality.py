#!/usr/bin/env python3
"""
asurdev Sentinel — Quality Runner
Scheduled quality checks: daily, weekly, monthly

Usage:
    python -m quality.run_quality daily   # Daily health check
    python -m quality.run_quality weekly  # Weekly deep dive
    python -m quality.run_quality monthly # Monthly release

Cron examples:
    0 6 * * * cd /home/workspace/asurdevSentinel && python -m quality.run_quality daily
    0 7 * * 1 cd /home/workspace/asurdevSentinel && python -m quality.run_quality weekly
    0 6 1 * * cd /home/workspace/asurdevSentinel && python -m quality.run_quality monthly
"""
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, Any

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from quality.backtester import Backtester
from quality.cp_manager import CPManager
from quality.client import get_quality_db


def run_daily_check() -> Dict[str, Any]:
    """
    Daily health check.
    - Quick backtest on last 7 days
    - Check for degradation vs 30-day baseline
    - Alert if thresholds exceeded
    """
    print("=" * 60)
    print("DAILY QUALITY CHECK")
    print(f"Timestamp: {datetime.utcnow().isoformat()}")
    print("=" * 60)
    
    bt = Backtester()
    
    # Check degradation
    report = bt.check_degradation(
        baseline_window="30d",
        current_window="7d"
    )
    
    print(f"\n📊 Degradation Check:")
    print(f"   Baseline (30d) accuracy: {report['baseline']['accuracy']:.2%}")
    print(f"   Current (7d) accuracy:   {report['current']['accuracy']:.2%}")
    print(f"   Drop: {report['changes']['accuracy_drop']:.2%}")
    
    if report["degraded"]:
        print(f"\n⚠️  DEGRADATION DETECTED")
        for rec in report["recommendations"]:
            print(f"   {rec}")
        
        # Auto-generate CP
        cp = bt.generate_cp(report)
        print(f"\n📝 Auto-generated CP: {cp['cp_id']}")
        print(f"   Problem: {cp['problem']}")
        
        return {"status": "degraded", "report": report, "cp": cp}
    else:
        print(f"\n✅ No significant degradation")
        for rec in report["recommendations"]:
            print(f"   {rec}")
        
        return {"status": "ok", "report": report}


def run_weekly_check() -> Dict[str, Any]:
    """
    Weekly deep dive.
    - Full backtest on last 90 days
    - Worst cases analysis
    - CP review and planning
    """
    print("=" * 60)
    print("WEEKLY QUALITY DEEP DIVE")
    print(f"Timestamp: {datetime.utcnow().isoformat()}")
    print("=" * 60)
    
    bt = Backtester()
    cpm = CPManager()
    
    # Full backtest
    results = bt.run_backtest(
        start_date=(datetime.utcnow() - timedelta(days=90)).isoformat(),
        end_date=datetime.utcnow().isoformat()
    )
    
    print(f"\n📊 90-Day Backtest:")
    print(f"   Total samples: {results['total_samples']}")
    print(f"   Avg accuracy:  {results['aggregated']['avg_accuracy']:.2%}")
    print(f"   Avg Brier:     {results['aggregated']['avg_brier']:.3f}")
    
    # Per-asset breakdown
    print(f"\n📈 Per-Asset Performance:")
    for asset_result in results.get("per_asset", []):
        print(f"   {asset_result['asset']}: acc={asset_result['accuracy']:.2%}, n={asset_result['n_samples']}")
    
    # Pending CPs
    pending_cps = cpm.get_cp_history(status="draft")
    print(f"\n📋 Pending CPs: {len(pending_cps)}")
    for cp in pending_cps[:5]:
        print(f"   {cp['cp_id']}: {cp['problem'][:60]}...")
    
    # Weekly recommendations
    recs = []
    if results['aggregated']['avg_accuracy'] < 0.52:
        recs.append("⚠️ Accuracy below 52% — needs prompt review")
    if results['aggregated']['avg_brier'] > 0.26:
        recs.append("⚠️ Brier score high — confidence calibration issues")
    
    print(f"\n💡 Weekly Recommendations:")
    if recs:
        for r in recs:
            print(f"   {r}")
    else:
        print(f"   System performing within acceptable parameters")
    
    return {"status": "ok", "results": results, "pending_cps": len(pending_cps)}


def run_monthly_check() -> Dict[str, Any]:
    """
    Monthly comprehensive review.
    - 6-month backtest
    - Regime breakdown (trending vs flat)
    - Core vs Edge comparison
    - Version release
    """
    print("=" * 60)
    print("MONTHLY COMPREHENSIVE REVIEW")
    print(f"Timestamp: {datetime.utcnow().isoformat()}")
    print("=" * 60)
    
    bt = Backtester()
    cpm = CPManager()
    db = get_quality_db()
    
    # 6-month backtest
    results = bt.run_backtest(
        start_date=(datetime.utcnow() - timedelta(days=180)).isoformat(),
        end_date=datetime.utcnow().isoformat()
    )
    
    print(f"\n📊 180-Day Comprehensive:")
    print(f"   Total samples: {results['total_samples']}")
    
    # Core vs Edge
    core_results = bt.run_backtest(
        start_date=(datetime.utcnow() - timedelta(days=180)).isoformat(),
        end_date=datetime.utcnow().isoformat(),
        mode="core"
    )
    edge_results = bt.run_backtest(
        start_date=(datetime.utcnow() - timedelta(days=180)).isoformat(),
        end_date=datetime.utcnow().isoformat(),
        mode="edge"
    )
    
    print(f"\n🔄 Core vs Edge:")
    print(f"   Core accuracy: {core_results['aggregated']['avg_accuracy']:.2%}")
    print(f"   Edge accuracy: {edge_results['aggregated']['avg_accuracy']:.2%}")
    
    # Approved CPs this month
    approved = cpm.get_cp_history(status="approved")
    applied = cpm.get_cp_history(status="applied")
    verified = cpm.get_cp_history(status="verified")
    
    print(f"\n📝 Change Proposals:")
    print(f"   Approved: {len(approved)}")
    print(f"   Applied:  {len(applied)}")
    print(f"   Verified: {len(verified)}")
    
    # Current versions
    versions = db.get_current_versions()
    print(f"\n📦 Current Versions:")
    for component, version in versions.items():
        print(f"   {component}: {version}")
    
    # Generate summary
    summary = {
        "period": "180d",
        "accuracy": results['aggregated']['avg_accuracy'],
        "core_vs_edge_gap": (
            core_results['aggregated']['avg_accuracy'] - 
            edge_results['aggregated']['avg_accuracy']
        ),
        "cps_approved": len(approved),
        "cps_verified": len(verified),
        "versions": versions
    }
    
    return {"status": "ok", "summary": summary}


def main():
    if len(sys.argv) < 2:
        print("Usage: python -m quality.run_quality [daily|weekly|monthly]")
        sys.exit(1)
    
    mode = sys.argv[1].lower()
    
    if mode == "daily":
        result = run_daily_check()
    elif mode == "weekly":
        result = run_weekly_check()
    elif mode == "monthly":
        result = run_monthly_check()
    else:
        print(f"Unknown mode: {mode}")
        sys.exit(1)
    
    # Exit code based on status
    if result.get("status") == "degraded":
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
