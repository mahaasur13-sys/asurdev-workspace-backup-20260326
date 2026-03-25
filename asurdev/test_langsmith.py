#!/usr/bin/env python3
"""
asurdev Sentinel — Test Script with LangSmith Observability

Usage:
    # Without LangSmith
    python test_langsmith.py
    
    # With LangSmith (get API key from https://smith.langchain.com)
    export LANGSMITH_API_KEY="ls_..."
    export LANGSMITH_PROJECT="asurdev-sentinel-test"
    python test_langsmith.py
"""

import asyncio
import os
import sys
from datetime import datetime

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# =============================================================================
# LANGSMITH SETUP
# =============================================================================

LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY", "")
LANGSMITH_PROJECT = os.getenv("LANGSMITH_PROJECT", "asurdev-sentinel-test")

if LANGSMITH_API_KEY:
    os.environ["LANGSMITH_API_KEY"] = LANGSMITH_API_KEY
    print(f"✓ LangSmith configured: project={LANGSMITH_PROJECT}")
    print(f"  View traces at: https://smith.langchain.com/o/{LANGSMITH_API_KEY[:8]}.../projects/p/{LANGSMITH_PROJECT}")
else:
    print("⚠️  LANGSMITH_API_KEY not set — running without cloud tracing")
    print("   Get free key at: https://smith.langchain.com")

print()

# =============================================================================
# IMPORTS
# =============================================================================

from agents.langgraph_orchestrator import LangGraphOrchestrator
from agents.signal import Signal


# =============================================================================
# TEST FUNCTIONS
# =============================================================================

async def test_quick_analysis():
    """Test basic analysis"""
    print("=" * 60)
    print("🧪 Test 1: Quick Analysis (BTC)")
    print("=" * 60)
    
    orchestrator = LangGraphOrchestrator()
    result = await orchestrator.analyze("BTC", action="hold")
    
    print_result(result)
    return result


async def test_eth_analysis():
    """Test ETH analysis"""
    print("\n" + "=" * 60)
    print("🧪 Test 2: ETH Analysis")
    print("=" * 60)
    
    orchestrator = LangGraphOrchestrator()
    result = await orchestrator.analyze("ETH", action="buy")
    
    print_result(result)
    return result


async def test_review_mode():
    """Test human-in-the-loop review mode"""
    print("\n" + "=" * 60)
    print("🧪 Test 3: Review Mode (stop before synthesis)")
    print("=" * 60)
    
    orchestrator = LangGraphOrchestrator(
        interrupt_before=["synthesize"]
    )
    
    thread_id = f"test_{datetime.now().strftime('%H%M%S')}"
    print(f"Thread ID: {thread_id}")
    
    initial_state = {
        "messages": [],
        "symbol": "BTC",
        "action": "hold",
        "market_price": 67000,
        "market_trend": "NEUTRAL",
        "market_response": None,
        "bull_response": None,
        "bear_response": None,
        "astro_response": None,
        "cycle_response": None,
        "dow_response": None,
        "andrews_response": None,
        "gann_response": None,
        "merriman_response": None,
        "meridian_response": None,
        "synthesis": None,
        "final_verdict": Signal.NEUTRAL,
        "errors": [],
        "confidence_avg": 0,
    }
    
    config = {"configurable": {"thread_id": thread_id}}
    
    # Run until interrupt
    state = await orchestrator.app.ainvoke(initial_state, config)
    
    print("\n📍 State BEFORE synthesis (interrupt point):")
    for key in ["market", "bull", "bear", "astro", "cycle", "dow", "andrews", "gann", "merriman", "meridian"]:
        resp = state.get(f"{key}_response")
        if resp:
            print(f"  {key:12}: {resp.signal} ({resp.confidence}%)")
    
    print("\n🔍 No synthesis yet — human review would happen here")
    print("   To resume: orchestrator.app.ainvoke(None, config)")
    
    return state


def print_result(result: dict):
    """Print analysis result"""
    print(f"\n📊 Final Verdict: {result['final_verdict'].value}")
    print(f"📈 Avg Confidence: {result.get('confidence_avg', 0):.1f}%")
    
    if result.get("errors"):
        print(f"\n⚠️  Errors: {result['errors']}")
    
    print("\n📋 Agent Signals:")
    for key in ["market", "bull", "bear", "astro", "cycle", "dow", "andrews", "gann", "merriman", "meridian"]:
        resp = result.get(f"{key}_response")
        if resp:
            signal_emoji = {
                "STRONG_BUY": "🟢🟢",
                "BUY": "🟢",
                "HOLD": "⚪",
                "NEUTRAL": "⚪",
                "SELL": "🔴",
                "STRONG_SELL": "🔴🔴",
            }.get(resp.signal, "❓")
            print(f"  {key:12}: {signal_emoji} {resp.signal} ({resp.confidence}%)")
    
    synthesis = result.get("synthesis")
    if synthesis:
        print(f"\n💬 Synthesis Summary:")
        print(f"   {synthesis.summary[:400]}")
    
    return result


# =============================================================================
# MAIN
# =============================================================================

async def main():
    print("🔮 asurdev Sentinel — LangSmith Test Suite")
    print("=" * 60)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"LangSmith: {'✓ Enabled' if LANGSMITH_API_KEY else '✗ Disabled'}")
    print()
    
    try:
        # Run tests
        await test_quick_analysis()
        await test_eth_analysis()
        await test_review_mode()
        
        print("\n" + "=" * 60)
        print("✅ All tests completed!")
        print("=" * 60)
        
        if LANGSMITH_API_KEY:
            print(f"\n📊 View traces: https://smith.langchain.com")
            print(f"   Project: {LANGSMITH_PROJECT}")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
