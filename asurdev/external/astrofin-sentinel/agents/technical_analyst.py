"""
Technical Analyst Agent for AstroFin Sentinel

Analyzes market data using technical indicators and price patterns.
"""

import json
from typing import Optional
from dataclasses import dataclass, asdict

from tools.market_data import get_market_tool


@dataclass
class TechnicalReport:
    """Output from Technical Analyst Agent."""
    signal: str  # BUY, SELL, NEUTRAL
    confidence: float  # 0.0 - 1.0
    pattern: str
    levels: dict  # entry, stop_loss, take_profit_1/2/3
    indicators: dict  # trend, momentum, volatility
    reasoning: str
    symbol: str = ""
    interval: str = ""


class TechnicalAnalystAgent:
    """
    Technical Analyst Agent.
    
    Analyzes charts, patterns, and technical indicators
    to generate trading signals.
    """
    
    def __init__(self):
        self.market_tool = get_market_tool()
        self.system_prompt = self._load_system_prompt()
    
    def _load_system_prompt(self) -> str:
        """Load system prompt from file."""
        try:
            with open("prompts/technical_analyst.txt", "r") as f:
                return f.read()
        except FileNotFoundError:
            return "You are a technical analyst."
    
    def analyze(self, symbol: str, interval: str = "1h", asset_type: str = "crypto") -> TechnicalReport:
        """
        Perform technical analysis on a symbol.
        
        Args:
            symbol: Trading pair (e.g., "BTC/USDT" or "BTCUSDT")
            interval: Timeframe (1m, 5m, 15m, 1h, 4h, 1d)
            asset_type: Type of asset (crypto, stock, forex)
            
        Returns:
            TechnicalReport with analysis results
        """
        # Fetch market data
        analysis = self.market_tool.get_full_analysis(symbol, interval)
        
        if analysis.get("status") == "error":
            return TechnicalReport(
                signal="NEUTRAL",
                confidence=0.0,
                pattern="ERROR",
                levels={},
                indicators={},
                reasoning=f"Failed to fetch data: {analysis.get('error')}",
                symbol=symbol,
                interval=interval
            )
        
        indicators = analysis.get("indicators", {})
        candles = analysis.get("ohlcv", [])
        
        if not candles:
            return TechnicalReport(
                signal="NEUTRAL",
                confidence=0.0,
                pattern="NO_DATA",
                levels={},
                indicators={},
                reasoning="No candle data available",
                symbol=symbol,
                interval=interval
            )
        
        # Calculate signal
        signal, confidence, pattern = self._generate_signal(indicators)
        
        # Calculate levels
        levels = self._calculate_levels(indicators, candles)
        
        # Determine indicators summary
        ind_summary = {
            "trend": indicators.get("trend", "UNKNOWN"),
            "momentum": self._get_momentum(indicators),
            "volatility": self._get_volatility(indicators)
        }
        
        # Generate reasoning
        reasoning = self._generate_reasoning(indicators, signal, pattern)
        
        return TechnicalReport(
            signal=signal,
            confidence=confidence,
            pattern=pattern,
            levels=levels,
            indicators=ind_summary,
            reasoning=reasoning,
            symbol=symbol,
            interval=interval
        )
    
    def _generate_signal(self, indicators: dict) -> tuple:
        """Generate trading signal based on indicators."""
        score = 0.0
        factors = []
        
        # Trend analysis (SMA)
        sma = indicators.get("sma", {})
        current = indicators.get("current_price", 0)
        
        if sma.get("sma_20") and sma.get("sma_50"):
            if current > sma["sma_20"] > sma["sma_50"]:
                score += 0.3
                factors.append("Above both SMAs (bullish trend)")
            elif current < sma["sma_20"] < sma["sma_50"]:
                score -= 0.3
                factors.append("Below both SMAs (bearish trend)")
            elif current > sma["sma_20"]:
                score += 0.1
                factors.append("Above SMA20 only")
            else:
                score -= 0.1
                factors.append("Below SMA20 only")
        
        # RSI analysis
        rsi = indicators.get("rsi_14", 50)
        if rsi < 30:
            score += 0.25
            factors.append(f"RSI oversold ({rsi})")
        elif rsi > 70:
            score -= 0.25
            factors.append(f"RSI overbought ({rsi})")
        elif 40 < rsi < 60:
            score += 0.1
            factors.append(f"RSI neutral ({rsi})")
        
        # MACD analysis
        macd = indicators.get("macd", {})
        if macd.get("histogram", 0) > 0:
            score += 0.2
            factors.append("MACD histogram positive")
        else:
            score -= 0.2
            factors.append("MACD histogram negative")
        
        # Bollinger Bands
        bb = indicators.get("bollinger_bands", {})
        if bb.get("lower") and current <= bb["lower"]:
            score += 0.25
            factors.append("Price at lower Bollinger Band")
        elif bb.get("upper") and current >= bb["upper"]:
            score -= 0.25
            factors.append("Price at upper Bollinger Band")
        
        # Determine signal
        if score >= 0.5:
            signal = "BUY"
            confidence = min(abs(score) + 0.1, 0.95)
        elif score <= -0.5:
            signal = "SELL"
            confidence = min(abs(score) + 0.1, 0.95)
        else:
            signal = "NEUTRAL"
            confidence = 0.5
        
        pattern = ", ".join(factors[:3]) if factors else "Mixed signals"
        
        return signal, confidence, pattern
    
    def _calculate_levels(self, indicators: dict, candles: list) -> dict:
        """Calculate entry, stop-loss, and take-profit levels."""
        current = indicators.get("current_price", 0)
        atr = indicators.get("atr_14", current * 0.02)
        sr = indicators.get("support_resistance", {})
        
        # Default ATR-based levels
        stop_pct = 1.5 * (atr / current) if current else 0.03
        tp1_pct = 2 * stop_pct
        tp2_pct = 3 * stop_pct
        tp3_pct = 5 * stop_pct
        
        return {
            "entry": f"{current * 0.998:.2f} - {current * 1.002:.2f}",
            "stop_loss": f"{current * (1 - stop_pct):.2f} (-{stop_pct * 100:.1f}%)",
            "take_profit_1": f"{current * (1 + tp1_pct):.2f} (+{tp1_pct * 100:.1f}%)",
            "take_profit_2": f"{current * (1 + tp2_pct):.2f} (+{tp2_pct * 100:.1f}%)",
            "take_profit_3": f"{current * (1 + tp3_pct):.2f} (+{tp3_pct * 100:.1f}%)"
        }
    
    def _get_momentum(self, indicators: dict) -> str:
        """Determine momentum strength."""
        rsi = indicators.get("rsi_14", 50)
        macd_hist = indicators.get("macd", {}).get("histogram", 0)
        
        if rsi > 60 and macd_hist > 0:
            return "STRONG"
        elif rsi < 40 and macd_hist < 0:
            return "WEAK"
        return "NEUTRAL"
    
    def _get_volatility(self, indicators: dict) -> str:
        """Determine volatility level."""
        bb = indicators.get("bollinger_bands", {})
        atr = indicators.get("atr_14", 0)
        current = indicators.get("current_price", 1)
        
        if not bb.get("upper") or not bb.get("lower"):
            return "NORMAL"
        
        bb_width = (bb["upper"] - bb["lower"]) / bb["middle"]
        atr_pct = atr / current
        
        if bb_width > 0.05 or atr_pct > 0.04:
            return "HIGH"
        elif bb_width < 0.02 and atr_pct < 0.015:
            return "LOW"
        return "NORMAL"
    
    def _generate_reasoning(self, indicators: dict, signal: str, pattern: str) -> str:
        """Generate human-readable reasoning."""
        rsi = indicators.get("rsi_14", 50)
        trend = indicators.get("trend", "UNKNOWN")
        
        reasoning = f"Signal: {signal}. "
        reasoning += f"Trend: {trend}. "
        reasoning += f"RSI: {rsi}. "
        reasoning += f"Pattern: {pattern}."
        
        return reasoning
    
    def to_dict(self, report: TechnicalReport) -> dict:
        """Convert report to dictionary."""
        return asdict(report)


# Global instance
_technical_agent = None

def get_technical_analyst() -> TechnicalAnalystAgent:
    global _technical_agent
    if _technical_agent is None:
        _technical_agent = TechnicalAnalystAgent()
    return _technical_agent
