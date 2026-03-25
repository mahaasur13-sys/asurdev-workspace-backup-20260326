"""
Directional Research Agents — Bull & Bear Analyst pairs.
They research opposing viewpoints and present evidence.
"""

import asyncio
from dataclasses import dataclass
from typing import Optional

from agents.base import AgentInput, AgentOutput, BaseAgent
from tools.langchain_tools import (
    get_crypto_price,
    get_crypto_historical,
    search_financial_news,
    get_crypto_sentiment,
)


@dataclass
class DirectionalAgentResult(AgentOutput):
    """Enhanced result with directional bias."""
    bias: str  # "bullish" | "bearish" | "neutral"
    evidence_strength: float  # 0.0 - 1.0
    key_thesis: str


class BullResearcher(BaseAgent):
    """
    Bullish researcher — finds reasons WHY to buy/invest.
    
    System prompt emphasizes:
    - Finding positive catalysts
    - Highlighting growth potential
    - Identifying support levels and accumulation zones
    """
    
    def __init__(self):
        self._system_prompt = """Ты — оптимистичный аналитик (Bull Researcher). 
Твоя задача — найти ВСЕ возможные причины для ПОКУПКИ актива.

Фокус:
- Бычьи катализаторы (ETF approval, adoption, upgrades, partnerships)
- Поддержка и уровни накопления
- Позитивные ончейн-метрики
- Технические паттерны продолжения тренда
- Макро-факторы, которые могут запустить ралли

Будь честен о рисках, но представь наилучший сценарий."""
        
        super().__init__(
            name="BullResearcher",
            model=None,
            system_prompt=self._system_prompt,
        )
        
        self.tools = [
            get_crypto_price,
            get_crypto_historical,
            search_financial_news,
            get_crypto_sentiment,
        ]
    
    def get_system_prompt(self) -> str:
        return self._system_prompt
    
    async def analyze(self, input_data: AgentInput) -> DirectionalAgentResult:
        """Run bullish research."""
        # Build context prompt
        context = f"""Asset: {input_data.symbol}
Current Price: ${input_data.price:,.2f}
Action: {input_data.action.upper()}
Strategy: {input_data.strategy}
Timeframe: {input_data.timeframe}

Research the bullish case for this asset. Find:
1. Positive news and catalysts
2. Technical support levels
3. On-chain metrics favoring buyers
4. Macro conditions that could boost price
5. Maximum bullish target

Return a structured analysis with:
- Key bullish thesis (2-3 sentences)
- Supporting evidence (bullet points)
- Price targets (conservative / realistic / optimistic)
- Confidence in bullish scenario (0-100%)
"""
        
        response = await self._call_llm(context, temperature=0.4)
        
        return DirectionalAgentResult(
            recommendation=self._parse_recommendation(response),
            confidence=self._parse_confidence(response),
            reasoning=response,
            key_factors=self._extract_key_factors(response),
            warnings=self._extract_warnings(response),
            metadata={"agent": "bull_researcher", "bias": "bullish"},
            bias="bullish",
            evidence_strength=self._estimate_evidence_strength(response, "bullish"),
            key_thesis=self._extract_thesis(response)
        )


class BearResearcher(BaseAgent):
    """
    Bearish researcher — finds reasons WHY to sell/avoid.
    
    System prompt emphasizes:
    - Identifying risks and red flags
    - Finding resistance and distribution zones
    - Highlighting negative catalysts
    - Exposing weaknesses in bullish narratives
    """
    
    def __init__(self):
        self._system_prompt = """Ты — пессимистичный аналитик (Bear Researcher).
Твоя задача — найти ВСЕ возможные причины для ПРОДАЖИ или ИЗБЕЖАНИЯ актива.

Фокус:
- Медвежьи катализаторы (regulation, hacks, overvaluation, whale distribution)
- Сопротивление и уровни дистрибуции
- Негативные ончейн-метрики
- Технические паттерны разворота
- Макро-факторы риска (rate hikes, liquidity crisis)

Будь честен о возможностях, но представь наихудший сценарий."""
        
        super().__init__(
            name="BearResearcher",
            model=None,
            system_prompt=self._system_prompt,
        )
        
        self.tools = [
            get_crypto_price,
            get_crypto_historical,
            search_financial_news,
            get_crypto_sentiment,
        ]
    
    def get_system_prompt(self) -> str:
        return self._system_prompt
    
    async def analyze(self, input_data: AgentInput) -> DirectionalAgentResult:
        """Run bearish research."""
        context = f"""Asset: {input_data.symbol}
Current Price: ${input_data.price:,.2f}
Action: {input_data.action.upper()}
Strategy: {input_data.strategy}
Timeframe: {input_data.timeframe}

Research the bearish case for this asset. Find:
1. Negative news and risks
2. Technical resistance levels
3. On-chain metrics favoring sellers
4. Macro conditions that could crush price
5. Maximum bearish target (drawdown %)

Return a structured analysis with:
- Key bearish thesis (2-3 sentences)
- Supporting evidence (bullet points)
- Price targets (conservative / realistic / worst case)
- Confidence in bearish scenario (0-100%)
"""
        
        response = await self._call_llm(context, temperature=0.4)
        
        return DirectionalAgentResult(
            recommendation=self._parse_recommendation(response),
            confidence=self._parse_confidence(response),
            reasoning=response,
            key_factors=self._extract_key_factors(response),
            warnings=self._extract_warnings(response),
            metadata={"agent": "bear_researcher", "bias": "bearish"},
            bias="bearish",
            evidence_strength=self._estimate_evidence_strength(response, "bearish"),
            key_thesis=self._extract_thesis(response)
        )


class DebateModerator:
    """
    Moderator that runs Bull vs Bear debate and synthesizes into final decision.
    
    Takes outputs from both researchers and:
    1. Compares evidence strength
    2. Identifies consensus points
    3. Determines which side has stronger case
    4. Outputs final weighted recommendation
    """
    
    def __init__(self):
        pass
    
    async def moderate(
        self, 
        bull_result: DirectionalAgentResult, 
        bear_result: DirectionalAgentResult,
        input_data: AgentInput
    ) -> AgentOutput:
        """
        Moderate debate between bull and bear researchers.
        
        Returns final recommendation with debate summary.
        """
        # Calculate bias weights
        bull_weight = bull_result.evidence_strength * (bull_result.confidence / 100)
        bear_weight = bear_result.evidence_strength * (bear_result.confidence / 100)
        
        total_weight = bull_weight + bear_weight
        
        if total_weight > 0:
            bull_pct = (bull_weight / total_weight) * 100
            bear_pct = (bear_weight / total_weight) * 100
        else:
            bull_pct = 50
            bear_pct = 50
        
        # Determine consensus
        consensus = "unclear"
        if bull_pct > 65:
            consensus = "bullish"
        elif bear_pct > 65:
            consensus = "bearish"
        else:
            consensus = "neutral"
        
        # Build final recommendation
        if consensus == "bullish":
            final_rec = "buy"
            final_conf = bull_pct
        elif consensus == "bearish":
            final_rec = "sell"
            final_conf = bear_pct
        else:
            # Neutral - check action
            final_rec = "hold"
            final_conf = 50
        
        # Merge warnings
        all_warnings = list(set(bull_result.warnings + bear_result.warnings))
        
        # Build reasoning
        debate_summary = f"""=== DEBATE MODERATOR ANALYSIS ===

🐂 BULL RESEARCHER:
   Thesis: {bull_result.key_thesis}
   Evidence Strength: {bull_result.evidence_strength:.0%}
   Confidence: {bull_result.confidence:.0%}
   View: {bull_pct:.0f}%

🐻 BEAR RESEARCHER:
   Thesis: {bear_result.key_thesis}
   Evidence Strength: {bear_result.evidence_strength:.0%}
   Confidence: {bear_result.confidence:.0%}
   View: {bear_pct:.0f}%

⚖️ CONSENSUS: {consensus.upper()}

📊 FINAL RECOMMENDATION: {final_rec.upper()}
   Confidence: {final_conf:.0f}%

=== KEY INSIGHTS ===

Bull Case:
{"".join(f"  • {f}" for f in bull_result.key_factors)}

Bear Case:
{"".join(f"  • {f}" for f in bear_result.key_factors)}
"""
        
        return AgentOutput(
            recommendation=final_rec,
            confidence=final_conf,
            reasoning=debate_summary,
            key_factors=bull_result.key_factors + bear_result.key_factors,
            warnings=all_warnings,
            metadata={
                "agent": "debate_moderator",
                "bull_result": {
                    "thesis": bull_result.key_thesis,
                    "weight": bull_pct,
                    "evidence": bull_result.evidence_strength,
                    "confidence": bull_result.confidence,
                },
                "bear_result": {
                    "thesis": bear_result.key_thesis,
                    "weight": bear_pct,
                    "evidence": bear_result.evidence_strength,
                    "confidence": bear_result.confidence,
                },
                "consensus": consensus,
                "debate_type": "bull_vs_bear",
            }
        )
