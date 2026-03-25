"""
Horary Astrology Module for asurdev Sentinel
=============================================

Implements William Lilly's Christian Astrology (1647) for financial decisions.

Classes:
    - HoraryChart: Build and represent a horary chart
    - QuestionParser: Parse question and determine significators
    - LillyJudicator: Render verdict based on Lilly's rules
    - SignificatorRegistry: Maps question types to significators
    - HoraryLLM: LLM integration for detailed interpretations

Usage:
    from astrology.horary import HoraryChart, QuestionParser, LillyJudicator
    
    chart = HoraryChart(
        question="Should I buy BTC now?",
        dt=datetime.now(),
        lat=28.6139,
        lon=77.2090
    )
    parser = QuestionParser().parse("Should I buy BTC now?")
    judicator = LillyJudicator(chart, parser)
    verdict = judicator.judge()
    print(verdict.summary)
"""

from .chart import HoraryChart, PlanetPosition, Significator, SIGNS
from .parser import QuestionParser, QuestionType, parse_question
from .judicator import LillyJudicator, Judgement, Verdict
from .significators import SignificatorRegistry, SignificatorDef, SignificatorCategory
from .llm import HoraryLLM, interpret_question

__all__ = [
    # Core chart
    "HoraryChart",
    "PlanetPosition",
    "Significator",
    "SIGNS",
    # Parser
    "QuestionParser",
    "QuestionType",
    "parse_question",
    # Judicator
    "LillyJudicator",
    "Judgement",
    "Verdict",
    # Significators
    "SignificatorRegistry",
    "SignificatorDef",
    "SignificatorCategory",
    # LLM
    "HoraryLLM",
    "interpret_question",
]
