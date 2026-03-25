"""
Sentinel v4.1 — LangChain Tools
Web search, crypto prices, news, astro events.
"""
import os
import json
import requests
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

from langchain_core.tools import tool, StructuredTool


# ============================================================
# CRYPTO PRICE TOOL
# ============================================================

@tool
def get_crypto_price(symbol: str) -> dict:
    """
    Get current price and 24h change for a cryptocurrency.
    
    Args:
        symbol: Crypto symbol (e.g., 'BTC', 'ETH', 'SOL')
    
    Returns:
        dict with price_usd, change_24h, market_cap, volume_24h, symbol
    """
    symbol = symbol.upper()
    
    try:
        # Try CoinGecko
        url = f"https://api.coingecko.com/api/v3/simple/price"
        params = {
            "ids": _coin_symbol_to_id(symbol),
            "vs_currencies": "usd",
            "include_24hr_change": "true",
            "include_market_cap": "true",
            "include_24hr_vol": "true"
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            coin_id = _coin_symbol_to_id(symbol)
            
            if coin_id in data:
                return {
                    "symbol": symbol,
                    "price_usd": data[coin_id].get("usd", 0),
                    "change_24h": data[coin_id].get("usd_24h_change", 0),
                    "market_cap": data[coin_id].get("usd_market_cap", 0),
                    "volume_24h": data[coin_id].get("usd_24h_vol", 0),
                    "source": "coingecko"
                }
        
        return {"error": f"Could not fetch {symbol}", "symbol": symbol}
    
    except Exception as e:
        return {"error": str(e), "symbol": symbol}


@tool
def get_crypto_historical(symbol: str, days: int = 30) -> dict:
    """
    Get historical price data for a cryptocurrency.
    
    Args:
        symbol: Crypto symbol (e.g., 'BTC')
        days: Number of days of history (default 30, max 365)
    
    Returns:
        dict with prices array and current price
    """
    symbol = symbol.upper()
    days = min(days, 365)
    
    try:
        coin_id = _coin_symbol_to_id(symbol)
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
        params = {
            "vs_currency": "usd",
            "days": str(days),
            "interval": "daily" if days > 30 else None
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            prices = data.get("prices", [])
            
            return {
                "symbol": symbol,
                "days": days,
                "current_price": prices[-1][1] if prices else 0,
                "price_count": len(prices),
                "source": "coingecko"
            }
        
        return {"error": f"Could not fetch {symbol} history", "symbol": symbol}
    
    except Exception as e:
        return {"error": str(e), "symbol": symbol}


def _coin_symbol_to_id(symbol: str) -> str:
    """Map common symbols to CoinGecko IDs."""
    mapping = {
        "BTC": "bitcoin",
        "ETH": "ethereum",
        "SOL": "solana",
        "XRP": "ripple",
        "ADA": "cardano",
        "DOGE": "dogecoin",
        "DOT": "polkadot",
        "AVAX": "avalanche-2",
        "LINK": "chainlink",
        "MATIC": "matic-network",
        "UNI": "uniswap",
        "ATOM": "cosmos",
        "LTC": "litecoin",
        "ETC": "ethereum-classic",
        "FIL": "filecoin",
        "APT": "aptos",
        "ARB": "arbitrum",
        "OP": "optimism",
        "NEAR": "near",
        "INJ": "injective-protocol",
        "SUI": "sui",
        "SEI": "sei-network",
        "TIA": "celestia",
        "SAND": "the-sandbox",
        "MANA": "decentraland",
        "AXS": "axie-infinity",
        "AAVE": "aave",
        "CRV": "curve-dao-token",
        "LDO": "lido-dao",
        "MKR": "maker"
    }
    return mapping.get(symbol, symbol.lower())


# ============================================================
# NEWS SEARCH TOOL
# ============================================================

@tool
def search_financial_news(query: str, limit: int = 5) -> dict:
    """
    Search for financial and crypto news.
    
    Args:
        query: Search query (e.g., 'Bitcoin ETF approval', 'crypto regulation')
        limit: Maximum number of results (default 5)
    
    Returns:
        dict with articles list containing title, url, source, published_at
    """
    try:
        # Try Tavily first (better for finance)
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
                    "total": len(data.get("results", [])),
                    "source": "tavily"
                }
        
        # Fallback to Brave Search
        brave_key = os.environ.get("BRAVE_API_KEY")
        
        if brave_key:
            url = "https://api.search.brave.com/res/v1/news/search"
            headers = {"X-Subscription-Token": brave_key}
            params = {
                "q": query,
                "count": limit,
                "freshness": "pd"  # Past day
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                articles = []
                for item in data.get("results", [])[:limit]:
                    articles.append({
                        "title": item.get("title"),
                        "url": item.get("url"),
                        "source": item.get("meta_url", {}).get("netloc", "").replace("www.", ""),
                        "published_at": item.get("age", "")
                    })
                
                return {
                    "query": query,
                    "results": articles,
                    "total": len(articles),
                    "source": "brave"
                }
        
        return {
            "error": "No API keys set. Set TAVILY_API_KEY or BRAVE_API_KEY",
            "query": query
        }
    
    except Exception as e:
        return {"error": str(e), "query": query}


@tool
def get_crypto_sentiment(symbol: str) -> dict:
    """
    Get overall sentiment for a cryptocurrency from recent news.
    
    Args:
        symbol: Crypto symbol (e.g., 'BTC', 'ETH')
    
    Returns:
        dict with sentiment score (-100 to +100), article_count, top_topics
    """
    symbol = symbol.upper()
    
    try:
        # Get news
        news = search_financial_news.invoke(f"{symbol} cryptocurrency market")
        
        if "error" in news:
            return {"symbol": symbol, "sentiment": 0, "error": news["error"]}
        
        articles = news.get("results", [])
        
        if not articles:
            return {"symbol": symbol, "sentiment": 0, "article_count": 0}
        
        # Simple keyword-based sentiment
        positive = ["bull", "rise", "gain", "surge", "up", "growth", "adoption", "breakthrough", "rally"]
        negative = ["bear", "fall", "drop", "crash", "lose", "decline", "regulation", "ban", "hack", "scam"]
        
        score = 0
        topics = []
        
        for article in articles:
            title = article.get("title", "").lower()
            
            for p in positive:
                if p in title:
                    score += 10
            for n in negative:
                if n in title:
                    score -= 10
        
        sentiment = max(-100, min(100, score))
        
        return {
            "symbol": symbol,
            "sentiment": sentiment,
            "interpretation": _sentiment_interpretation(sentiment),
            "article_count": len(articles),
            "top_topics": topics[:5]
        }
    
    except Exception as e:
        return {"symbol": symbol, "sentiment": 0, "error": str(e)}


def _sentiment_interpretation(score: int) -> str:
    """Convert score to text."""
    if score >= 50:
        return "Very Bullish"
    elif score >= 20:
        return "Bullish"
    elif score >= -20:
        return "Neutral"
    elif score >= -50:
        return "Bearish"
    else:
        return "Very Bearish"


# ============================================================
# ASTROLOGICAL EVENTS TOOL
# ============================================================

@tool
def get_upcoming_astro_events(days: int = 30, latitude: float = 55.75, longitude: float = 37.62) -> dict:
    """
    Get upcoming astrological events (aspects, retrogrades, lunations).
    
    Args:
        days: Number of days ahead to look (default 30)
        latitude: Observer latitude for horoscopes
        longitude: Observer longitude for horoscopes
    
    Returns:
        dict with events list
    """
    try:
        # Note: pip package is 'pyswisseph' but import name is 'swisseph'
        import swisseph as swe
        from datetime import datetime, timedelta
        
        now = datetime.utcnow()
        events = []
        
        # Swiss planet constants
        _PLANETS = {
            "sun": swe.SUN,
            "moon": swe.MOON,
            "mercury": swe.MERCURY,
            "venus": swe.VENUS,
            "mars": swe.MARS,
            "jupiter": swe.JUPITER,
            "saturn": swe.SATURN,
        }
        
        # Key aspects to track
        aspect_pairs = [
            ("sun", "moon"),  # New/Full Moon tracking
            ("jupiter", "saturn"),  # Great Conjunction
            ("mars", "saturn"),  # Tension
            ("venus", "mars"),  # Passion
        ]
        
        for i in range(days):
            d = now + timedelta(days=i)
            jd = swe.julday(d.year, d.month, d.day, 12)  # Noon UTC
            
            # Get planetary positions
            positions = {}
            for planet, planet_id in _PLANETS.items():
                result = swe.calc(jd, planet_id)
                xx = result[0] if isinstance(result, tuple) else result
                positions[planet] = xx[0]  # Longitude
            
            # Check for aspects (within 2 degrees)
            for p1, p2 in aspect_pairs:
                if p1 not in positions or p2 not in positions:
                    continue
                
                diff = abs(positions[p1] - positions[p2])
                if diff > 180:
                    diff = 360 - diff
                
                # Exact aspect (within 2 deg)
                for aspect_deg, aspect_name in [(0, "conjunction"), (60, "sextile"), 
                                                 (90, "square"), (120, "trine"), (180, "opposition")]:
                    if abs(diff - aspect_deg) < 2:
                        events.append({
                            "date": d.strftime("%Y-%m-%d"),
                            "event": f"{aspect_name.title()} {p1.title()}-{p2.title()}",
                            "type": "aspect",
                            "exact_degree": round(diff, 1)
                        })
            
            # Check for retrograde transitions (simplified)
            # In production, compare speeds across days
        
        # Sort by date
        events.sort(key=lambda x: x["date"])
        
        return {
            "days": days,
            "event_count": len(events),
            "events": events[:20]  # Limit output
        }
    
    except ImportError:
        return {"error": "Swiss Ephemeris not installed. Run: pip install pyswisseph"}
    except Exception as e:
        return {"error": str(e)}


@tool  
def get_moon_phase(date: str = None) -> dict:
    """
    Get current moon phase or for specific date.
    
    Args:
        date: Date string YYYY-MM-DD (default: today)
    
    Returns:
        dict with phase name, illumination %, zodiac position
    """
    try:
        # Note: pip package is 'pyswisseph' but import name is 'swisseph'
        import swisseph as swe
        
        if date:
            d = datetime.strptime(date, "%Y-%m-%d")
        else:
            d = datetime.utcnow()
        
        jd = swe.julday(d.year, d.month, d.day, 12)
        
        # Moon position
        moon_result = swe.calc(jd, swe.MOON)
        moon_xx = moon_result[0] if isinstance(moon_result, tuple) else moon_result
        moon_lon = moon_xx[0]
        
        # Sun position
        sun_result = swe.calc(jd, swe.SUN)
        sun_xx = sun_result[0] if isinstance(sun_result, tuple) else sun_result
        sun_lon = sun_xx[0]
        
        # Phase calculation
        diff = (moon_lon - sun_lon) % 360
        illumination = (1 - abs(diff - 180) / 180) * 100
        
        # Phase names
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
        
        # Zodiac sign
        signs = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
                 "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
        sign_idx = int(moon_lon // 30) % 12
        sign_deg = moon_lon % 30
        
        return {
            "date": d.strftime("%Y-%m-%d"),
            "phase": phase,
            "illumination_pct": round(illumination, 1),
            "moon_longitude": round(moon_lon, 2),
            "zodiac_sign": signs[sign_idx],
            "zodiac_degree": round(sign_deg, 1)
        }
    
    except ImportError:
        return {"error": "Swiss Ephemeris not installed"}
    except Exception as e:
        return {"error": str(e)}


# ============================================================
# TRADING ECONOMICS CALENDAR
# ============================================================

@tool
def get_economic_calendar(days: int = 7, symbols: List[str] = None) -> dict:
    """
    Get upcoming economic events that affect markets.
    
    Args:
        days: Days ahead (default 7)
        symbols: Optional list of symbols to filter events for (e.g., ['BTC', 'ETH'])
    
    Returns:
        dict with events list
    """
    try:
        # Trading Economics free API
        api_key = os.environ.get("TRADING_ECONOMICS_API_KEY")
        
        events = []
        
        # High-impact events to track
        high_impact = ["interest rate", "inflation", "gdp", "employment", 
                       "federal reserve", "ecb", "unemployment", "pce", "cpi", "ppi"]
        
        # For now, return placeholder since TE requires paid API
        # In production, integrate with their API
        return {
            "days": days,
            "events": [
                {
                    "date": "2026-03-25",
                    "event": "US Federal Reserve Interest Rate Decision",
                    "country": "United States",
                    "impact": "high",
                    "previous": "4.50%",
                    "forecast": "4.25%"
                },
                {
                    "date": "2026-03-27",
                    "event": "US PCE Inflation Rate",
                    "country": "United States",
                    "impact": "high",
                    "previous": "2.6%",
                    "forecast": "2.5%"
                },
                {
                    "date": "2026-03-28",
                    "event": "US Unemployment Claims",
                    "country": "United States",
                    "impact": "medium",
                    "previous": "215K",
                    "forecast": "210K"
                }
            ],
            "note": "Connect TRADING_ECONOMICS_API_KEY for live data"
        }
    
    except Exception as e:
        return {"error": str(e)}


# ============================================================
# TOOL REGISTRY
# ============================================================

def get_all_tools() -> List:
    """Get all LangChain tools for agent use."""
    return [
        get_crypto_price,
        get_crypto_historical,
        search_financial_news,
        get_crypto_sentiment,
        get_upcoming_astro_events,
        get_moon_phase,
        get_economic_calendar,
    ]


def get_tools_dict() -> Dict[str, Any]:
    """Get tools as dict for convenience."""
    return {tool.name: tool for tool in get_all_tools()}
