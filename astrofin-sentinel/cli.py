#!/usr/bin/env python3
"""
AstroFin Sentinel CLI — тестирование всех 11 агентов.

Usage:
    # Быстрый тест (3 агента)
    python cli.py --symbol BTC --action buy --price 67432.50 --mode quick
    
    # Стандартный режим (9 агентов)
    python cli.py --symbol ETH --action sell --price 3421.80 --mode standard
    
    # Полный режим (все 11 агентов)
    python cli.py --symbol SOL --action buy --price 142.50 --mode full
    
    # Тест конкретного агента
    python cli.py --agent RiskAgent -s BTC -p 65000 -a buy
    
    # Интерактивный режим
    python cli.py --interactive
"""

import asyncio
import argparse
import sys
from datetime import datetime
from typing import Optional

sys.path.insert(0, '/home/workspace/astrofin-sentinel')

from agents import (
    AgentFactory, AgentTeam,
    AgentInput, AgentOutput,
    Orchestrator, Alert,
)


async def test_single_agent(agent_name: str, symbol: str, price: float, 
                            action: str, strategy: str, timeframe: str = "1h") -> AgentOutput:
    """Тестирует одного агента."""
    print(f"\n{'='*60}")
    print(f"🤖 TESTING: {agent_name}")
    print(f"{'='*60}")
    
    try:
        agent = AgentFactory.get(agent_name)
    except ValueError as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    
    input_data = AgentInput(
        symbol=symbol,
        action=action,
        price=price,
        strategy=strategy,
        timeframe=timeframe,
        ml_confidence=0.75,
        astro_signal=False,
    )
    
    start = datetime.now()
    result = await agent.analyze(input_data)
    elapsed = (datetime.now() - start).total_seconds()
    
    print(f"\n🎯 Recommendation: {result.recommendation.upper()}")
    print(f"📈 Confidence: {result.confidence:.2%}")
    print(f"⏱️  Time: {elapsed:.1f}s")
    print(f"\n📝 Reasoning:\n{result.reasoning}")
    
    if result.key_factors:
        print(f"\n🔑 Key Factors:")
        for f in result.key_factors[:5]:
            print(f"   • {f[:100]}")
    
    if result.warnings:
        print(f"\n⚠️  Warnings:")
        for w in result.warnings[:3]:
            print(f"   • {w}")
    
    if result.metadata:
        print(f"\n📊 Metadata:")
        for k, v in list(result.metadata.items())[:5]:
            print(f"   • {k}: {v}")
    
    return result


async def test_full_orchestrator(symbol: str, price: float, action: str,
                                  strategy: str, timeframe: str = "1h",
                                  mode: str = "standard") -> Alert:
    """Тестирует оркестратор с выбранным режимом."""
    print(f"\n{'='*60}")
    print(f"🚀 ORCHESTRATOR TEST ({mode.upper()} MODE)")
    print(f"{'='*60}")
    print(f"   Symbol: {symbol}")
    print(f"   Action: {action.upper()}")
    print(f"   Price: ${price:,.2f}")
    print(f"   Strategy: {strategy}")
    print(f"{'='*60}")
    
    orchestrator = Orchestrator(mode=mode)
    
    raw_data = {
        "symbol": symbol,
        "action": action,
        "price": price,
        "strategy": strategy,
        "timeframe": timeframe,
        "ml_confidence": 0.75,
        "astro_signal": True,
    }
    
    start = datetime.now()
    alert = await orchestrator.process_alert(raw_data)
    elapsed = (datetime.now() - start).total_seconds()
    
    print(f"\n{'='*60}")
    print(f"📊 RESULTS SUMMARY")
    print(f"{'='*60}")
    print(f"⏱️  Total time: {elapsed:.1f}s")
    print(f"📈 Status: {alert.status.upper()}")
    
    if alert.error:
        print(f"❌ Error: {alert.error}")
        return alert
    
    # Выводим результаты всех агентов
    results_map = {
        "MarketAnalyst": alert.market_analyst_result,
        "BullResearcher": alert.bull_result,
        "BearResearcher": alert.bear_result,
        "CycleAgent": alert.cycle_result,
        "AstroCouncil": alert.astro_council_result,
        "GannAgent": alert.gann_result,
        "ElliotAgent": alert.elliot_result,
        "BradleyAgent": alert.bradley_result,
        "SentimentAgent": alert.sentiment_result,
        "RiskAgent": alert.risk_result,
        "TimeWindowAgent": alert.timewindow_result,
    }
    
    print(f"\n📊 Agent Results:")
    for name, result in results_map.items():
        if result:
            emoji = "🟢" if result.recommendation == "buy" else ("🔴" if result.recommendation == "sell" else "🟡")
            print(f"   {emoji} {name}: {result.recommendation.upper()} ({result.confidence:.0%})")
    
    # Synthesis
    if alert.synthesis_result:
        print(f"\n{'='*60}")
        print(f"🧠 FINAL SYNTHESIS")
        print(f"{'='*60}")
        print(f"   🎯 Recommendation: {alert.synthesis_result.recommendation.upper()}")
        print(f"   📈 Confidence: {alert.synthesis_result.confidence:.2%}")
        print(f"   📝 Reasoning: {alert.synthesis_result.reasoning[:200]}...")
    
    # Debate
    if alert.debate_result:
        print(f"\n{'='*60}")
        print(f"⚖️  DEBATE RESULT")
        print(f"{'='*60}")
        if isinstance(alert.debate_result, dict):
            print(f"   Consensus: {alert.debate_result.get('consensus', 'N/A')}")
            print(f"   Bull weight: {alert.debate_result.get('bull_weight', 'N/A')}")
            print(f"   Bear weight: {alert.debate_result.get('bear_weight', 'N/A')}")
    
    return alert


async def list_agents():
    """Выводит список всех доступных агентов."""
    from agents import AGENTS_REGISTRY
    
    print(f"\n{'='*60}")
    print(f"📋 AVAILABLE AGENTS ({len(AGENTS_REGISTRY)} total)")
    print(f"{'='*60}")
    
    categories = {
        "Core": ["MarketAnalyst", "BullResearcher", "BearResearcher", "DebateModerator"],
        "Cycle & Timing": ["CycleAgent", "GannAgent", "ElliotAgent", "BradleyAgent", "TimeWindowAgent"],
        "Astro & Sentiment": ["AstroCouncil", "SentimentAgent"],
        "Risk & Execution": ["RiskAgent"],
        "Synthesis": ["SynthesisEngine"],
    }
    
    for category, names in categories.items():
        print(f"\n🔹 {category}:")
        for name in names:
            if name in AGENTS_REGISTRY:
                print(f"   • {name}")


async def interactive_mode():
    """Интерактивный режим."""
    print(f"\n{'='*60}")
    print(f"🎮 INTERACTIVE MODE")
    print(f"{'='*60}")
    
    modes = ["quick", "standard", "full"]
    mode = "standard"
    
    while True:
        try:
            print(f"\nКоманды: list | mode | run | agent | quit")
            cmd = input("\n> ").strip().lower()
            
            if cmd in ('q', 'quit', 'exit'):
                print("👋 Goodbye!")
                break
            
            elif cmd == 'list':
                await list_agents()
            
            elif cmd == 'mode':
                print(f"Текущий режим: {mode}")
                print(f"Доступные: {modes}")
                new_mode = input("Новый режим: ").strip().lower()
                if new_mode in modes:
                    mode = new_mode
                    print(f"✅ Режим изменён на: {mode}")
            
            elif cmd == 'run':
                symbol = input("  Symbol (BTC): ").strip().upper() or "BTC"
                action = input("  Action (buy/sell): ").strip().lower() or "buy"
                price = float(input("  Price: ").strip() or "65000")
                strategy = input("  Strategy: ").strip() or "Manual"
                timeframe = input("  Timeframe (1h): ").strip() or "1h"
                
                await test_full_orchestrator(symbol, price, action, strategy, timeframe, mode)
            
            elif cmd == 'agent':
                agent_name = input("  Agent name: ").strip()
                if agent_name in AGENTS_REGISTRY:
                    symbol = input("  Symbol (BTC): ").strip().upper() or "BTC"
                    action = input("  Action (buy): ").strip().lower() or "buy"
                    price = float(input("  Price: ").strip() or "65000")
                    strategy = input("  Strategy: ").strip() or "Manual"
                    await test_single_agent(agent_name, symbol, price, action, strategy)
                else:
                    print(f"❌ Неизвестный агент: {agent_name}")
            
            else:
                print("Доступные команды: list, mode, run, agent, quit")
        
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")


async def show_status():
    """Показывает статус Ollama и агентов."""
    from llm.ollama_client import get_ollama
    from agents import AGENTS_REGISTRY
    
    print(f"\n{'='*60}")
    print(f"🔍 SYSTEM STATUS")
    print(f"{'='*60}")
    
    # Ollama status
    print(f"\n📡 Ollama:")
    try:
        llm = get_ollama()
        info = llm.get_model_info()
        print(f"   Model: {info['model']}")
        print(f"   URL: {info['base_url']}")
        print(f"   Temperature: {info['temperature']}")
        print(f"   Context: {info['num_ctx']}")
        print(f"   Status: {'✅ Connected' if info['available'] else '❌ Not available'}")
        
        # Check available models
        import requests
        resp = requests.get(f"{info['base_url']}/api/tags", timeout=2)
        if resp.status_code == 200:
            models = resp.json().get('models', [])
            print(f"   Installed models ({len(models)}):")
            for m in models:
                size_gb = m.get('size', 0) / (1024**3)
                print(f"      • {m['name']} ({size_gb:.1f} GB)")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Agents
    print(f"\n🤖 Agents: {len(AGENTS_REGISTRY)} total")
    
    categories = {
        "Core": ["MarketAnalyst", "BullResearcher", "BearResearcher", "DebateModerator"],
        "Cycle & Timing": ["CycleAgent", "GannAgent", "ElliotAgent", "BradleyAgent", "TimeWindowAgent"],
        "Astro & Sentiment": ["AstroCouncil", "SentimentAgent"],
        "Risk & Execution": ["RiskAgent"],
        "Synthesis": ["SynthesisEngine"],
    }
    
    for category, names in categories.items():
        print(f"\n   🔹 {category}:")
        for name in names:
            if name in AGENTS_REGISTRY:
                print(f"      • {name}")


def main():
    parser = argparse.ArgumentParser(
        description="AstroFin Sentinel CLI — 11 агентов для алгоритмической торговли"
    )
    
    # Basic args
    parser.add_argument("--symbol", "-s", default="BTC", help="Trading symbol")
    parser.add_argument("--action", "-a", default="buy", choices=["buy", "sell", "hold"], help="Action")
    parser.add_argument("--price", "-p", type=float, default=67432.50, help="Entry price")
    parser.add_argument("--strategy", default="MomentumBreakout", help="Strategy name")
    parser.add_argument("--timeframe", "-t", default="1h", help="Timeframe")
    
    # Mode
    parser.add_argument("--mode", "-m", default="standard", 
                       choices=["quick", "standard", "full"],
                       help="Orchestrator mode")
    
    # Single agent
    parser.add_argument("--agent", help="Test single agent by name")
    
    # Flags
    parser.add_argument("--interactive", "-i", action="store_true", help="Interactive mode")
    parser.add_argument("--list", "-l", action="store_true", help="List all agents")
    parser.add_argument("--status", action="store_true", help="Show system status")
    
    args = parser.parse_args()
    
    if args.status:
        asyncio.run(show_status())
    elif args.list:
        asyncio.run(list_agents())
    elif args.interactive:
        asyncio.run(interactive_mode())
    elif args.agent:
        asyncio.run(test_single_agent(
            args.agent,
            args.symbol,
            args.price,
            args.action,
            args.strategy,
            args.timeframe,
        ))
    else:
        asyncio.run(test_full_orchestrator(
            args.symbol,
            args.price,
            args.action,
            args.strategy,
            args.timeframe,
            args.mode,
        ))


if __name__ == "__main__":
    main()
