#!/usr/bin/env python3
"""
AstroFin Sentinel - Main Entry Point

Multi-agent financial advisory system combining:
- Technical Analysis
- Fundamental Analysis  
- Vedic Astrology (Mankashi)

Usage:
    python main.py --symbol BTC/USDT --side buy
    python main.py --symbol ETH/USDT --side sell --birth-date 03.05.1967 --birth-time 07:15
    python main.py --symbol SOL/USDT --interval 4h --weights technical=0.4 fundamental=0.4 astrological=0.2
"""

import argparse
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.orchestrator import get_orchestrator, analyze_symbol


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="AstroFin Sentinel - Multi-Agent Financial Advisor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --symbol BTC/USDT --side buy
  python main.py --symbol ETH/USDT --side sell --birth-date 03.05.1967 --birth-time 07:15
  python main.py --symbol SOL/USDT --interval 4h
  python main.py --symbol BNB/USDT --weights technical=0.3 fundamental=0.3 astrological=0.4

Weights sum must equal 1.0. Default weights:
  - Technical: 0.30
  - Fundamental: 0.30
  - Astrological: 0.40
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
        "--output", "-o",
        choices=["markdown", "json"],
        default="markdown",
        help="Output format"
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


def main():
    """Main entry point."""
    args = parse_args()
    
    # Validate weights
    weights = None
    if args.weights:
        weights = validate_weights(args.weights)
        print(f"Using custom weights: {weights}")
    
    print(f"\n🔮 AstroFin Sentinel - Analyzing {args.symbol} ({args.side.upper()})\n")
    print(f"   Timeframe: {args.interval}")
    if args.birth_date:
        print(f"   Birth Chart: {args.birth_date} {args.birth_time}")
    print("-" * 60)
    
    try:
        # Run analysis
        result = analyze_symbol(
            symbol=args.symbol,
            side=args.side,
            interval=args.interval,
            birth_date=args.birth_date,
            birth_time=args.birth_time
        )
        
        # Output
        if args.output == "markdown":
            print(result)
        elif args.output == "json":
            import json
            # Would need to serialize the result to JSON
            print(json.dumps({"status": "success", "output": result[:500] + "..."}))
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Analysis cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
