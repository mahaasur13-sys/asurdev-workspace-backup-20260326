"""
CLI entry point for asurdev Sentinel.

Usage:
    python -m agents --symbol BTC --date 2026-03-22
    python -m agents --symbol ETH --date 2026-03-22 --lat 55.75 --lon 37.62
    python -m agents --symbol BTC --action buy
"""

import argparse
import asyncio
import sys
import os

# Ensure package root is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.langgraph_orchestrator import LangGraphOrchestrator
from agents.types import Signal


def parse_args():
    parser = argparse.ArgumentParser(
        description="asurdev Sentinel — Multi-Agent Trading Analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python -m agents --symbol BTC --date 2026-03-22
    python -m agents --symbol ETH --action buy --lat 55.75 --lon 37.62
        """
    )
    
    parser.add_argument(
        "--symbol", "-s",
        default="BTC",
        help="Trading symbol (BTC, ETH, etc.) [default: BTC]"
    )
    
    parser.add_argument(
        "--date", "-d",
        default=None,
        help="Analysis date (YYYY-MM-DD). Uses current date if not specified."
    )
    
    parser.add_argument(
        "--action", "-a",
        default="hold",
        choices=["buy", "sell", "hold"],
        help="Trading action [default: hold]"
    )
    
    parser.add_argument(
        "--lat",
        type=float,
        default=53.1955,
        help="Latitude for astrological calculations [default: 53.1955 (Samara, Russia)]"
    )
    
    parser.add_argument(
        "--lon",
        type=float,
        default=50.1017,
        help="Longitude for astrological calculations [default: 50.1017 (Samara, Russia)]"
    )
    
    parser.add_argument(
        "--no-interrupt",
        action="store_true",
        help="Run without interrupting before synthesis (full auto mode)"
    )
    
    parser.add_argument(
        "--review",
        action="store_true",
        help="Stop for human review before final synthesis"
    )
    
    return parser.parse_args()


def print_result(result: dict):
    """Print analysis results in human-readable format."""
    
    print("\n" + "=" * 50)
    print(f"📊 Final Verdict: {result['final_verdict'].value}")
    print(f"📈 Avg Confidence: {result['confidence_avg']:.1f}%")
    
    print("\n📋 Agent Signals:")
    agent_keys = [
        "market", "bull", "bear", "astro", "cycle",
        "dow", "andrews", "gann", "meridian"
    ]
    for key in agent_keys:
        resp = result.get(f"{key}_response")
        if resp:
            print(f"  {key:12}: {resp.signal} ({resp.confidence}%)")
    
    if result.get("synthesis"):
        synthesis = result["synthesis"]
        print(f"\n💬 Synthesis Summary: {synthesis.summary[:300]}")
        if synthesis.details:
            print("\n📊 Additional Details:")
            for k, v in list(synthesis.details.items())[:10]:
                print(f"  {k}: {v}")
    
    # Show AstroCouncil specifically
    if result.get("astro_response"):
        astro = result["astro_response"]
        print(f"\n🌙 AstroCouncil Analysis:")
        if astro.details:
            details = astro.details
            if "components" in details:
                comp = details["components"]
                print(f"  Western: {comp.get('western', {}).get('signal', 'N/A')}")
                print(f"  Vedic: {comp.get('vedic', {}).get('signal', 'N/A')}")
                print(f"  Moon Phase: {comp.get('moon_phase', {}).get('name', 'N/A')}")
            else:
                for k, v in list(details.items())[:5]:
                    print(f"  {k}: {v}")
    
    # Show errors if any
    if result.get("errors"):
        print("\n⚠️  Errors encountered:")
        for err in result["errors"]:
            print(f"  - {err}")
    
    print("\n" + "=" * 50)


async def setup_langsmith():
    """Initialize LangSmith tracing if API key is available."""
    import os
    langsmith_key = os.getenv("LANGSMITH_API_KEY")
    if langsmith_key:
        try:
            from langsmith import traceable
            os.environ["LANGSMITH_TRACING"] = "true"
            os.environ["LANGSMITH_PROJECT"] = os.getenv("LANGSMITH_PROJECT", "asurdev-sentinel")
            print(f"✓ LangSmith enabled: project={os.environ['LANGSMITH_PROJECT']}")
            return True
        except ImportError:
            print("⚠️  langsmith not installed — run: pip install langsmith")
    else:
        print("⚠️  LangSmith not configured — set LANGSMITH_API_KEY for tracing")
    return False


async def main():
    args = parse_args()
    
    # Initialize LangSmith tracing
    await setup_langsmith()
    
    print("🔮 asurdev Sentinel v3.1 (Refactored)")
    print("=" * 50)
    print(f"📌 Symbol: {args.symbol}")
    print(f"📌 Action: {args.action}")
    print(f"📌 Location: {args.lat}, {args.lon}")
    if args.date:
        print(f"📌 Date: {args.date}")
    
    # Create orchestrator
    interrupt_before = [] if args.no_interrupt else ["synthesize"]
    
    orchestrator = LangGraphOrchestrator(
        interrupt_before=interrupt_before if not args.review else ["synthesize"]
    )
    
    print("\n📊 Running analysis...")
    
    try:
        result = await orchestrator.analyze(
            symbol=args.symbol,
            action=args.action,
            lat=args.lat,
            lon=args.lon,
        )
        
        print_result(result)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Analysis interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
