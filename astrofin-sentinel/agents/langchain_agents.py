"""
LangChain Agents для AstroFin Sentinel v4.1.

Использует LangChain для tool-calling и управления агентами.
Интегрирует crypto, news, astro tools.
"""

import os
import json
import logging
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_ollama import ChatOllama
from langchain_core.tools import tool, StructuredTool

from .base import AgentInput, AgentOutput
from core.config import settings

logger = logging.getLogger(__name__)


# ============================================================
# TOOL DEFINITIONS (LangChain format)
# ============================================================

@tool
def get_crypto_price(symbol: str) -> dict:
    """Get current price and 24h change for a cryptocurrency.
    
    Args:
        symbol: Crypto symbol (e.g., 'BTC', 'ETH', 'SOL')
    
    Returns:
        dict with price_usd, change_24h, market_cap, volume_24h
    """
    import requests
    
    symbol = symbol.upper()
    mapping = {
        "BTC": "bitcoin", "ETH": "ethereum", "SOL": "solana",
        "XRP": "ripple", "ADA": "cardano", "DOGE": "dogecoin",
        "DOT": "polkadot", "AVAX": "avalanche-2", "LINK": "chainlink",
    }
    coin_id = mapping.get(symbol, symbol.lower())
    
    try:
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {
            "ids": coin_id,
            "vs_currencies": "usd",
            "include_24hr_change": "true",
            "include_market_cap": "true",
            "include_24hr_vol": "true"
        }
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if coin_id in data:
                return {
                    "symbol": symbol,
                    "price_usd": data[coin_id].get("usd", 0),
                    "change_24h": data[coin_id].get("usd_24h_change", 0),
                    "market_cap": data[coin_id].get("usd_market_cap", 0),
                    "volume_24h": data[coin_id].get("usd_24h_vol", 0),
                }
        return {"error": f"Could not fetch {symbol}"}
    except Exception as e:
        return {"error": str(e)}


@tool
def get_crypto_historical(symbol: str, days: int = 30) -> dict:
    """Get historical price data for a cryptocurrency.
    
    Args:
        symbol: Crypto symbol (e.g., 'BTC')
        days: Number of days of history (default 30)
    """
    import requests
    
    symbol = symbol.upper()
    days = min(days, 365)
    mapping = {
        "BTC": "bitcoin", "ETH": "ethereum", "SOL": "solana",
        "XRP": "ripple", "ADA": "cardano", "DOGE": "dogecoin",
    }
    coin_id = mapping.get(symbol, symbol.lower())
    
    try:
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
        params = {"vs_currency": "usd", "days": str(days)}
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            prices = data.get("prices", [])
            if prices:
                return {
                    "symbol": symbol,
                    "days": days,
                    "current_price": prices[-1][1],
                    "start_price": prices[0][1],
                    "price_change_pct": ((prices[-1][1] - prices[0][1]) / prices[0][1]) * 100,
                    "data_points": len(prices),
                }
        return {"error": f"Could not fetch {symbol} history"}
    except Exception as e:
        return {"error": str(e)}


@tool
def get_moon_phase(date: str = None) -> dict:
    """Get current moon phase or for specific date.
    
    Args:
        date: Date string YYYY-MM-DD (default: today)
    
    Returns:
        dict with phase name, illumination %, zodiac position
    """
    from datetime import datetime
    try:
        import swisseph as swe
        
        if date:
            d = datetime.strptime(date, "%Y-%m-%d")
        else:
            d = datetime.utcnow()
        
        jd = swe.julday(d.year, d.month, d.day, 12)
        
        moon_result = swe.calc(jd, swe.MOON)
        moon_lon = moon_result[0][0]
        
        sun_result = swe.calc(jd, swe.SUN)
        sun_lon = sun_result[0][0]
        
        diff = (moon_lon - sun_lon) % 360
        illumination = (1 - abs(diff - 180) / 180) * 100
        
        if diff < 22.5:
            phase = "New Moon"
        elif diff < 67.5:
            phase = "Waxing Crescent"
        elif diff < 112.5:
            phase = "First Quarter"
        elif diff < 157.5:
            phase = "Waxing Gibbous"
        elif diff < 202.5:
            phase = "Full Moon"
        elif diff < 247.5:
            phase = "Waning Gibbous"
        elif diff < 292.5:
            phase = "Last Quarter"
        elif diff < 337.5:
            phase = "Waning Crescent"
        else:
            phase = "New Moon"
        
        signs = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
                 "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
        sign_idx = int(moon_lon // 30) % 12
        
        return {
            "date": d.strftime("%Y-%m-%d"),
            "phase": phase,
            "illumination_pct": round(illumination, 1),
            "zodiac_sign": signs[sign_idx],
            "zodiac_degree": round(moon_lon % 30, 1),
        }
    except ImportError:
        return {"error": "Swiss Ephemeris not installed. Run: pip install pyswisseph"}
    except Exception as e:
        return {"error": str(e)}


@tool
def get_astro_aspects(days: int = 7) -> dict:
    """Get upcoming major astrological aspects.
    
    Args:
        days: Number of days ahead to look (default 7)
    
    Returns:
        dict with major aspects (conjunctions, oppositions, etc.)
    """
    from datetime import datetime, timedelta
    try:
        import swisseph as swe
        
        now = datetime.utcnow()
        events = []
        
        _PLANETS = {
            "sun": swe.SUN, "moon": swe.MOON, "mercury": swe.MERCURY,
            "venus": swe.VENUS, "mars": swe.MARS, "jupiter": swe.JUPITER,
            "saturn": swe.SATURN,
        }
        
        for i in range(days):
            d = now + timedelta(days=i)
            jd = swe.julday(d.year, d.month, d.day, 12)
            
            positions = {}
            for planet, pid in _PLANETS.items():
                result = swe.calc(jd, pid)
                positions[planet] = result[0][0]
            
            # Check major aspects
            for p1, p2 in [("jupiter", "saturn"), ("mars", "saturn"), ("venus", "mars")]:
                if p1 not in positions or p2 not in positions:
                    continue
                diff = abs(positions[p1] - positions[p2])
                if diff > 180:
                    diff = 360 - diff
                
                for aspect_deg, name in [(0, "conjunction"), (120, "trine"), (180, "opposition")]:
                    if abs(diff - aspect_deg) < 3:
                        events.append({
                            "date": d.strftime("%Y-%m-%d"),
                            "aspect": f"{name} {p1}-{p2}",
                            "exactness_deg": round(abs(diff - aspect_deg), 1)
                        })
        
        return {"days": days, "events": events[:15]}
    except ImportError:
        return {"error": "Swiss Ephemeris not installed"}
    except Exception as e:
        return {"error": str(e)}


@tool
def search_market_news(query: str, limit: int = 5) -> dict:
    """Search for financial and crypto news.
    
    Args:
        query: Search query (e.g., 'Bitcoin ETF', 'crypto regulation')
        limit: Maximum number of results (default 5)
    
    Returns:
        dict with articles list
    """
    import requests
    
    try:
        tavily_key = os.environ.get("TAVILY_API_KEY")
        if tavily_key:
            url = "https://api.tavily.com/search"
            headers = {"api-key": tavily_key}
            params = {
                "query": f"{query} finance crypto",
                "search_depth": "basic",
                "max_results": limit
            }
            response = requests.post(url, headers=headers, json=params, timeout=15)
            if response.status_code == 200:
                data = response.json()
                return {
                    "query": query,
                    "results": data.get("results", [])[:limit],
                    "source": "tavily"
                }
        
        # Fallback
        return {
            "query": query,
            "results": [],
            "note": "Set TAVILY_API_KEY for live news"
        }
    except Exception as e:
        return {"error": str(e)}


def get_tools() -> List[StructuredTool]:
    """Get all LangChain tools."""
    return [
        get_crypto_price,
        get_crypto_historical,
        get_moon_phase,
        get_astro_aspects,
        search_market_news,
    ]


# ============================================================
# LANGCHAIN-BASED AGENT
# ============================================================

class LangChainAgent:
    """
    Базовый агент на LangChain с tool-calling.
    """
    
    def __init__(
        self,
        name: str,
        model: str | None = None,
        system_prompt: str | None = None,
        tools: List[StructuredTool] | None = None,
    ):
        self.name = name
        self.model_name = model or settings.OLLAMA_MODEL
        self.tools = tools or get_tools()
        
        # System prompt
        self.system_prompt = system_prompt or f"""You are {name}, a professional financial analyst.

You have access to tools for:
- Getting crypto prices and historical data
- Getting astrological information (moon phases, planetary aspects)
- Searching market news

Always use tools to gather real data before giving analysis.
Be concise but thorough. Provide specific numbers and data points.
"""
        
        # Initialize ChatOllama
        self.llm = ChatOllama(
            model=self.model_name,
            base_url=settings.OLLAMA_BASE_URL,
            temperature=settings.OLLAMA_TEMPERATURE,
            timeout=settings.OLLAMA_TIMEOUT,
        ).bind_tools(self.tools)
    
    async def analyze(self, input_data: AgentInput) -> AgentOutput:
        """Analyze using LangChain tool-calling agent."""
        from langchain_core.messages import HumanMessage
        
        # Build context
        context = f"""Analyze {input_data.symbol} trading signal.

Signal: {input_data.action.upper()}
Price: ${input_data.price:,.2f}
Strategy: {input_data.strategy}
Timeframe: {input_data.timeframe}
ML Confidence: {input_data.ml_confidence:.2%}

First, gather relevant data using your tools:
1. Get current price for {input_data.symbol}
2. Get historical data (30 days)
3. Get moon phase and astro aspects
4. Search for relevant news

Then provide your recommendation with confidence score."""

        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=context)
        ]
        
        logger.info(f"[{self.name}] Invoking LangChain agent with tools...")
        
        try:
            # Invoke LLM with tools
            response = self.llm.invoke(messages)
            
            # Extract tool calls if any were made
            tool_calls = []
            if hasattr(response, 'tool_calls') and response.tool_calls:
                for tc in response.tool_calls:
                    tool_calls.append({
                        "tool": tc.get("name"),
                        "args": tc.get("args", {}),
                    })
            
            # Get final response
            reasoning = response.content if hasattr(response, 'content') else str(response)
            
            # Parse recommendation from response
            recommendation, confidence = self._parse_recommendation(reasoning, input_data)
            
            return AgentOutput(
                agent=self.name,
                recommendation=recommendation,
                confidence=confidence,
                reasoning=reasoning[:500],
                key_factors=self._extract_key_factors(reasoning),
                warnings=self._extract_warnings(reasoning),
                metadata={
                    "tool_calls": tool_calls,
                    "model": self.model_name,
                }
            )
            
        except Exception as e:
            logger.error(f"[{self.name}] Error: {e}")
            return AgentOutput(
                agent=self.name,
                recommendation="hold",
                confidence=0.3,
                reasoning=f"Error: {str(e)}",
                key_factors=[],
                warnings=["Agent error"],
                metadata={"error": str(e)}
            )
    
    def _parse_recommendation(self, text: str, input_data: AgentInput) -> tuple[str, float]:
        """Parse recommendation from LLM response."""
        text_lower = text.lower()
        
        # Match recommendation keywords
        if "buy" in text_lower[:100] or "long" in text_lower[:100]:
            rec = "buy"
        elif "sell" in text_lower[:100] or "short" in text_lower[:100]:
            rec = "sell"
        else:
            rec = "hold"
        
        # Estimate confidence from certainty language
        confidence = input_data.ml_confidence
        if "strong" in text_lower or "definite" in text_lower:
            confidence = min(1.0, confidence + 0.15)
        elif "weak" in text_lower or "uncertain" in text_lower:
            confidence = max(0.1, confidence - 0.15)
        
        return rec, confidence
    
    def _extract_key_factors(self, text: str) -> List[str]:
        """Extract key factors from text."""
        factors = []
        keywords = ["rsi", "macd", "volume", "trend", "support", "resistance", 
                    "moon", "aspect", "news", "catalyst"]
        
        text_lower = text.lower()
        for kw in keywords:
            if kw in text_lower:
                idx = text_lower.find(kw)
                snippet = text[max(0, idx-20):min(len(text), idx+50)]
                factors.append(snippet.strip())
        
        return factors[:5]
    
    def _extract_warnings(self, text: str) -> List[str]:
        """Extract warnings from text."""
        warnings = []
        warning_keywords = ["risk", "warning", "caution", "overbought", "oversold",
                          "volatile", "uncertain"]
        
        text_lower = text.lower()
        for kw in warning_keywords:
            if kw in text_lower:
                warnings.append(f"⚠️ {kw.title()}")
        
        return warnings[:3]


# ============================================================
# SPECIALIZED AGENTS
# ============================================================

class LangChainMarketAnalyst(LangChainAgent):
    """Market analyst using LangChain tools."""
    
    def __init__(self):
        system_prompt = """You are a professional technical analyst with deep knowledge of:
- Price action and candlestick patterns
- Indicators: RSI, MACD, Bollinger Bands, Moving Averages
- Volume analysis
- Support and resistance levels
- Market sentiment

Use tools to get real price data and provide actionable insights."""
        
        super().__init__(
            name="market_analyst",
            model=settings.ANALYST_MODEL or settings.OLLAMA_MODEL,
            system_prompt=system_prompt,
        )


class LangChainAstroAdvisor(LangChainAgent):
    """Astro advisor using LangChain tools."""
    
    def __init__(self):
        system_prompt = """You are a financial astrologer specializing in market timing.

Your expertise includes:
- Moon phases and their impact on markets
- Planetary aspects (conjunctions, trines, squares, oppositions)
- Retrograde planets
- Eclipse effects on markets
- Traditional astrology timing techniques

Use tools to get real astrological data. Provide insights on how celestial 
events may influence trading decisions."""
        
        super().__init__(
            name="astro_advisor",
            model=settings.ASTRO_MODEL or settings.OLLAMA_MODEL,
            system_prompt=system_prompt,
        )


class LangChainSynthesisEngine(LangChainAgent):
    """Synthesis engine combining all signals."""
    
    def __init__(self):
        system_prompt = """You are the head of a trading research committee.

Your role is to synthesize input from:
1. Technical Analyst (price action, indicators, patterns)
2. Astro Advisor (celestial timing, planetary influences)
3. Market Researcher (news, sentiment, fundamentals)

Weight the inputs appropriately and provide a FINAL recommendation:
- BUY: Strong bullish case with favorable risk/reward
- SELL: Strong bearish case
- HOLD: Uncertain or conflicting signals

Always consider risk management. Provide specific entry levels and stop losses.
Be decisive - don't sit on the fence."""
        
        super().__init__(
            name="synthesis_engine",
            model=settings.SYNTHESIS_MODEL or settings.OLLAMA_MODEL,
            system_prompt=system_prompt,
        )
