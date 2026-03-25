"""
AstroFin Sentinel - Multi-Agent Trading Assistant with Astrology

Usage:
    from src.main import run
    
    result = run("BTC", timeframe="4h")
    print(result.final_recommendation)
"""
from src.graph.compiler import run_analysis
from src.types import Symbol, TimeFrame, Decision
import os


def run(symbol: str, timeframe: str = "4h", question: str = "") -> dict:
    """
    Run a full analysis on a symbol.
    
    Args:
        symbol: "BTC", "ETH", "SOL" etc.
        timeframe: "1h", "4h", "1d", "7d"
        question: Optional custom question/context
    
    Returns:
        BoardVote object with final decision
    """
    # Map string to enum
    symbol_map = {"BTC": Symbol.BTC, "ETH": Symbol.ETH, "SOL": Symbol.SOL}
    timeframe_map = {"1h": TimeFrame.HOUR_1, "4h": TimeFrame.HOUR_4, "1d": TimeFrame.DAY_1, "7d": TimeFrame.DAY_7}
    
    sym = symbol_map.get(symbol.upper(), Symbol.BTC)
    tf = timeframe_map.get(timeframe, TimeFrame.HOUR_4)
    
    result = run_analysis(sym, tf, question)
    
    return result


def run_cli():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="AstroFin Sentinel")
    parser.add_argument("symbol", help="Symbol (BTC, ETH, SOL)")
    parser.add_argument("--timeframe", "-t", default="4h", help="Timeframe (1h, 4h, 1d, 7d)")
    parser.add_argument("--question", "-q", default="", help="Custom question")
    
    args = parser.parse_args()
    
    print(f"\n🔮 AstroFin Sentinel - Analyzing {args.symbol}...\n")
    
    result = run(args.symbol, args.timeframe, args.question)
    
    print(result.final_recommendation)
    print("\n" + "="*50)
    print(f"Decision: {result.final_decision.value}")
    print(f"Confidence: {result.final_confidence:.1%}")
    print(f"Consensus: {result.consensus_score:.1%}")
    print(f"Risk: {result.risk_assessment}")


if __name__ == "__main__":
    run_cli()
