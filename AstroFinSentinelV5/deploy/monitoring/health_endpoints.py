"""Health check and metrics endpoints for monitoring."""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
import time
import psutil
import os

app = FastAPI(title="AstroFin Sentinel - Health & Metrics")

# System metrics
process = psutil.Process(os.getpid())

class HealthResponse(BaseModel):
    status: str
    timestamp: float
    uptime_seconds: float
    memory_mb: float
    cpu_percent: float
    version: str = "5.0.0"

class KARLMetrics(BaseModel):
    # OAP KPIs
    oos_fail_rate: float
    entropy_avg: float
    grounding_strength: float
    current_ttc_depth: int
    
    # Audit
    total_decisions: int
    avg_confidence: float
    action_distribution: Dict[str, int]
    
    # Reward Calibration
    calibration_error: float
    slope: float
    intercept: float
    
    # Drift
    drift_status: str
    confidence_drift: float
    uncertainty_drift: float
    
    # Trading
    win_rate: float
    sharpe_ratio: float
    max_drawdown: float
    total_trades: int

_start_time = time.time()

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Kubernetes-compatible health check."""
    return HealthResponse(
        status="healthy",
        timestamp=time.time(),
        uptime_seconds=time.time() - _start_time,
        memory_mb=process.memory_info().rss / 1024 / 1024,
        cpu_percent=process.cpu_percent(interval=0.1),
    )

@app.get("/health/ready")
async def readiness_check():
    """Readiness probe - checks DB and cache connectivity."""
    # TODO: Add actual DB/Redis checks
    return {"status": "ready", "timestamp": time.time()}

@app.get("/metrics/karl", response_model=KARLMetrics)
async def karl_metrics():
    """Expose KARL AMRE metrics for Prometheus."""
    try:
        from agents.karl_synthesis import get_karl_agent
        
        agent = get_karl_agent()
        status = agent.get_status()
        diag = status.get("karl_diagnostics", {})
        
        oap = diag.get("oap_kpi", {})
        audit = diag.get("audit_summary", {})
        calibr = diag.get("calibration", {})
        drift = diag.get("drift_status", {})
        
        return KARLMetrics(
            oos_fail_rate=oap.get("oos_fail_rate", 0.0),
            entropy_avg=oap.get("entropy_avg", 0.0),
            grounding_strength=oap.get("grounding_strength", 0.0),
            current_ttc_depth=oap.get("current_ttc_depth", 0),
            total_decisions=audit.get("total", 0),
            avg_confidence=audit.get("avg_confidence_final", 0.0),
            action_distribution=audit.get("action_distribution", {}),
            calibration_error=calibr.get("calibration_error", 0.0),
            slope=calibr.get("slope", 0.0),
            intercept=calibr.get("intercept", 0.0),
            drift_status=drift.get("status", "unknown"),
            confidence_drift=drift.get("confidence_drift", 0.0),
            uncertainty_drift=drift.get("uncertainty_drift", 0.0),
            win_rate=diag.get("win_rate", 0.0),
            sharpe_ratio=diag.get("sharpe_ratio", 0.0),
            max_drawdown=diag.get("max_drawdown", 0.0),
            total_trades=diag.get("total_trades", 0),
        )
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))

@app.get("/metrics/system")
async def system_metrics():
    """System-level metrics."""
    return {
        "memory_percent": process.memory_percent(),
        "memory_mb": process.memory_info().rss / 1024 / 1024,
        "cpu_percent": process.cpu_percent(interval=0.1),
        "num_threads": process.num_threads(),
        "open_files": len(process.open_files()),
        "connections": len(process.connections()),
    }

@app.get("/")
async def root():
    return {
        "service": "AstroFin Sentinel V5",
        "version": "5.0.0",
        "status": "running",
        "docs": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
