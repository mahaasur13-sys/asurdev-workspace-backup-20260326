"""
HoraryAgent — Horary astrology agent for asurdev Sentinel.
Integrates with existing agent framework.
"""

import asyncio
from datetime import datetime
from typing import Dict, Any, Optional
from agents._impl.base_agent import BaseAgent
from agents.types import AgentResponse

from astrology.horary import (
    HoraryChart, QuestionParser, LillyJudicator,
    HoraryLLM, Verdict
)


class HoraryAgent(BaseAgent):
    """
    Horary Astrology agent based on William Lilly's Christian Astrology.
    
    Takes a financial question and returns a verdict based on:
    1. Chart construction (planetary positions, houses)
    2. Significator analysis (quesitor, thing, counsel)
    3. Lilly's judgment rules (dignities, aspects, accidental strength)
    4. Optional LLM interpretation for detailed analysis
    
    Usage:
        agent = HoraryAgent()
        response = await agent.analyze({"question": "Should I buy BTC now?"})
    """
    
    def __init__(
        self,
        lat: float = 28.6139,
        lon: float = 77.2090,
        use_llm: bool = False,  # Set True if Ollama is running
        model: str = None,
        **kwargs
    ):
        name = kwargs.pop("name", "Horary")
        system_prompt = kwargs.pop(
            "system_prompt",
            "You are a horary astrologer using William Lilly's Christian Astrology. "
            "Analyze financial questions using classical techniques."
        )
        
        super().__init__(
            name=name,
            system_prompt=system_prompt,
            **kwargs
        )
        
        self.lat = lat
        self.lon = lon
        self.use_llm = use_llm
        self.llm = HoraryLLM(model=model) if use_llm else None
    
    async def analyze(self, context: Dict[str, Any]) -> AgentResponse:
        """
        Analyze a horary question.
        
        Context can contain:
        - question: The question to analyze (str)
        - datetime: Optional datetime (defaults to now)
        - lat, lon: Optional location (defaults to init values)
        - use_llm: Override LLM usage
        
        Returns AgentResponse with verdict, confidence, and details.
        """
        # Extract question
        question = context.get("question", "")
        if not question:
            return AgentResponse(
                agent_name=self.name,
                signal="NEUTRAL",
                confidence=0,
                summary="No question provided",
                details={"error": "Question is required"}
            )
        
        # Extract parameters
        dt = context.get("datetime")
        if dt is None:
            dt = datetime.now()
        elif isinstance(dt, str):
            dt = datetime.fromisoformat(dt)
        
        lat = context.get("lat", self.lat)
        lon = context.get("lon", self.lon)
        use_llm = context.get("use_llm", self.use_llm)
        
        try:
            # Build chart
            chart = HoraryChart(
                question=question,
                dt=dt,
                lat=lat,
                lon=lon
            )
            
            # Parse question
            parser = QuestionParser().parse(question)
            
            # Judge
            judicator = LillyJudicator(chart, parser)
            judgement = judicator.judge()
            
            # Generate interpretation
            if use_llm and self.llm:
                interpretation = self.llm.interpret(chart, parser, judgement)
            else:
                llm_fake = HoraryLLM()
                interpretation = llm_fake._generate_fallback(chart, parser, judgement)
            
            # Map verdict to signal
            verdict_to_signal = {
                Verdict.STRONG_YES: "STRONG_BUY",
                Verdict.YES: "BUY",
                Verdict.NEUTRAL: "NEUTRAL",
                Verdict.NO: "SELL",
                Verdict.STRONG_NO: "STRONG_SELL",
                Verdict.ASK_LATER: "HOLD",
            }
            signal = verdict_to_signal.get(judgement.verdict, "NEUTRAL")
            
            return AgentResponse(
                agent_name=self.name,
                signal=signal,
                confidence=judgement.confidence,
                summary=f"{judgement.verdict.value} ({judgement.confidence}% confidence) - {parser.symbol}",
                details={
                    "question": question,
                    "symbol": parser.symbol,
                    "action": parser.action,
                    "asset_class": parser.asset_class,
                    "verdict": judgement.verdict.value,
                    "confidence": judgement.confidence,
                    "reasons_for": judgement.reasons_for,
                    "reasons_against": judgement.reasons_against,
                    "key_aspects": judgement.key_aspects,
                    "dignities": judgement.dignities,
                    "recommendation": judgement.recommendation,
                    "interpretation": interpretation,
                    "chart": chart.describe(),
                    "use_llm": use_llm,
                }
            )
            
        except Exception as e:
            return AgentResponse(
                agent_name=self.name,
                signal="ERROR",
                confidence=0,
                summary=str(e),
                details={"error": str(e), "question": question}
            )
    
    async def analyze_impl(self, prompt: str) -> str:
        """Internal implementation for LLM calls."""
        return "Horary analysis"


# Convenience function
async def ask_horary(
    question: str,
    lat: float = 28.6139,
    lon: float = 77.2090,
    use_llm: bool = False
) -> Dict[str, Any]:
    """
    Ask a horary question and get a response.
    
    Args:
        question: The financial question
        lat, lon: Location for chart
        use_llm: Use LLM for detailed interpretation
    
    Returns:
        Dict with verdict, interpretation, and chart data
    """
    agent = HoraryAgent(lat=lat, lon=lon, use_llm=use_llm)
    response = await agent.analyze({"question": question})
    return response.details
