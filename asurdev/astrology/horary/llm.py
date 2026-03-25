"""
HoraryLLM — LLM integration for complex horary interpretations.
Uses local Ollama or OpenAI for detailed chart analysis.
"""

import os
import json
from typing import Dict, Any, Optional, List
from datetime import datetime

from .chart import HoraryChart, SIGNS
from .parser import QuestionParser
from .judicator import Judgement, LillyJudicator


LLM_PROMPT_TEMPLATE = """You are an expert astrologer specializing in William Lilly's Christian Astrology (1647).

Given the following horary chart analysis and question, provide a detailed interpretation.

QUESTION: {question}
QUESTION TYPE: {question_type}
SYMBOL: {symbol}
ASSET CLASS: {asset_class}

CHART DATA:
- Time: {datetime}
- Day/Night: {is_day}
- Ascendant: {ascendant}

PLANETARY POSITIONS:
{positions}

HOUSE CUSPS:
{cusps}

SIGNIFICATORS:
{significators}

JUDGEMENT:
- Verdict: {verdict}
- Confidence: {confidence}%
- Reasons for: {reasons_for}
- Reasons against: {reasons_against}

Provide a detailed interpretation (3-5 paragraphs) that:
1. Explains the chart dynamics in plain language
2. Integrates the traditional Lilly judgment with modern context
3. Gives specific guidance for the financial decision
4. Notes any warnings or cautionary factors

End with a clear recommendation (BUY/SELL/HOLD/WAIT) with reasoning.
"""


class HoraryLLM:
    """
    LLM integration for horary astrology.
    
    Provides detailed natural language interpretations of charts
    using local Ollama models (qwen3-coder recommended).
    """
    
    def __init__(
        self,
        model: str = None,
        base_url: str = "http://localhost:11434",
        temperature: float = 0.3,
    ):
        self.model = model or os.environ.get(
            "asurdev_MODEL", "qwen3-coder:30b-a3b"
        )
        self.base_url = base_url
        self.temperature = temperature
        self.llm = None
        self._init_llm()
    
    def _init_llm(self):
        """Initialize LLM connection."""
        try:
            from langchain_ollama import ChatOllama
            self.llm = ChatOllama(
                model=self.model,
                base_url=self.base_url,
                temperature=self.temperature,
                timeout=120,
            )
        except ImportError:
            try:
                from langchain_openai import ChatOpenAI
                api_key = os.environ.get("asurdev_OPENAI_API_KEY") or \
                          os.environ.get("OPENAI_API_KEY")
                if api_key:
                    self.llm = ChatOpenAI(
                        model="gpt-4o-mini",
                        api_key=api_key,
                        temperature=self.temperature,
                    )
            except Exception:
                pass
    
    def interpret(
        self,
        chart: HoraryChart,
        parser: QuestionParser,
        judgement: Judgement,
    ) -> str:
        """
        Generate detailed interpretation using LLM.
        
        Returns a natural language interpretation of the chart.
        Falls back to template if LLM is not available.
        """
        if self.llm:
            return self._generate_with_llm(chart, parser, judgement)
        else:
            return self._generate_fallback(chart, parser, judgement)
    
    def _generate_with_llm(
        self,
        chart: HoraryChart,
        parser: QuestionParser,
        judgement: Judgement,
    ) -> str:
        """Generate interpretation using LLM."""
        prompt = self._build_prompt(chart, parser, judgement)
        
        try:
            from langchain_core.messages import HumanMessage
            response = self.llm.invoke([HumanMessage(content=prompt)])
            return response.content
        except Exception as e:
            return f"LLM error: {e}\n\n" + self._generate_fallback(chart, parser, judgement)
    
    def _build_prompt(
        self,
        chart: HoraryChart,
        parser: QuestionParser,
        judgement: Judgement,
    ) -> str:
        """Build the prompt for the LLM."""
        # Format positions
        positions_text = []
        for name, pos in chart.positions.items():
            house = chart.get_planet_in_house(name)
            positions_text.append(
                f"- {name}: {pos.sign} {pos.degree:.1f} deg (House {house})"
            )
        
        # Format cusps
        cusps_text = []
        for i, cusp in enumerate(chart.cusps):
            sign = SIGNS[int(cusp // 30)]
            cusps_text.append(f"- House {i+1}: {cusp:.1f} deg {sign}")
        
        # Format significators
        try:
            quesitor = chart.get_significator(parser.mapping.quesitor_planet)
            thing = chart.get_significator(parser.get_asset_significator(
                parser.symbol, parser.asset_class
            ))
            significators_text = [
                f"- Quesitor ({parser.mapping.quesitor_planet}): "
                f"House {quesitor.house}, Dignity: {quesitor.dignity_score}, "
                f"Total Score: {quesitor.total_score}",
                f"- Thing ({thing.planet.name}): "
                f"House {thing.house}, Dignity: {thing.dignity_score}, "
                f"Total Score: {thing.total_score}",
            ]
        except (ValueError, AttributeError):
            significators_text = ["Significator analysis not available"]
        
        return LLM_PROMPT_TEMPLATE.format(
            question=parser.raw_question,
            question_type=parser.question_type.value,
            symbol=parser.symbol,
            asset_class=parser.asset_class,
            datetime=chart.datetime.isoformat(),
            is_day="Day" if chart.is_day else "Night",
            ascendant=f"{SIGNS[int(chart.asc // 30)]} {chart.asc % 30:.1f} deg",
            positions="\n".join(positions_text),
            cusps="\n".join(cusps_text),
            significators="\n".join(significators_text),
            verdict=judgement.verdict.value,
            confidence=judgement.confidence,
            reasons_for="\n".join(f"- {r}" for r in judgement.reasons_for),
            reasons_against="\n".join(f"- {r}" for r in judgement.reasons_against),
        )
    
    def _generate_fallback(
        self,
        chart: HoraryChart,
        parser: QuestionParser,
        judgement: Judgement,
    ) -> str:
        """Generate a basic interpretation without LLM."""
        lines = [
            "=" * 60,
            "HORARY CHART INTERPRETATION (Template)",
            "=" * 60,
            "",
            f"Question: {parser.raw_question}",
            f"Symbol: {parser.symbol}",
            f"Time: {chart.datetime.strftime('%Y-%m-%d %H:%M')}",
            "",
            "-" * 40,
            "CHART SUMMARY",
            "-" * 40,
            f"Day/Night: {'Day' if chart.is_day else 'Night'} chart",
            f"Ascendant: {SIGNS[int(chart.asc // 30)]} {chart.asc % 30:.1f} deg",
            "",
            "PLANETARY POSITIONS:",
        ]
        
        for name, pos in chart.positions.items():
            house = chart.get_planet_in_house(name)
            lines.append(f"  {name}: {pos.sign} {pos.degree:.1f} deg in House {house}")
        
        lines.extend([
            "",
            "-" * 40,
            "JUDGEMENT",
            "-" * 40,
            f"Verdict: {judgement.verdict.value}",
            f"Confidence: {judgement.confidence}%",
            "",
            "REASONS FOR:",
        ])
        for r in judgement.reasons_for:
            lines.append(f"  + {r}")
        
        lines.append("")
        lines.append("REASONS AGAINST:")
        for r in judgement.reasons_against:
            lines.append(f"  - {r}")
        
        lines.extend([
            "",
            "-" * 40,
            "RECOMMENDATION",
            "-" * 40,
            judgement.recommendation,
            "",
            "=" * 60,
        ])
        
        return "\n".join(lines)
    
    def interpret_batch(
        self,
        questions: List[str],
        lat: float = 28.6139,
        lon: float = 77.2090,
    ) -> List[Dict[str, Any]]:
        """
        Interpret multiple questions at once.
        
        Returns list of dicts with chart, parser, judgement, and interpretation.
        """
        results = []
        
        for question in questions:
            dt = datetime.now()
            chart = HoraryChart(question, dt, lat, lon)
            parser = QuestionParser().parse(question)
            judicator = LillyJudicator(chart, parser)
            judgement = judicator.judge()
            interpretation = self.interpret(chart, parser, judgement)
            
            results.append({
                "question": question,
                "chart": chart,
                "parser": parser,
                "judgement": judgement,
                "interpretation": interpretation,
            })
        
        return results


async def interpret_question(
    question: str,
    lat: float = 28.6139,
    lon: float = 77.2090,
    use_llm: bool = True,
) -> Dict[str, Any]:
    """
    Convenience function to interpret a single question.
    
    Returns dict with:
    - question: the original question
    - chart_data: chart description
    - verdict: the judgement verdict
    - interpretation: detailed natural language interpretation
    """
    dt = datetime.now()
    
    # Build chart
    chart = HoraryChart(question, dt, lat, lon)
    
    # Parse question
    parser = QuestionParser().parse(question)
    
    # Judge
    judicator = LillyJudicator(chart, parser)
    judgement = judicator.judge()
    
    # Interpret
    llm = HoraryLLM() if use_llm else None
    if llm:
        interpretation = llm.interpret(chart, parser, judgement)
    else:
        llm_fake = HoraryLLM()
        interpretation = llm_fake._generate_fallback(chart, parser, judgement)
    
    return {
        "question": question,
        "symbol": parser.symbol,
        "action": parser.action,
        "asset_class": parser.asset_class,
        "chart": chart.describe(),
        "verdict": judgement.to_dict(),
        "interpretation": interpretation,
        "timestamp": dt.isoformat(),
    }
