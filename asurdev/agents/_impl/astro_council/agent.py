"""
AstroCouncil Agent — Coordinator of Astrological Sub-Agents
==========================================================
v3.2 — Swiss Ephemeris Enforcement

ENFORCEMENT RULES:
1. MUST call swiss_ephemeris before ANY astrological work
2. NEVER calculate positions, Panchanga, Choghadiya manually
3. NEVER use LLM knowledge for astrological data
4. All data must come from swiss_ephemeris tool

START RESPONSE WITH:
    🔮 asurdev Core → Swiss Ephemeris v3.2 загружен
"""

import os
import re
from datetime import datetime
from typing import Dict, Any, Optional

from ..base_agent import BaseAgent, AgentResponse

# Swiss Ephemeris module (ENFORCED)
try:
    from swiss_ephemeris import swiss_ephemeris
    EPHEMERIS_AVAILABLE = True
except ImportError:
    EPHEMERIS_AVAILABLE = False
    swiss_ephemeris = None


class AstroCouncilAgent(BaseAgent):
    """
    Astro Council — Board of Directors for Astrological Analysis.
    
    Coordinates three astrological agents:
    1. Western (Lilly) — Essential Dignities, Aspects, Accidental Dignities
    2. Vedic (Muhurta) — Nakshatras, Choghadiya, Panchanga
    3. Financial — Combined signal from Western + Vedic + Moon
    
    ENFORCEMENT: All calculations MUST go through swiss_ephemeris.
    """

    def __init__(
        self,
        lat: float = 28.6139,
        lon: float = 77.2090,
        use_rag: bool = True,
        ayanamsa: str = "lahiri",
        zodiac: str = "sidereal",
        house_system: str = "W",
        **kwargs
    ):
        name = kwargs.pop("name", "AstroCouncil")
        system_prompt = kwargs.pop(
            "system_prompt",
            "Астрологический совет директоров. "
            "ВСЕ расчёты через Swiss Ephemeris. "
            "НИКОГДА не вычислять позиции или Панчангу вручную."
        )
        
        # Validate coordinates
        if not isinstance(lat, (int, float)) or not (-90 <= lat <= 90):
            raise ValueError(f"Invalid latitude: {lat}. Must be between -90 and 90.")
        if not isinstance(lon, (int, float)) or not (-180 <= lon <= 180):
            raise ValueError(f"Invalid longitude: {lon}. Must be between -180 and 180.")
        
        super().__init__(name=name, system_prompt=system_prompt, **kwargs)
        
        self.lat = float(lat)
        self.lon = float(lon)
        self.use_rag = use_rag
        self.ayanamsa = ayanamsa
        self.zodiac = zodiac
        self.house_system = house_system
        
        # Sub-agents
        self._western = None
        self._vedic = None
        self._financial = None
        self._muhurta = None

    @property
    def western(self):
        if self._western is None:
            from .western import WesternAstrologer
            self._western = WesternAstrologer()
        return self._western

    @property
    def vedic(self):
        if self._vedic is None:
            from .vedic import VedicAstrologerAgent
            self._vedic = VedicAstrologerAgent()
        return self._vedic

    @property
    def financial(self):
        if self._financial is None:
            from .financial import FinancialAstrologer
            self._financial = FinancialAstrologer()
        return self._financial

    @property
    def muhurta(self):
        """MuhurtaSpecialist for finding auspicious timing."""
        if self._muhurta is None:
            from ..muhurta import MuhurtaSpecialist
            self._muhurta = MuhurtaSpecialist(lat=self.lat, lon=self.lon)
        return self._muhurta

    async def analyze(self, context: Dict[str, Any]) -> AgentResponse:
        """
        Conduct astrological analysis.
        
        ENFORCEMENT: First call swiss_ephemeris, THEN use the data.
        
        Context may contain:
        - datetime: specific date/time (ISO format)
        - symbol: trading symbol
        - positions: pre-calculated positions (if already computed)
        - action: for muhurta requests (брак, путешествие, бизнес, ритуал)
        """
        # Check if this is a muhurta/timing request
        if self._is_muhurta_request(context):
            return await self._handle_muhurta_request(context)
        
        # Get datetime
        dt = context.get("datetime")
        if dt is None:
            dt = datetime.now()
        elif isinstance(dt, str):
            dt = datetime.fromisoformat(dt.replace("Z", "+00:00"))
        
        # Format for Swiss Ephemeris
        date_str = dt.strftime("%Y-%m-%d")
        time_str = dt.strftime("%H:%M:%S")
        
        # ENFORCEMENT: Call Swiss Ephemeris FIRST
        eph = self._call_ephemeris(date_str, time_str)
        
        # Get positions and houses from ephemeris
        positions = eph.get("positions", {})
        houses = eph.get("houses", {})
        panchanga = eph.get("panchanga", {})
        choghadiya = eph.get("current_choghadiya", {})
        ashtak = eph.get("ashtakavarga_trading", {})
        
        # Get RAG context if enabled
        rag_context = None
        if self.use_rag:
            symbol = context.get("symbol", "BTC")
            rag_context = self._get_rag_context(f"{symbol} astrology financial market")
        
        # Run FinancialAstrologer with ephemeris data
        result = self.financial.analyze_with_ephemeris(
            dt=dt,
            eph=eph,
            rag_context=rag_context
        )
        
        # Run Western House Analysis (Mankasi System)
        western_houses = None
        try:
            western_houses = self.western.interpret_houses(eph)
        except Exception as e:
            western_houses = {"error": str(e), "mankasi_enabled": False}
        
        # Build response
        return AgentResponse(
            agent_name="AstroCouncil",
            signal=result["signal"],
            confidence=result["confidence"],
            summary=self._summarize(result, panchanga, choghadiya),
            details={
                **result,
                "ephemeris": {
                    "date": date_str,
                    "time": time_str,
                    "lat": self.lat,
                    "lon": self.lon,
                    "ayanamsa": self.ayanamsa,
                    "positions": positions,
                    "houses": houses,
                    "panchanga": panchanga,
                    "current_choghadiya": choghadiya,
                    "ashtakavarga": ashtak,
                },
                "western_houses": western_houses,
            }
        )
    
    @staticmethod
    def _is_muhurta_request(context: Dict[str, Any]) -> bool:
        """Detect if context is a muhurta/timing request."""
        action = context.get("action", "")
        query = context.get("query", "")
        intent = context.get("intent", "")
        
        muhurta_keywords = [
            "благоприятн", "мухурт", "когда лучше", "когда合适",
            "время для", "планиру", "начина", "свадьб", "брак",
            "путешеств", "поездк", "ритуал", "обряд",
            "когда лучше всего", "какое время", "выбор времени",
            "muhurta", "auspicious", "timing", "when to"
        ]
        
        combined = f"{action} {query} {intent}".lower()
        return any(kw in combined for kw in muhurta_keywords)
    
    async def _handle_muhurta_request(self, context: Dict[str, Any]) -> AgentResponse:
        """Handle muhurta/timing analysis requests."""
        action = context.get("action", context.get("query", ""))
        
        # Extract action type if not explicit
        if not action or action == "analysis":
            query = context.get("query", "").lower()
            if any(w in query for w in ["свадьб", "брак", "замуж", "женить"]):
                action = "брак"
            elif any(w in query for w in ["путешеств", "поездк", "travel"]):
                action = "путешествие"
            elif any(w in query for w in ["бизнес", "начало", "business"]):
                action = "бизнес"
            elif any(w in query for w in ["ритуал", "обряд", "ceremony"]):
                action = "ритуал"
            else:
                action = "общее"
        
        # Get datetime
        dt = context.get("datetime")
        if dt is None:
            dt = datetime.now()
        elif isinstance(dt, str):
            dt = datetime.fromisoformat(dt.replace("Z", "+00:00"))
        
        # Call MuhurtaSpecialist
        muhurta_context = {
            "action": action,
            "datetime": dt.isoformat(),
            "lat": context.get("lat", self.lat),
            "lon": context.get("lon", self.lon),
            "days_ahead": context.get("days_ahead", 7),
        }
        
        try:
            muhurta_result = await self.muhurta.analyze(muhurta_context)
            
            # Return MuhurtaSpecialist's result directly
            return AgentResponse(
                agent_name="AstroCouncil",
                signal=muhurta_result.signal,
                confidence=muhurta_result.confidence,
                summary=muhurta_result.summary,
                details={
                    **muhurta_result.details,
                    "analysis_type": "muhurta",
                    "action": action,
                }
            )
        except Exception as e:
            return AgentResponse(
                agent_name="AstroCouncil",
                signal="ERROR",
                confidence=0,
                summary=f"Muhurta analysis failed: {str(e)}",
                details={"error": str(e), "analysis_type": "muhurta"}
            )

    def _call_ephemeris(self, date: str, time: str) -> Dict:
        """
        Call Swiss Ephemeris tool with retry and fallback.
        
        ENFORCEMENT: This is the ONLY way to get astrological data.
        """
        if not EPHEMERIS_AVAILABLE:
            raise RuntimeError(
                "Swiss Ephemeris not available. "
                "Install with: pip install swissEph"
            )
        
        try:
            # Primary attempt with user coordinates
            result = swiss_ephemeris(
                date=date,
                time=time,
                lat=self.lat,
                lon=self.lon,
                ayanamsa=self.ayanamsa,
                zodiac=self.zodiac,
                house_system=self.house_system,
                compute_houses=True,
                compute_panchanga=True,
                compute_choghadiya=True,
                compute_ashtakavarga=True,
            )
            
            # Check for errors in result
            if result.get("error") or not result.get("positions"):
                raise ValueError(f"Ephemeris returned error: {result.get('error')}")
            
            return result
            
        except Exception as e:
            # Fallback: Use Delhi coordinates and retry
            print(f"[AstroCouncil] Ephemeris error: {e}. Retrying with fallback coords...")
            
            result = swiss_ephemeris(
                date=date,
                time=time,
                lat=28.6139,  # Delhi fallback
                lon=77.2090,
                ayanamsa="lahiri",
                zodiac="sidereal",
                house_system="W",
                compute_houses=True,
                compute_panchanga=True,
                compute_choghadiya=True,
                compute_ashtakavarga=True,
            )
            
            if result.get("error") or not result.get("positions"):
                raise RuntimeError(
                    f"Swiss Ephemeris failed even with fallback: {e}. "
                    "Cannot proceed without ephemeris data."
                )
            
            return result

    def _get_rag_context(self, query: str, top_k: int = 3) -> Optional[str]:
        """Get context from RAG (Obsidian Vault)."""
        try:
            from rag import ObsidianKnowledgeBase
            
            vault_path = os.environ.get(
                "OBSIDIAN_VAULT_PATH",
                "/home/workspace/obsidian-sync"
            )
            persist_dir = os.environ.get(
                "RAG_PERSIST_DIR",
                "/home/workspace/asurdevSentinel/data/rag_index"
            )
            
            kb = ObsidianKnowledgeBase(
                vault_path=vault_path,
                persist_dir=persist_dir
            )
            
            return kb.get_context(query, max_length=1500)
        except Exception as e:
            print(f"[AstroCouncil] RAG not available: {e}")
            return None

    @staticmethod
    def _summarize(result: Dict, panchanga: Dict, choghadiya: Dict) -> str:
        """Create brief summary of result."""
        sig = result.get("signal", "NEUTRAL")
        conf = result.get("confidence", 50)
        
        nakshatra = panchanga.get("nakshatra", "Unknown")
        yoga = panchanga.get("yoga", "Unknown")
        chogh_type = choghadiya.get("type", "Unknown")
        
        return (
            f"🌙 AstroCouncil: {sig} ({conf}%)\n"
            f"   Nakshatra: {nakshatra} | Yoga: {yoga}\n"
            f"   Choghadiya: {chogh_type}"
        )


# =============================================================================
# STANDALONE TEST
# =============================================================================

async def test_astro_council():
    """Test AstroCouncil with Swiss Ephemeris enforcement."""
    print("🔮 asurdev Core → Swiss Ephemeris v3.2 загружен")
    print("=" * 60)
    
    agent = AstroCouncilAgent(
        lat=55.7558,
        lon=37.6173,
        use_rag=False
    )
    
    context = {
        "datetime": datetime.now().isoformat(),
        "symbol": "BTC"
    }
    
    result = await agent.analyze(context)
    
    print(f"\nSignal: {result.signal}")
    print(f"Confidence: {result.confidence}%")
    print(f"\nSummary:\n{result.summary}")
    print(f"\nDetails keys: {list(result.details.keys())}")
    
    # Show ephemeris data
    eph = result.details.get("ephemeris", {})
    print(f"\nEphemeris positions: {list(eph.get('positions', {}).keys())}")
    print(f"Panchanga: {eph.get('panchanga', {})}")
    print(f"Current Choghadiya: {eph.get('current_choghadiya', {})}")
    
    return result


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_astro_council())
