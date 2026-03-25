"""
asurdev Sentinel — FastAPI Backend
Provides REST API for React UI
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
import asyncio
import sys
import os
import re
import uuid
import json

# Add parent dir to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

app = FastAPI(title="asurdev Sentinel API", version="2.1.0")

# CORS — whitelist specific origins (FIX #1)
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "https://asurdev.zo.space",
    # Add your production domains here
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)

# Valid symbols whitelist (FIX #3)
VALID_SYMBOLS = frozenset({
    "BTC", "ETH", "SOL", "XRP", "ADA", "DOGE", "DOT", "AVAX", "LINK", "MATIC",
    "ATOM", "UNI", "LTC", "BCH", "XLM", "ALGO", "VET", "ICP", "FIL", "THETA",
    "TRX", "ETC", "XMR", "CRO", "CAKE", "AAVE", "MKR", "SNX", "COMP", "SUSHI",
    "APE", "SHIB", "SAND", "MANA", "AXS", "ENJ", "GALA", "IMX", "FTM", "NEAR",
    "APT", "SUI", "SEI", "TIA", "INJ", "JUP", "PYTH", "W", "BOME", "ORDI",
    "RUNE", "KAVA", "ANKR", "IOTA", "XTZ", "EOS", "NEO", "dash", "zec", "rvn",
    "KCS", "BSV", "DCR", "ZIL", "ENS", "LDO", "RPL", "GMX", "SNX", "CRV",
})

# Models (FIX #3)
class AnalyzeRequest(BaseModel):
    symbol: str = Field(
        ..., 
        min_length=2, 
        max_length=10,
        description="Trading symbol (e.g., BTC, ETH)"
    )
    action: str = Field(default="hold", pattern="^(buy|sell|hold)$")
    
    @property
    def clean_symbol(self) -> str:
        """Sanitized uppercase symbol"""
        return re.sub(r'[^A-Z0-9]', '', self.symbol.upper())


class ChartRequest(BaseModel):
    """Request model for astrological chart calculation."""
    date: str = Field(default="2026-03-22", description="Date in YYYY-MM-DD format")
    time: str = Field(default="12:00:00", description="Time in HH:MM:SS format (UTC)")
    lat: float = Field(default=55.7558, ge=-90, le=90, description="Latitude")
    lon: float = Field(default=37.6173, ge=-180, le=180, description="Longitude")
    ayanamsa: str = Field(default="lahiri", description="Ayanamsa (lahiri, raman, krishnamurti, fagan_bradley, surya_siddhanta, true_citra, tropical)")
    zodiac: str = Field(default="sidereal", description="Zodiac type (sidereal or tropical)")
    house_system: str = Field(default="W", description="House system (W=Whole Sign, P=Placidus, K=Koch, C=Campanus)")
    compute_houses: bool = Field(default=True, description="Calculate house cusps")
    compute_panchanga: bool = Field(default=True, description="Calculate Panchanga")
    compute_choghadiya: bool = Field(default=True, description="Calculate Choghadiya")
    compute_ashtakavarga: bool = Field(default=False, description="Calculate Ashtakavarga")


class FeedbackRequest(BaseModel):
    agent_id: str = Field(..., max_length=64)
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=1000)

# Global state
orchestrator = None
learning_engine = None

def get_orchestrator():
    global orchestrator
    if orchestrator is None:
        from agents.orchestrator import Orchestrator
        orchestrator = Orchestrator()
    return orchestrator

def get_learning_engine():
    global learning_engine
    if learning_engine is None:
        from feedback.learner import get_learning_engine
        from memory.vector_store import get_memory
        memory = get_memory()
        learning_engine = get_learning_engine(memory)
    return learning_engine

@app.get("/")
async def root():
    return {"message": "asurdev Sentinel API v2.1", "status": "running"}

@app.get("/api/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/api/analyze")
async def analyze(req: AnalyzeRequest):
    """Run full analysis for symbol"""
    try:
        orch = get_orchestrator()
        result = await orch.analyze(req.symbol, req.action)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail="An error occurred while processing your request.")

@app.get("/api/agents")
async def get_agents():
    """Get all agents status"""
    try:
        # from agents import get_all_agents
        agents = []
        # agents = []  # TODO: implement agent registry
        return [{"name": a.name, "status": "ready"} for a in agents]
    except Exception as e:
        raise HTTPException(status_code=500, detail="An error occurred while processing your request.")

@app.get("/api/performance")
async def get_performance():
    """Get agent performance metrics"""
    try:
        engine = get_learning_engine()
        return engine.get_agent_performance()
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/feedback")
async def submit_feedback(req: FeedbackRequest):
    """Submit user feedback"""
    try:
        engine = get_learning_engine()
        # Store in memory
        memory = engine.memory
        if memory and req.rating > 0:
            memory.add_feedback(
                analysis_id=req.agent_id,
                helpful=req.rating >= 3,
                rating=req.rating,
                notes=req.comment
            )
        return {"status": "success", "rating": req.rating}
    except Exception as e:
        raise HTTPException(status_code=500, detail="An error occurred while processing your request.")

@app.get("/api/astro")
async def get_astro():
    """Get current astrology data"""
    try:
        from datetime import datetime
        from agents.astrologer import get_moon_phase, get_nakshatra, get_choghadiya
        
        now = datetime.now()
        moon = get_moon_phase(now)
        nak = get_nakshatra(now)
        chg = get_choghadiya(now)
        
        return {
            "moon_phase": moon.get("phase", "Unknown"),
            "nakshatra": nak.get("name", "Unknown") if isinstance(nak, dict) else str(nak),
            "choghadiya": chg.get("name", "Unknown") if isinstance(chg, dict) else str(chg),
            "choghadiya_favorable": chg.get("favorable", True) if isinstance(chg, dict) else True,
            "timestamp": now.isoformat()
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/memory/summary")
async def get_memory_summary():
    """Get vector memory summary"""
    try:
        from memory.vector_store import get_memory
        memory = get_memory()
        return memory.get_summary()
    except Exception as e:
        return {"error": str(e)}


# ============================================================================
# ASTROLOGY CHART ENDPOINTS
# ============================================================================

def _format_choghadiya(choghadiya: dict) -> list:
    """Convert choghadiya dict format to list of entries for API response."""
    if not choghadiya or not isinstance(choghadiya, dict):
        return []
    
    day_parts = choghadiya.get("day_parts", [])
    night_parts = choghadiya.get("night_parts", [])
    
    result = []
    for ch in day_parts:
        result.append({
            "name": ch.get("type", "-"),
            "period": ch.get("period", "-"),
            "start": ch.get("start", ""),
            "end": ch.get("end", ""),
            "favorable": ch.get("auspicious", False),
            "quality": ch.get("quality", ""),
            "is_day": True,
        })
    for ch in night_parts:
        result.append({
            "name": ch.get("type", "-"),
            "period": ch.get("period", "-"),
            "start": ch.get("start", ""),
            "end": ch.get("end", ""),
            "favorable": ch.get("auspicious", False),
            "quality": ch.get("quality", ""),
            "is_day": False,
        })
    
    return result


def get_swiss_ephemeris():
    """Lazy load Swiss Ephemeris tool."""
    from swiss_ephemeris.swiss_ephemeris_tool import swiss_ephemeris
    return swiss_ephemeris


@app.post("/api/chart", response_model=dict)
async def compute_chart(req: ChartRequest):
    """
    Compute full astrological chart with Swiss Ephemeris.
    
    Calculates planet positions, houses, Panchanga, Choghadiya, and optionally Ashtakavarga.
    """
    try:
        swiss_ephemeris = get_swiss_ephemeris()
        
        result = swiss_ephemeris(
            date=req.date,
            time=req.time,
            lat=req.lat,
            lon=req.lon,
            ayanamsa=req.ayanamsa,
            zodiac=req.zodiac,
            house_system=req.house_system,
            compute_houses=req.compute_houses,
            compute_panchanga=req.compute_panchanga,
            compute_choghadiya=req.compute_choghadiya,
            compute_ashtakavarga=req.compute_ashtakavarga,
        )

        if "errors" in result and result["errors"]:
            raise HTTPException(status_code=400, detail=result["errors"])

        # Use positions_formatted (has degree, sign, nakshatra) for UI
        positions_out = result.get("positions_formatted", result.get("positions", {}))

        return {
            "status": "success",
            "input": {
                "date": req.date,
                "time": req.time,
                "lat": req.lat,
                "lon": req.lon,
                "ayanamsa": req.ayanamsa,
                "zodiac": req.zodiac,
                "house_system": req.house_system,
            },
            "positions": positions_out,
            "houses": result.get("houses", {}) if req.compute_houses else None,
            "panchanga": result.get("panchanga", {}) if req.compute_panchanga else None,
            "choghadiya": _format_choghadiya(result.get("choghadiya", {})) if req.compute_choghadiya else None,
            "ashtakavarga": result.get("ashtakavarga", {}) if req.compute_ashtakavarga else None,
            "calculation_time_ms": result.get("calculation_time", 0),
            "timestamp": datetime.now().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/chart/positions")
async def get_planet_positions(
    date: str = "2026-03-22",
    time: str = "12:00:00",
    lat: float = 55.7558,
    lon: float = 37.6173,
    ayanamsa: str = "lahiri",
):
    """
    Get current planet positions (lightweight endpoint).
    """
    try:
        swiss_ephemeris = get_swiss_ephemeris()
        result = swiss_ephemeris({
            "date": date,
            "time": time,
            "lat": lat,
            "lon": lon,
            "ayanamsa": ayanamsa,
            "zodiac": "sidereal",
            "house_system": "W",
            "compute_houses": False,
            "compute_panchanga": False,
            "compute_choghadiya": False,
        })
        positions_out = result.get("positions_formatted", result.get("positions", {}))
        return {"positions": positions_out, "timestamp": datetime.now().isoformat()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/chart/panchanga")
async def get_panchanga(
    date: str = "2026-03-22",
    time: str = "12:00:00",
    lat: float = 55.7558,
    lon: float = 37.6173,
):
    """
    Get Panchanga data (vara, tithi, nakshatra, yoga, karana).
    """
    try:
        swiss_ephemeris = get_swiss_ephemeris()
        result = swiss_ephemeris({
            "date": date,
            "time": time,
            "lat": lat,
            "lon": lon,
            "ayanamsa": "lahiri",
            "zodiac": "sidereal",
            "house_system": "W",
            "compute_houses": False,
            "compute_panchanga": True,
            "compute_choghadiya": False,
        })
        return {"panchanga": result.get("panchanga", {}), "timestamp": datetime.now().isoformat()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/chart/choghadiya")
async def get_choghadiya(
    date: str = "2026-03-22",
    time: str = "12:00:00",
    lat: float = 55.7558,
    lon: float = 37.6173,
):
    """
    Get Choghadiya Muhurta table for the day.
    """
    try:
        swiss_ephemeris = get_swiss_ephemeris()
        result = swiss_ephemeris({
            "date": date,
            "time": time,
            "lat": lat,
            "lon": lon,
            "ayanamsa": "lahiri",
            "zodiac": "sidereal",
            "house_system": "W",
            "compute_houses": False,
            "compute_panchanga": True,
            "compute_choghadiya": True,
        })
        
        sunrise = result.get("panchanga", {}).get("sunrise", None)
        sunset = result.get("panchanga", {}).get("sunset", None)
        
        return {
            "choghadiya": result.get("choghadiya", []),
            "sunrise": sunrise,
            "sunset": sunset,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/astro/current")
async def get_current_astro(
    lat: float = 55.7558,
    lon: float = 37.6173,
):
    """
    Get current astrological conditions (real-time).
    """
    try:
        swiss_ephemeris = get_swiss_ephemeris()
        now = datetime.now()
        
        result = swiss_ephemeris({
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S"),
            "lat": lat,
            "lon": lon,
            "ayanamsa": "lahiri",
            "zodiac": "sidereal",
            "house_system": "W",
            "compute_houses": False,
            "compute_panchanga": True,
            "compute_choghadiya": True,
        })

        positions = result.get("positions", {})
        panchanga = result.get("panchanga", {})
        choghadiya = result.get("choghadiya", [])

        return {
            "timestamp": now.isoformat(),
            "sun": positions.get("Sun", {}),
            "moon": positions.get("Moon", {}),
            "mercury": positions.get("Mercury", {}),
            "venus": positions.get("Venus", {}),
            "mars": positions.get("Mars", {}),
            "jupiter": positions.get("Jupiter", {}),
            "saturn": positions.get("Saturn", {}),
            "panchanga": panchanga,
            "choghadiya_today": choghadiya,
            "location": {"lat": lat, "lon": lon},
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


# ============================================================================
# SSE STREAMING ENDPOINTS (from P2)
# ============================================================================

from sse_starlette.sse import EventSourceResponse


class BoardAnalysisRequest(BaseModel):
    """Request for Board of Directors analysis."""
    query: str = Field(..., min_length=5, max_length=1000)
    include_astrology: bool = Field(default=True)
    include_risk_manager: bool = Field(default=True)
    mode: Literal["round_robin", "debate"] = Field(default="debate")
    stream: bool = Field(default=True, description="Enable SSE streaming")


class HealthResponse(BaseModel):
    """Health check response with LLM provider info."""
    status: str
    version: str
    llm_provider: str
    ollama_available: bool


def _check_ollama() -> bool:
    """Check if Ollama is available."""
    try:
        import httpx
        response = httpx.get("http://localhost:11434/api/tags", timeout=2.0)
        return response.status_code == 200
    except Exception:
        return False


async def board_event_generator(
    query: str,
    include_astrology: bool,
    include_risk_manager: bool,
    mode: str,
):
    """
    Generate SSE events for Board of Directors meeting.
    """
    import json
    session_id = str(uuid.uuid4())
    
    try:
        # Send session start
        yield {"event": "session_start", "data": json.dumps({
            "session_id": session_id,
            "query": query,
        })}
        
        # Import and run board
        from agents._impl.board import BoardOfDirectors
        
        board = BoardOfDirectors(
            provider="auto",
            mode=mode,
            include_astrology=include_astrology,
            include_risk_manager=include_risk_manager,
        )
        
        await board.initialize()
        
        try:
            # Conduct the meeting with streaming
            async for event in board.conduct_vote_streaming(query):
                yield {"event": event["type"], "data": json.dumps(event["data"])}
                
        finally:
            pass
                
        # Send completion
        yield {"event": "complete", "data": json.dumps({"session_id": session_id})}
        
    except Exception as e:
        yield {"event": "error", "data": json.dumps({"message": str(e)})}


@app.post("/api/board/stream")
async def board_analyze_stream(request: BoardAnalysisRequest):
    """
    Board of Directors analysis with SSE streaming.
    
    Real-time events:
    - agent_speaking: {"agent": "Market_Analyst", "content": "..."}
    - vote: {"agent": "Market_Analyst", "recommendation": "BUY", "confidence": 0.8}
    - verdict: {"recommendation": "BUY", "confidence": 0.75, ...}
    - complete: {"session_id": "..."}
    """
    import json
    
    return EventSourceResponse(
        board_event_generator(
            query=request.query,
            include_astrology=request.include_astrology,
            include_risk_manager=request.include_risk_manager,
            mode=request.mode,
        ),
        media_type="text/event-stream",
    )


@app.post("/api/board")
async def board_analyze_sync(request: BoardAnalysisRequest):
    """
    Synchronous Board of Directors analysis.
    
    Waits for complete board verdict before returning.
    """
    try:
        from agents._impl.board import BoardOfDirectors
        
        async with BoardOfDirectors(
            provider="auto",
            mode=request.mode,
            include_astrology=request.include_astrology,
            include_risk_manager=request.include_risk_manager,
        ) as board:
            verdict = await board.conduct_vote(request.query)
            
        return {
            "query": request.query,
            "timestamp": datetime.now().isoformat(),
            "verdict": verdict.to_dict(),
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/health/v2", response_model=HealthResponse)
async def health_with_llm():
    """Health check with LLM provider status."""
    ollama_status = _check_ollama()
    
    return HealthResponse(
        status="healthy",
        version="3.2.0",
        llm_provider="ollama" if ollama_status else "openai",
        ollama_available=ollama_status,
    )

# ============================================================================
# P2-compatible endpoints (/analyze and /analyze/stream)
# These are aliases for /api/board and /api/board/stream
# ============================================================================

@app.post("/analyze")
async def analyze_board_sync(request: BoardAnalysisRequest):
    """
    P2-compatible: Synchronous Board of Directors analysis.
    
    This is an alias for POST /api/board.
    Waits for complete board verdict before returning.
    """
    try:
        from agents._impl.board import BoardOfDirectors
        
        async with BoardOfDirectors(
            provider="auto",
            mode=request.mode,
            include_astrology=request.include_astrology,
            include_risk_manager=request.include_risk_manager,
        ) as board:
            verdict = await board.conduct_vote(request.query)
            
        return {
            "query": request.query,
            "timestamp": datetime.now().isoformat(),
            "verdict": verdict.to_dict(),
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze/stream")
async def analyze_board_stream(request: BoardAnalysisRequest):
    """
    P2-compatible: Board of Directors analysis with SSE streaming.
    
    This is an alias for POST /api/board/stream.
    
    Real-time events:
    - agent_speaking: {"agent": "Market_Analyst", "content": "..."}
    - vote: {"agent": "Market_Analyst", "recommendation": "BUY", "confidence": 0.8}
    - verdict: {"recommendation": "BUY", "confidence": 0.75, ...}
    - complete: {"session_id": "..."}
    """
    import json
    
    return EventSourceResponse(
        board_event_generator(
            query=request.query,
            include_astrology=request.include_astrology,
            include_risk_manager=request.include_risk_manager,
            mode=request.mode,
        ),
        media_type="text/event-stream",
    )
