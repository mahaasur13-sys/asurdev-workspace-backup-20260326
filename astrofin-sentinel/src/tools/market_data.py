import httpx
import os
from datetime import datetime


COINGECKO_BASE = "https://pro-api.coingecko.com/api/v3"
API_KEY = os.getenv("COINGECKO_API_KEY", "")


async def get_market_data_cg(symbol: str, timeframe: str = "7d") -> dict:
    """Fetch market data from CoinGecko Pro API."""
    headers = {"x-cg-pro-api-key": API_KEY} if API_KEY else {}
    
    # Map symbol to CoinGecko ID
    symbol_map = {
        "bitcoin": "bitcoin", "btc": "bitcoin",
        "ethereum": "ethereum", "eth": "ethereum",
        "solana": "solana", "sol": "solana"
    }
    coin_id = symbol_map.get(symbol.lower(), symbol.lower())
    
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{COINGECKO_BASE}/coins/{coin_id}/market_chart",
            headers=headers,
            params={"vs_currency": "usd", "days": timeframe}
        )
        resp.raise_for_status()
        data = resp.json()
    
    prices = data["prices"]
    volumes = data["total_volumes"]
    
    # Calculate metrics
    current_price = prices[-1][1] if prices else 0
    start_price = prices[0][1] if prices else 0
    change_24h = ((current_price - start_price) / start_price * 100) if start_price else 0
    
    avg_volume = sum(v[1] for v in volumes) / len(volumes) if volumes else 0
    
    return {
        "price": current_price,
        "change_24h": change_24h,
        "volume_24h": volumes[-1][1] if volumes else 0,
        "avg_volume": avg_volume,
        "market_cap": data.get("market_caps", [[0, 0]])[-1][1],
        "ath": data.get("market_caps", [[0, current_price]])[-1][1] * 1.5,  # Estimate
        "ath_change": -33,  # Placeholder
        "high_24h": max(p[1] for p in prices) if prices else current_price,
        "low_24h": min(p[1] for p in prices) if prices else current_price,
    }


def get_market_data(symbol: str, timeframe: str = "1") -> dict:
    """Sync wrapper for market data."""
    import asyncio
    try:
        return asyncio.get_event_loop().run_until_complete(
            get_market_data_cg(symbol, timeframe)
        )
    except RuntimeError:
        return asyncio.run(get_market_data_cg(symbol, timeframe))


def get_technical_indicators(symbol: str, timeframe: str = "1") -> dict:
    """
    Calculate basic technical indicators.
    In production, use pandas-ta or similar for proper TA.
    """
    # For demo - in production integrate with ta-lib or pandas-ta
    # This is a simplified placeholder
    
    data = get_market_data(symbol, timeframe)
    price = data["price"]
    
    # Very basic indicators for demo
    change = data["change_24h"]
    
    # RSI approximation
    if change > 5:
        rsi = 70
    elif change < -5:
        rsi = 30
    else:
        rsi = 50 + change * 2
    
    rsi = max(0, min(100, rsi))
    
    # Trend based on price action
    if change > 3:
        trend = "bullish"
    elif change < -3:
        trend = "bearish"
    else:
        trend = "neutral"
    
    # Support/Resistance
    high = data["high_24h"]
    low = data["low_24h"]
    support = low * 1.01
    resistance = high * 0.99
    
    # MACD signal
    if change > 2:
        macd_signal = "bullish crossover"
    elif change < -2:
        macd_signal = "bearish crossover"
    else:
        macd_signal = "neutral"
    
    return {
        "trend": trend,
        "support": support,
        "resistance": resistance,
        "rsi": rsi,
        "macd_signal": macd_signal,
        "signals": [
            f"RSI at {rsi:.0f} ({'overbought' if rsi > 70 else 'oversold' if rsi < 30 else 'neutral'})",
            f"Price {trend}",
            f"{macd_signal}"
        ],
        "confidence": 0.6
    }


# --- Pydantic models for type safety ---
from src.types import MarketData, TimeFrame, Symbol
from typing import Literal


def get_market_data_typed(symbol: Symbol, timeframe: TimeFrame) -> MarketData:
    """Get market data with proper typing."""
    tf_map = {
        "1h": "1",
        "4h": "1",
        "1d": "7",
        "7d": "7"
    }
    data = get_market_data(symbol.value, tf_map.get(timeframe.value, "1"))
    
    return MarketData(
        symbol=symbol,
        timeframe=timeframe,
        price=data["price"],
        change_24h=data["change_24h"],
        volume=data["volume_24h"],
        market_cap=data["market_cap"],
        ath=data["ath"],
        ath_change=data["ath_change"],
        high_24h=data["high_24h"],
        low_24h=data["low_24h"],
        fetched_at=datetime.utcnow()
    )
