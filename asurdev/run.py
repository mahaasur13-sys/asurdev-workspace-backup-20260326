#!/usr/bin/env python3
"""
asurdev Sentinel - Main Entry Point
"""
import sys
import asyncio
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


def show_help():
    print("""
asurdev Sentinel - Trading Advisor System

Usage:
    python run.py <command>

Commands:
    analyze <symbol>     Analyze a symbol (e.g., BTC, ETH)
    dashboard           Launch Streamlit dashboard
    backtest <symbol>   Run backtest for symbol
    test                Run system tests
    status              Show system status

Examples:
    python run.py analyze BTC
    python run.py dashboard
    python run.py backtest ETH
    """)


async def run_analysis(symbol: str):
    from agents import get_orchestrator
    
    print(f"Starting analysis for {symbol}...")
    orchestrator = get_orchestrator()
    result = await orchestrator.analyze(symbol)
    
    print(f"\n=== Analysis Result ===")
    print(f"Symbol: {result.get('symbol')}")
    print(f"Signal: {result.get('signal')}")
    print(f"Confidence: {result.get('confidence')}%")
    
    return result


def main():
    parser = argparse.ArgumentParser(description="asurdev Sentinel")
    parser.add_argument("command", nargs="?", default="help")
    parser.add_argument("symbol", nargs="?", default="BTC")
    parser.add_argument("--model", default="qwen2.5-coder:32b")
    
    args = parser.parse_args()
    
    if args.command == "analyze":
        asyncio.run(run_analysis(args.symbol))
    elif args.command == "dashboard":
        print("Launching dashboard...")
        import subprocess
        subprocess.run([sys.executable, "-m", "streamlit", "run", "ui/dashboard.py"])
    elif args.command == "test":
        print("Running tests...")
        subprocess.run([sys.executable, "-m", "pytest", "tests/", "-v"])
    elif args.command == "status":
        print("System Status: OK")
        print(f"Model: {args.model}")
    else:
        show_help()


if __name__ == "__main__":
    main()
