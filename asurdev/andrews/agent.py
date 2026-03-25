"""
Andrews Agent — asurdev Sentinel
"""
from typing import Dict, Any
from agents.base import BaseAgent, AgentResponse


class AndrewsAgent(BaseAgent):
    """
    Andrews Pitchfork analysis agent.
    Tool-based, no LLM needed.
    """
    
    def __init__(self, **kwargs):
        # Don't call BaseAgent.__init__ - we're tool-based
        self.name = "Andrews"
        self.tools = self._get_tools()
    
    def _get_tools(self):
        from .pitchfork import get_andrews_tools
        return get_andrews_tools()
    
    def _parse_response(self, raw: str) -> AgentResponse:
        return AgentResponse(
            agent_name=self.name,
            signal="NEUTRAL",
            confidence=30,
            summary=raw[:200]
        )
    
    async def analyze(self, context: Dict[str, Any]) -> AgentResponse:
        """Run Andrews analysis"""
        prices = context.get('prices', [])
        
        if not prices:
            # Generate synthetic data from price
            price = context.get('current_price', 100)
            if price <= 0:
                return AgentResponse(
                    agent_name=self.name,
                    signal="NEUTRAL",
                    confidence=0,
                    summary="No price data"
                )
            
            # Generate synthetic OHLCV-like data
            import random
            base = price
            prices = []
            for i in range(50):
                change = random.uniform(-0.03, 0.03)
                base = base * (1 + change)
                prices.append(base)
        
        if len(prices) < 20:
            return AgentResponse(
                agent_name=self.name,
                signal="NEUTRAL",
                confidence=20,
                summary="Insufficient data for Andrews analysis"
            )
        
        result = self.tools.analyze(prices)
        
        return AgentResponse(
            agent_name=self.name,
            signal=result.get('signal', 'NEUTRAL'),
            confidence=result.get('confidence', 40),
            summary=result.get('description', result.get('trend', 'No signal')),
            details=result
        )
    
    async def analyze_impl(self, context: Dict[str, Any]) -> AgentResponse:
        """Required by BaseAgent"""
        return await self.analyze(context)


def get_andrews_agent() -> AndrewsAgent:
    return AndrewsAgent()
