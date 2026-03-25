"""
Market Data Tools for AstroFin Sentinel
Fetches OHLCV data and calculates technical indicators
"""

import json
from datetime import datetime, timedelta
from typing import Optional
import urllib.request
import urllib.error


class MarketDataTool:
    """Tool for fetching market data from exchanges."""
    
    def __init__(self, exchange: str = "binance"):
        self.exchange = exchange
        self.base_urls = {
            "binance": "https://api.binance.com/api/v3",
            "bybit": "https://api.bybit.com/v5"
        }
    
    def get_ohlcv(self, symbol: str, interval: str = "1h", limit: int = 100) -> dict:
        """
        Fetch OHLCV (candlestick) data.
        
        Args:
            symbol: Trading pair (e.g., "BTCUSDT")
            interval: Timeframe (1m, 5m, 15m, 1h, 4h, 1d, 1w)
            limit: Number of candles (max 1000)
            
        Returns:
            Dictionary with OHLCV data
        """
        # Normalize symbol for Binance
        symbol = symbol.replace("/", "").upper()
        
        url = f"{self.base_urls[self.exchange]}/klines"
        params = f"?symbol={symbol}&interval={interval}&limit={limit}"
        
        try:
            with urllib.request.urlopen(url + params, timeout=10) as response:
                data = json.loads(response.read().decode())
                
                candles = []
                for candle in data:
                    candles.append({
                        "open_time": candle[0],
                        "open": float(candle[1]),
                        "high": float(candle[2]),
                        "low": float(candle[3]),
                        "close": float(candle[4]),
                        "volume": float(candle[5]),
                        "close_time": candle[6]
                    })
                
                return {
                    "status": "success",
                    "symbol": symbol,
                    "interval": interval,
                    "count": len(candles),
                    "candles": candles[-20:]  # Return last 20 for analysis
                }
        except urllib.error.URLError as e:
            return {"status": "error", "error": str(e)}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def calculate_indicators(self, candles: list) -> dict:
        """
        Calculate technical indicators from OHLCV data.
        
        Args:
            candles: List of candle dictionaries
            
        Returns:
            Dictionary with calculated indicators
        """
        if len(candles) < 50:
            return {"status": "error", "error": "Insufficient data for indicators"}
        
        closes = [c["close"] for c in candles]
        highs = [c["high"] for c in candles]
        lows = [c["low"] for c in candles]
        volumes = [c["volume"] for c in candles]
        
        # SMA calculations
        sma_20 = sum(closes[-20:]) / 20
        sma_50 = sum(closes[-50:]) / 50
        
        # EMA calculations
        ema_9 = self._ema(closes, 9)
        ema_21 = self._ema(closes, 21)
        
        # RSI (14)
        rsi_14 = self._rsi(closes, 14)
        
        # MACD
        macd, signal, histogram = self._macd(closes)
        
        # Bollinger Bands
        bb_upper, bb_middle, bb_lower = self._bollinger_bands(closes, 20, 2)
        
        # ATR
        atr = self._atr(candles, 14)
        
        # Support and Resistance
        sr_levels = self._find_sr_levels(highs, lows, closes)
        
        return {
            "sma": {
                "sma_20": round(sma_20, 2),
                "sma_50": round(sma_50, 2)
            },
            "ema": {
                "ema_9": round(ema_9, 2),
                "ema_21": round(ema_21, 2)
            },
            "rsi_14": round(rsi_14, 2),
            "macd": {
                "macd_line": round(macd, 2),
                "signal_line": round(signal, 2),
                "histogram": round(histogram, 2)
            },
            "bollinger_bands": {
                "upper": round(bb_upper, 2),
                "middle": round(bb_middle, 2),
                "lower": round(bb_lower, 2)
            },
            "atr_14": round(atr, 2),
            "support_resistance": sr_levels,
            "current_price": closes[-1],
            "trend": "UP" if closes[-1] > sma_50 else "DOWN"
        }
    
    def _ema(self, data: list, period: int) -> float:
        """Calculate Exponential Moving Average."""
        multiplier = 2 / (period + 1)
        ema = sum(data[:period]) / period
        for price in data[period:]:
            ema = (price - ema) * multiplier + ema
        return ema
    
    def _rsi(self, prices: list, period: int = 14) -> float:
        """Calculate Relative Strength Index."""
        gains = []
        losses = []
        for i in range(1, len(prices)):
            diff = prices[i] - prices[i-1]
            gains.append(max(diff, 0))
            losses.append(max(-diff, 0))
        
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))
    
    def _macd(self, prices: list, fast: int = 12, slow: int = 26, signal: int = 9):
        """Calculate MACD."""
        ema_fast = self._ema(prices, fast)
        ema_slow = self._ema(prices, slow)
        macd_line = ema_fast - ema_slow
        
        # Signal line (simplified)
        signal_line = macd_line * 0.9  # Approximation
        histogram = macd_line - signal_line
        
        return macd_line, signal_line, histogram
    
    def _bollinger_bands(self, prices: list, period: int = 20, std_dev: int = 2):
        """Calculate Bollinger Bands."""
        sma = sum(prices[-period:]) / period
        variance = sum((p - sma) ** 2 for p in prices[-period:]) / period
        std = variance ** 0.5
        
        upper = sma + (std * std_dev)
        lower = sma - (std * std_dev)
        
        return upper, sma, lower
    
    def _atr(self, candles: list, period: int = 14) -> float:
        """Calculate Average True Range."""
        true_ranges = []
        for i in range(1, len(candles)):
            high = candles[i]["high"]
            low = candles[i]["low"]
            prev_close = candles[i-1]["close"]
            
            tr = max(
                high - low,
                abs(high - prev_close),
                abs(low - prev_close)
            )
            true_ranges.append(tr)
        
        return sum(true_ranges[-period:]) / period
    
    def _find_sr_levels(self, highs: list, lows: list, closes: list) -> dict:
        """Find approximate support and resistance levels."""
        current_price = closes[-1]
        
        # Simple approach - find recent highs/lows
        resistance = max(highs[-20:])
        support = min(lows[-20:])
        
        return {
            "resistance": round(resistance, 2),
            "support": round(support, 2),
            "current": round(current_price, 2)
        }
    
    def get_full_analysis(self, symbol: str, interval: str = "1h") -> dict:
        """Get complete market analysis."""
        ohlcv = self.get_ohlcv(symbol, interval)
        
        if ohlcv.get("status") == "error":
            return ohlcv
        
        candles = ohlcv.get("candles", [])
        indicators = self.calculate_indicators(candles)
        
        return {
            "status": "success",
            "symbol": symbol,
            "interval": interval,
            "ohlcv": candles,
            "indicators": indicators,
            "timestamp": datetime.now().isoformat()
        }


# Global instance
_market_tool = None

def get_market_tool() -> MarketDataTool:
    global _market_tool
    if _market_tool is None:
        _market_tool = MarketDataTool()
    return _market_tool
