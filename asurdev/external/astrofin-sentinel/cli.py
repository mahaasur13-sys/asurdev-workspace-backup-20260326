"""
AstroFin Sentinel — CLI Entry Point (LangGraph Edition)

Multi-agent financial advisory system using LangGraph with:
- Parallel async agent execution
- RAG memory for context
- Conditional routing

Usage:
    python cli.py --symbol BTC/USDT --side buy
    python cli.py --symbol ETH/USDT --side sell --birth-date 03.05.1967 --birth-time 07:15
    python cli.py --symbol SOL/USDT --interval 4h --weights 0.4 0.4 0.2
    python cli.py --symbol BTC/USDT --quick  # Skip astrologer for speed
"""

import argparse
import asyncio
import sys
import os
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from graph import run_analysis, AnalysisState
from graph.state import QueryType


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="AstroFin Sentinel — Multi-Agent Financial Advisor (LangGraph)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli.py --symbol BTC/USDT --side buy
  python cli.py --symbol ETH/USDT --side sell --birth-date 03.05.1967 --birth-time 07:15
  python cli.py --symbol SOL/USDT --interval 4h
  python cli.py --symbol BNB/USDT --weights 0.3 0.3 0.4
  python cli.py --symbol BTC/USDT --quick  # Technical only, faster
  python cli.py --symbol BTC/USDT --session my-session-1

Weights (sum must = 1.0):
  --weights TECHNICAL FUNDAMENTAL ASTROLOGICAL
  Default: 0.30 0.30 0.40
        """
    )
    
    parser.add_argument(
        "--symbol", "-s",
        required=True,
        help="Trading symbol (e.g., BTC/USDT, ETH/USDT)"
    )
    
    parser.add_argument(
        "--side", "-d",
        default="buy",
        choices=["buy", "sell"],
        help="Trading side (buy or sell)"
    )
    
    parser.add_argument(
        "--interval", "-i",
        default="1h",
        choices=["1m", "5m", "15m", "1h", "4h", "1d", "1w"],
        help="Timeframe for technical analysis"
    )
    
    parser.add_argument(
        "--birth-date",
        help="Birth date for personalized astrology (DD.MM.YYYY)"
    )
    
    parser.add_argument(
        "--birth-time",
        help="Birth time for personalized astrology (HH:MM)"
    )
    
    parser.add_argument(
        "--weights", "-w",
        nargs=3,
        metavar=("TECHNICAL", "FUNDAMENTAL", "ASTROLOGICAL"),
        type=float,
        help="Custom weights for synthesis (must sum to 1.0)"
    )
    
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Quick analysis (skip astrologer for speed)"
    )
    
    parser.add_argument(
        "--session",
        default=None,
        help="Session ID for memory context"
    )
    
    parser.add_argument(
        "--output", "-o",
        choices=["markdown", "json", "simple"],
        default="markdown",
        help="Output format"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output with agent timings"
    )
    
    return parser.parse_args()


def validate_weights(weights: list) -> dict:
    """Validate and normalize weights."""
    if weights is None:
        return None
    
    if len(weights) != 3:
        raise ValueError("Weights must have exactly 3 values")
    
    if abs(sum(weights) - 1.0) > 0.01:
        raise ValueError(f"Weights must sum to 1.0, got {sum(weights)}")
    
    return {
        "technical": weights[0],
        "fundamental": weights[1],
        "astrological": weights[2]
    }


def print_header(symbol: str, side: str, interval: str, birth_date: str = None):
    """Print analysis header."""
    print(f"\n🔮 AstroFin Sentinel (LangGraph Edition)")
    print(f"   Analyzing: {symbol} ({side.upper()})")
    print(f"   Timeframe: {interval}")
    if birth_date:
        print(f"   Birth Chart: {birth_date}")
    print("-" * 60)
    print()


async def run_async(symbol: str, side: str, interval: str,
                   birth_date: str, birth_time: str,
                   weights: dict, quick: bool, session_id: str,
                   verbose: bool) -> AnalysisState:
    """Run the async analysis."""
    skip_agents = ["astrologer"] if quick else []
    
    # Print agent status
    if verbose:
        agents = ["Technical", "Fundamental"]
        if not quick:
            agents.append("Astrologer")
        print(f"📊 Running agents: {', '.join(agents)}")
    
    # Run analysis
    state = await run_analysis(
        symbol=symbol,
        side=side,
        interval=interval,
        birth_date=birth_date,
        birth_time=birth_time,
        weights=weights,
        session_id=session_id
    )
    
    return state


def print_timings(state: AnalysisState):
    """Print agent execution timings."""
    print("\n⏱️  Agent Timings:")
    
    for agent in ["technical", "fundamental", "astrologer"]:
        meta = getattr(state, f"{agent}_meta")
        if meta and meta.execution_time_ms:
            status = meta.status.value
            print(f"   {agent.capitalize():15} {status:10} {meta.execution_time_ms:6}ms")
    
    if state.memory_context:
        print(f"   Memory retrieval: {len(state.memory_context)} relevant entries found")


def format_json(state: AnalysisState) -> str:
    """Format state as JSON."""
    import json
    
    result = {
        "symbol": state.symbol,
        "side": state.side,
        "interval": state.interval,
        "composite_score": state.composite_score,
        "recommendation": state.final_recommendation,
        "agent_reports": {},
        "scenarios": state.synthesizer_report.get("scenarios") if state.synthesizer_report else None,
        "risk_warnings": state.synthesizer_report.get("risk_warnings") if state.synthesizer_report else None,
        "timestamp": state.completed_at.isoformat() if state.completed_at else datetime.now().isoformat()
    }
    
    if state.technical_report:
        result["agent_reports"]["technical"] = state.technical_report.to_dict()
    if state.fundamental_report:
        result["agent_reports"]["fundamental"] = state.fundamental_report.to_dict()
    if state.astrologer_report:
        result["agent_reports"]["astrologer"] = state.astrologer_report.to_dict()
    
    return json.dumps(result, indent=2, ensure_ascii=False, default=str)


def format_simple(state: AnalysisState) -> str:
    """Format state as simple text."""
    lines = []
    lines.append(f"\n{'='*50}")
    lines.append(f"🎯 {state.symbol} — {state.side.upper()}")
    lines.append(f"{'='*50}")
    lines.append(f"\n📊 Composite Score: {state.composite_score:.3f}/1.00")
    
    if state.final_recommendation:
        lines.append(f"\n📋 RECOMMENDATION: {state.final_recommendation.get('action')}")
        lines.append(f"   Entry: {state.final_recommendation.get('entry_zone')}")
        lines.append(f"   Stop-Loss: {state.final_recommendation.get('stop_loss')}")
        lines.append(f"   Position: {state.final_recommendation.get('position_size')}")
    
    lines.append("\n📈 Signals:")
    if state.technical_report:
        lines.append(f"   Technical: {state.technical_report.signal} ({state.technical_report.confidence:.0%})")
    if state.fundamental_report:
        lines.append(f"   Fundamental: {state.fundamental_report.signal} ({state.fundamental_report.confidence:.0%})")
    if state.astrologer_report:
        lines.append(f"   Astrologer: {state.astrologer_report.signal} ({state.astrologer_report.confidence:.0%})")
    
    if state.synthesizer_report and state.synthesizer_report.get("risk_warnings"):
        lines.append("\n⚠️  Warnings:")
        for warning in state.synthesizer_report["risk_warnings"][:3]:
            lines.append(f"   {warning}")
    
    lines.append(f"\n{'='*50}\n")
    return "\n".join(lines)


async def main_async():
    """Async main entry point."""
    args = parse_args()
    
    # Validate weights
    weights = validate_weights(args.weights)
    if weights:
        print(f"Using custom weights: {weights}")
    
    # Print header
    print_header(args.symbol, args.side, args.interval,
                args.birth_date)
    
    try:
        # Run analysis
        state = await run_async(
            symbol=args.symbol,
            side=args.side,
            interval=args.interval,
            birth_date=args.birth_date,
            birth_time=args.birth_time,
            weights=weights,
            quick=args.quick,
            session_id=args.session,
            verbose=args.verbose
        )
        
        # Check for errors
        if state.error and not state.final_recommendation:
            print(f"\n❌ Error: {state.error}")
            return 1
        
        # Print timings if verbose
        if args.verbose:
            print_timings(state)
        
        # Output based on format
        if args.output == "markdown":
            if state.markdown_output:
                print(state.markdown_output)
            else:
                print(format_simple(state))
        elif args.output == "json":
            print(format_json(state))
        elif args.output == "simple":
            print(format_simple(state))
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Analysis cancelled by user")
        return 1
    except Exception as e:
        print(f"\n❌ Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


def main():
    """Main entry point."""
    exit_code = asyncio.run(main_async())
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
