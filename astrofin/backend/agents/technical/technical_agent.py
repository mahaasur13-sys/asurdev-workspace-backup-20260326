"""
Technical Agent — RSI, MACD, Bollinger Bands with RAG Knowledge.
"""
from __future__ import annotations
from datetime import datetime
from typing import Dict, Any, List
from backend.agents.base_agent import BaseAgent, AgentResponse, Signal
from backend.src.rag_knowledge import get_rag_kb, RAGKnowledgeBase

class TechnicalAgent(BaseAgent):
    """Technical analysis agent with RAG knowledge base."""
    
    def __init__(self):
        super().__init__(
            name="TechnicalAgent",
            system_prompt="Technical analyst using RSI, MACD, Bollinger Bands"
        )
        self.rag_kb: RAGKnowledgeBase = None
        
    async def _ensure_rag(self):
        """Lazily initialize RAG."""
        if self.rag_kb is None:
            self.rag_kb = await get_rag_kb()
    
    async def run(self, context: Dict[str, Any]) -> AgentResponse:
        await self._ensure_rag()
        
        symbol = context.get("symbol", "BTCUSDT")
        timeframe = context.get("timeframe", "1d")
        current_price = context.get("current_price", 50000)
        
        # Get market data
        price_data = await self._fetch_ohlcv(symbol, timeframe, 50)
        
        if not price_data:
            return AgentResponse(
                agent_name=self.name,
                signal=Signal.NEUTRAL,
                confidence=0.3,
                reasoning="No market data available",
                metadata={}
            )
        
        # Calculate indicators
        rsi = self._calculate_rsi(price_data)
        macd = self._calculate_macd(price_data)
        bb = self._calculate_bollinger(price_data)
        volume = self._calculate_volume(price_data)
        
        # Get RAG knowledge for context
        rag_chunks = await self.rag_kb.retrieve(
            query=f"RSI MACD Bollinger technical analysis {timeframe}",
            domain="technical",
            top_k=3
        )
        sources = [c.source for c in rag_chunks]
        
        # Determine signal
        signals = []
        confidences = []
        
        # RSI
        if rsi < 30:
            signals.append(Signal.LONG)
            confidences.append(0.7)
        elif rsi > 70:
            signals.append(Signal.SHORT)
            confidences.append(0.7)
        else:
            signals.append(Signal.NEUTRAL)
            confidences.append(0.5)
        
        # MACD
        if macd["histogram"] > 0:
            signals.append(Signal.LONG)
            confidences.append(0.6)
        else:
            signals.append(Signal.SHORT)
            confidences.append(0.6)
        
        # Bollinger
        if current_price < bb["lower"]:
            signals.append(Signal.LONG)
            confidences.append(0.65)
        elif current_price > bb["upper"]:
            signals.append(Signal.SHORT)
            confidences.append(0.65)
        else:
            signals.append(Signal.NEUTRAL)
            confidences.append(0.4)
        
        # Aggregate
        long_count = signals.count(Signal.LONG)
        short_count = signals.count(Signal.SHORT)
        final_signal = Signal.LONG if long_count > short_count else Signal.SHORT if short_count > long_count else Signal.NEUTRAL
        avg_confidence = sum(confidences) / len(confidences)
        
        reasoning = self._build_reasoning(rsi, macd, bb, volume, rag_chunks)
        
        return AgentResponse(
            agent_name=self.name,
            signal=final_signal,
            confidence=avg_confidence,
            reasoning=reasoning,
            sources=sources,
            metadata={
                "rsi": round(rsi, 1),
                "macd": macd,
                "bollinger": bb,
                "volume_trend": volume["trend"]
            }
        )
    
    def _build_reasoning(
        self, 
        rsi: float, 
        macd: Dict, 
        bb: Dict, 
        volume: Dict,
        rag_chunks: List
    ) -> str:
        """Build reasoning with RAG knowledge."""
        parts = [
            f"RSI(14)={rsi:.1f} {'🟢 oversold' if rsi < 30 else '🔴 overbought' if rsi > 70 else '⚪ neutral'}",
            f"MACD {'🟢 bullish' if macd['histogram'] > 0 else '🔴 bearish'} ({macd['histogram']:.2f})",
            f"BB: price {'below' if bb['current'] < bb['lower'] else 'above' if bb['current'] > bb['upper'] else 'inside'} bands",
            f"Vol: {volume['trend']}"
        ]
        
        if rag_chunks:
            parts.append(f"\n📚 RAG: {len(rag_chunks)} sources consulted")
        
        return " | ".join(parts)
    
    async def _fetch_ohlcv(self, symbol: str, timeframe: str, limit: int) -> List:
        """Fetch OHLCV from Binance."""
        try:
            import requests
            interval_map = {"1H": "1h", "4H": "4h", "1D": "1d", "1W": "1w", "SWING": "1d"}
            interval = interval_map.get(timeframe, "1d")
            url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
            resp = requests.get(url, timeout=10)
            data = resp.json()
            return [[float(x[4]), float(x[5])] for x in data]
        except Exception:
            return []
    
    def _calculate_rsi(self, data: List, period: int = 14) -> float:
        if len(data) < period + 1:
            return 50.0
        closes = [d[0] for d in data]
        deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
        gains = [d if d > 0 else 0 for d in deltas[-period:]]
        losses = [-d if d < 0 else 0 for d in deltas[-period:]]
        avg_gain = sum(gains) / period
        avg_loss = sum(losses) / period
        if avg_loss == 0:
            return 100.0
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))
    
    def _calculate_macd(self, data: List, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict:
        if len(data) < slow + signal:
            return {"macd": 0, "signal": 0, "histogram": 0}
        closes = [d[0] for d in data]
        
        def ema(values: List, period: int) -> float:
            if len(values) < period:
                return values[-1] if values else 0
            multiplier = 2 / (period + 1)
            ema_val = sum(values[:period]) / period
            for price in values[period:]:
                ema_val = (price - ema_val) * multiplier + ema_val
            return ema_val
        
        ema_fast = ema(closes, fast)
        ema_slow = ema(closes, slow)
        macd_line = ema_fast - ema_slow
        signal_line = macd_line * 0.9
        return {"macd": macd_line, "signal": signal_line, "histogram": macd_line - signal_line}
    
    def _calculate_bollinger(self, data: List, period: int = 20, std_dev: int = 2) -> Dict:
        if len(data) < period:
            return {"upper": 0, "middle": 0, "lower": 0, "current": 0}
        closes = [d[0] for d in data][-period:]
        middle = sum(closes) / period
        variance = sum((c - middle) ** 2 for c in closes) / period
        std = variance ** 0.5
        return {
            "upper": middle + std_dev * std,
            "middle": middle,
            "lower": middle - std_dev * std,
            "current": closes[-1]
        }
    
    def _calculate_volume(self, data: List) -> Dict:
        if len(data) < 20:
            return {"trend": "insufficient data"}
        volumes = [d[1] for d in data[-20:]]
        recent = sum(volumes[-5:]) / 5
        older = sum(volumes[-20:-5]) / 15
        if recent > older * 1.2:
            trend = "increasing 🟢"
        elif recent < older * 0.8:
            trend = "decreasing 🔴"
        else:
            trend = "stable ⚪"
        return {"trend": trend, "recent_avg": recent, "older_avg": older}


# Convenience function
async def run_technical_agent(context: Dict[str, Any]) -> Dict:
    """Run technical analysis."""
    agent = TechnicalAgent()
    result = await agent.run(context)
    return {"technical_signal": result.to_dict()}
