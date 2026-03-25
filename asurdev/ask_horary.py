#!/usr/bin/env python3
"""
ask_horary.py — CLI for horary astrology questions.
Usage: python ask_horary.py "Should I buy BTC now?"
"""

import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents._impl.horary_agent import HoraryAgent


async def main():
    if len(sys.argv) < 2:
        print("Usage: python ask_horary.py \"Should I buy BTC now?\"")
        print("       python ask_horary.py \"Should I sell AAPL?\"")
        print("       python ask_horary.py \"What will happen to ETH?\"")
        sys.exit(1)
    
    question = " ".join(sys.argv[1:])
    
    # Check if LLM is available
    use_llm = os.environ.get("asurdev_USE_LLM", "0") == "1"
    
    print(f"\n{'='*60}")
    print(f"HORARY ASTROLOGY")
    print(f"{'='*60}")
    print(f"Question: {question}")
    print(f"LLM: {'Enabled' if use_llm else 'Disabled (fallback only)'}")
    print(f"{'='*60}\n")
    
    # Run analysis
    agent = HoraryAgent(use_llm=use_llm)
    response = await agent.analyze({"question": question})
    
    # Print results
    print(f"VERDICT: {response.signal}")
    print(f"Confidence: {response.confidence}%\n")
    
    if "interpretation" in response.details:
        print(response.details["interpretation"])
    else:
        print("Reasons FOR:")
        for r in response.details.get("reasons_for", []):
            print(f"  + {r}")
        print("\nReasons AGAINST:")
        for r in response.details.get("reasons_against", []):
            print(f"  - {r}")
        print(f"\nRecommendation: {response.details.get('recommendation', 'N/A')}")
    
    print(f"\n{'='*60}")
    print(f"Symbol: {response.details.get('symbol', 'N/A')}")
    print(f"Asset Class: {response.details.get('asset_class', 'N/A')}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    asyncio.run(main())
