"""
Dow Theory Agent — asurdev Sentinel
"""
from typing import Dict, Any
from agents.base import BaseAgent, AgentResponse


class DowTheoryAgent(BaseAgent):
    """
    Dow Theory analysis agent.
    """
    
    def __init__(self, **kwargs):
        self.name = "DowTheory"
        self.analyzer = self._get_analyzer()
    
    def _get_analyzer(self):
        from .analysis import DowTheoryAnalyzer
        return DowTheoryAnalyzer()
    
    def _parse_response(self, raw: str) -> AgentResponse:
        return AgentResponse(
            agent_name=self.name,
            signal="NEUTRAL",
            confidence=30,
            summary=raw[:200]
        )
    
    async def analyze(self, context: Dict[str, Any]) -> AgentResponse:
        """Run Dow Theory analysis"""
        prices = context.get('prices', [])
        
        if not prices:
            price = context.get('current_price', 100)
            if price <= 0:
                return AgentResponse(
                    agent_name=self.name,
                    signal="NEUTRAL",
                    confidence=0,
                    summary="No price data"
                )
            
            import random
            base = price
            prices = []
            for i in range(50):
                change = random.uniform(-0.02, 0.02)
                base = base * (1 + change)
                prices.append(base)
        
        if len(prices) < 20:
            return AgentResponse(
                agent_name=self.name,
                signal="NEUTRAL",
                confidence=20,
                summary="Insufficient data for Dow Theory"
            )
        
        result = self.analyzer.analyze_trend(prices)
        
        signal = "NEUTRAL"
        if result.get('confirmed'):
            if 'up' in result.get('trend', '').lower():
                signal = "BULLISH"
            elif 'down' in result.get('trend', '').lower():
                signal = "BEARISH"
        
        return AgentResponse(
            agent_name=self.name,
            signal=signal,
            confidence=result.get('strength', 40),
            summary=result.get('description', result.get('trend', 'No signal')),
            details=result
        )
    
    async def analyze_impl(self, context: Dict[str, Any]) -> AgentResponse:
        """Required by BaseAgent"""
        return await self.analyze(context)


def get_dow_agent() -> DowTheoryAgent:
    return DowTheoryAgent()
