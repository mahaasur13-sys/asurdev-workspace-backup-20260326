"""
Test script for Horary Astrology module.
Run: python test_horary.py
"""

import asyncio
from datetime import datetime
from astrology.horary import (
    HoraryChart, QuestionParser, LillyJudicator,
    HoraryLLM, interpret_question, Verdict
)


def test_basic_chart():
    """Test basic chart creation and parsing."""
    print("\n" + "=" * 60)
    print("TEST 1: Basic Chart Creation")
    print("=" * 60)
    
    question = "Should I buy BTC now?"
    dt = datetime(2026, 3, 22, 12, 0)
    
    chart = HoraryChart(question, dt, lat=28.6139, lon=77.2090)
    
    print(f"Question: {chart.question}")
    print(f"DateTime: {chart.datetime}")
    print(f"Is Day: {chart.is_day}")
    print(f"ASC: {chart.asc:.1f} deg {chart.positions.get('Sun', 'N/A')}")
    print()
    print("Planetary Positions:")
    for name, pos in chart.positions.items():
        house = chart.get_planet_in_house(name)
        print(f"  {name}: {pos.sign} {pos.degree:.1f} deg -> House {house}")
    
    print()
    print("Houses (Whole Sign):")
    for i, cusp in enumerate(chart.cusps):
        from astrology.horary.chart import SIGNS
        sign = SIGNS[int(cusp // 30)]
        print(f"  House {i+1}: {cusp:.1f} deg {sign}")


def test_question_parser():
    """Test question parsing."""
    print("\n" + "=" * 60)
    print("TEST 2: Question Parser")
    print("=" * 60)
    
    questions = [
        "Should I buy BTC now?",
        "Should I sell AAPL?",
        "What will happen to ETH?",
        "Should I hold my position?",
        "Is this a good time to invest in gold?",
    ]
    
    for q in questions:
        parser = QuestionParser().parse(q)
        print(f"\nQ: {q}")
        print(f"  Type: {parser.question_type.value}")
        print(f"  Action: {parser.action}")
        print(f"  Symbol: {parser.symbol}")
        print(f"  Asset Class: {parser.asset_class}")


def test_significators():
    """Test significator extraction."""
    print("\n" + "=" * 60)
    print("TEST 3: Significators")
    print("=" * 60)
    
    question = "Should I buy BTC now?"
    dt = datetime(2026, 3, 22, 12, 0)
    
    chart = HoraryChart(question, dt)
    parser = QuestionParser().parse(question)
    
    try:
        quesitor = chart.get_significator(parser.mapping.quesitor_planet)
        print(f"Quesitor ({quesitor.planet.name}):")
        print(f"  House: {quesitor.house}")
        print(f"  Dignity Score: {quesitor.dignity_score}")
        print(f"  Accidental Score: {quesitor.accidental_score}")
        print(f"  Total Score: {quesitor.total_score}")
        print(f"  Aspects: {quesitor.aspects_to_other}")
    except Exception as e:
        print(f"Quesitor error: {e}")
    
    try:
        asset_planet = parser.get_asset_significator(parser.symbol, parser.asset_class)
        thing = chart.get_significator(asset_planet)
        print(f"\nThing ({thing.planet.name}):")
        print(f"  House: {thing.house}")
        print(f"  Dignity Score: {thing.dignity_score}")
        print(f"  Total Score: {thing.total_score}")
    except Exception as e:
        print(f"Thing error: {e}")


def test_judicator():
    """Test the judicator."""
    print("\n" + "=" * 60)
    print("TEST 4: Lilly Judicator")
    print("=" * 60)
    
    question = "Should I buy BTC now?"
    dt = datetime(2026, 3, 22, 12, 0)
    
    chart = HoraryChart(question, dt)
    parser = QuestionParser().parse(question)
    judicator = LillyJudicator(chart, parser)
    judgement = judicator.judge()
    
    print(f"Question: {question}")
    print(f"\nVerdict: {judgement.verdict.value}")
    print(f"Confidence: {judgement.confidence}%")
    print(f"\nReasons FOR:")
    for r in judgement.reasons_for:
        print(f"  + {r}")
    print(f"\nReasons AGAINST:")
    for r in judgement.reasons_against:
        print(f"  - {r}")
    print(f"\nKey Aspects:")
    for asp in judgement.key_aspects:
        print(f"  {asp['from']} {asp['aspect']} {asp['to']} (orb: {asp['orb']:.1f})")
    print(f"\nDignities:")
    for planet, score in judgement.dignities.items():
        print(f"  {planet}: {score}")
    print(f"\nRecommendation: {judgement.recommendation}")


def test_llm_fallback():
    """Test LLM fallback interpretation."""
    print("\n" + "=" * 60)
    print("TEST 5: LLM Fallback Interpretation")
    print("=" * 60)
    
    question = "Should I buy BTC now?"
    dt = datetime(2026, 3, 22, 12, 0)
    
    chart = HoraryChart(question, dt)
    parser = QuestionParser().parse(question)
    judicator = LillyJudicator(chart, parser)
    judgement = judicator.judge()
    
    llm = HoraryLLM()
    interpretation = llm.interpret(chart, parser, judgement)
    
    print(interpretation)


async def test_async_interpret():
    """Test async interpret_question function."""
    print("\n" + "=" * 60)
    print("TEST 6: Async Interpret Question")
    print("=" * 60)
    
    result = await interpret_question(
        "Should I buy AAPL now?",
        lat=37.7749,
        lon=-122.4194,
        use_llm=False  # Use fallback for testing
    )
    
    print(f"Question: {result['question']}")
    print(f"Symbol: {result['symbol']}")
    print(f"Action: {result['action']}")
    print(f"Asset Class: {result['asset_class']}")
    print(f"\nVerdict: {result['verdict']['verdict']}")
    print(f"Confidence: {result['verdict']['confidence']}%")
    print(f"\nInterpretation:")
    print(result['interpretation'])


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("HORARY ASTROLOGY MODULE TESTS")
    print("=" * 60)
    
    test_basic_chart()
    test_question_parser()
    test_significators()
    test_judicator()
    test_llm_fallback()
    
    # Run async test
    asyncio.run(test_async_interpret())
    
    print("\n" + "=" * 60)
    print("ALL TESTS COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
