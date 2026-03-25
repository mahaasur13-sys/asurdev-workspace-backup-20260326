"""
ResponseFormatterAgent — финальное форматирование ответа для пользователя.
"""
from __future__ import annotations
from datetime import datetime
from typing import Dict, Any, List
from backend.agents.base_agent import BaseAgent, AgentResponse, Signal
from backend.src.swiss_ephemeris import swiss_ephemeris

class ResponseFormatterAgent(BaseAgent):
    """ResponseFormatterAgent — форматирование ответа. Вес: 0.02 (utility)"""
    
    def __init__(self):
        super().__init__(
            name="ResponseFormatterAgent",
            system_prompt="Response Formatter"
        )

    async def run(self, context: Dict[str, Any]) -> AgentResponse:
        all_responses = context.get("all_responses", [])
        symbol = context.get("symbol", "BTC")
        current_price = context.get("current_price", 50000)
        
        if not all_responses:
            return AgentResponse(
                agent_name=self.name,
                signal=Signal.NEUTRAL,
                confidence=0.3,
                reasoning="No responses to format",
            )
        
        # Format the final report
        formatted = self._format_report(all_responses, symbol, current_price)
        
        return AgentResponse(
            agent_name=self.name,
            signal=Signal.NEUTRAL,
            confidence=0.99,  # This is just formatting, not analysis
            reasoning="Response formatted successfully",
            sources=[],
            metadata={"formatted_report": formatted},
        )

    def _format_report(self, responses: List[AgentResponse], symbol: str, price: float) -> str:
        lines = [
            f"╔══════════════════════════════════════════════════════════════╗",
            f"║              ASTROFIN SENTINEL — {symbol:^10}                  ║",
            f"╠══════════════════════════════════════════════════════════════╣",
            f"║  Price: ${price:,.2f}  |  Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC",
            f"╠══════════════════════════════════════════════════════════════╣",
        ]
        
        for resp in responses:
            bar = "█" * int(resp.confidence * 10) + "░" * (10 - int(resp.confidence * 10))
            lines.append(f"║  {resp.agent_name:20s} [{bar}] {resp.signal.value:6s} {resp.confidence:.0%}")
        
        lines.append(f"╚══════════════════════════════════════════════════════════════╝")
        
        return "\n".join(lines)
