#!/usr/bin/env python3
"""
Test script for asurdev Sentinel v3.0
Проверяет все компоненты: Swiss Ephemeris, Western, Vedic, Financial, RAG
"""
import asyncio
import sys
from datetime import datetime

# Add project to path
sys.path.insert(0, "/home/workspace/asurdevSentinel")


def test_swiss_ephemeris():
    """Тест Swiss Ephemeris через Skyfield"""
    print("\n" + "=" * 60)
    print("TEST 1: Swiss Ephemeris (Skyfield + DE421)")
    print("=" * 60)
    
    try:
        from skyfield.api import load, utc
        
        ts = load.timescale()
        eph = load("/home/workspace/zo-space-lib/de421.bsp")
        
        dt = datetime(2026, 3, 22, 12, 0, tzinfo=utc)
        t = ts.from_datetime(dt)
        
        bodies = ["sun", "moon", "mercury", "venus", "mars", "jupiter barycenter", "saturn barycenter"]
        
        print(f"\nПозиции на {dt}:")
        positions = {}
        for body in bodies:
            pos = eph[body].at(t)
            ra, dec, dist = pos.radec(epoch="date")
            lon = (ra._degrees + 180) % 360
            sign_num = int(lon / 30) % 12
            deg_in_sign = lon % 30
            signs = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
                     "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
            
            clean_name = body.replace(" barycenter", "")
            positions[clean_name] = round(lon, 2)
            print(f"  {clean_name:20} → {lon:7.2f}° ({signs[sign_num]} {deg_in_sign:.1f}°)")
        
        print("\n✅ Swiss Ephemeris: OK")
        return positions
        
    except Exception as e:
        print(f"\n❌ Swiss Ephemeris ERROR: {e}")
        return None


def test_western_astrology(positions):
    """Тест Western Astrologer (Lilly)"""
    print("\n" + "=" * 60)
    print("TEST 2: Western Astrologer (Lilly)")
    print("=" * 60)
    
    try:
        from agents._impl.astro_council.western import WesternAstrologer
        
        astrologer = WesternAstrologer()
        result = astrologer.analyze(positions, is_day=True)
        
        print(f"\nSignal: {result['signal']} (confidence: {result['confidence']}%)")
        print(f"\nDignities:")
        for planet, data in result["dignities"].items():
            print(f"  {planet:10} in {data['sign']:12} → Score: {data['score']:+d}")
        
        print(f"\nAspects ({len(result['aspects'])} found):")
        for asp in result["aspects"][:5]:
            print(f"  {asp['planets']} {asp['symbol']} ({asp['nature']})")
        
        print("\n✅ Western Astrologer: OK")
        return result
        
    except Exception as e:
        print(f"\n❌ Western Astrologer ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_vedic_astrology(dt, moon_lon):
    """Тест Vedic Astrologer (Muhurta)"""
    print("\n" + "=" * 60)
    print("TEST 3: Vedic Astrologer (Muhurta)")
    print("=" * 60)
    
    try:
        from agents._impl.astro_council.vedic import VedicAstrologerAgent
        
        astrologer = VedicAstrologerAgent()
        result = astrologer.analyze(dt, moon_lon)
        
        print(f"\nNakshatra: {result['nakshatra']} (Pada {result['nakshatra_pada']})")
        print(f"Moon Sign: {result['moon_sign']}")
        print(f"Choghadiya: {result['choghadiya']} ({result['choghadiya_quality']})")
        print(f"Muhurta Score: {result['muhurta_score']}/100")
        print(f"\nSignal: {result['signal']} (confidence: {result['confidence']}%)")
        
        print("\n✅ Vedic Astrologer: OK")
        return result
        
    except Exception as e:
        print(f"\n❌ Vedic Astrologer ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_financial_astrologer(dt, positions):
    """Тест Financial Astrologer (Combined)"""
    print("\n" + "=" * 60)
    print("TEST 4: Financial Astrologer (Combined)")
    print("=" * 60)
    
    try:
        from agents._impl.astro_council.financial import FinancialAstrologer
        
        astrologer = FinancialAstrologer()
        result = astrologer.analyze(dt, positions)
        
        print(f"\nWeighted Score: {result['weighted_score']}")
        print(f"FINAL SIGNAL: {result['signal']} (confidence: {result['confidence']}%)")
        
        print(f"\nComponents:")
        print(f"  Western: {result['components']['western']['signal']}")
        print(f"  Vedic: {result['components']['vedic']['signal']}")
        print(f"  Moon Phase: {result['components']['moon_phase']['name']}")
        
        advice = result["trading_advice"]
        print(f"\nTrading Advice:")
        print(f"  Action: {advice['action']}")
        print(f"  Risk: {advice['risk_per_trade']}")
        print(f"  Position: {advice['position_size']}")
        
        if advice["warnings"]:
            print(f"  Warnings: {', '.join(advice['warnings'])}")
        
        print("\n✅ Financial Astrologer: OK")
        return result
        
    except Exception as e:
        print(f"\n❌ Financial Astrologer ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_astro_council_agent(dt, positions):
    """Тест AstroCouncil Agent (Async)"""
    print("\n" + "=" * 60)
    print("TEST 5: AstroCouncil Agent (Async)")
    print("=" * 60)
    
    try:
        from agents._impl.astro_council.agent import AstroCouncilAgent
        
        agent = AstroCouncilAgent(use_rag=False)  # RAG опционально
        context = {
            "datetime": dt.isoformat(),
            "symbol": "BTC",
            "positions": positions
        }
        
        result = await agent.analyze(context)
        
        print(f"\nSignal: {result.signal}")
        print(f"Confidence: {result.confidence}%")
        print(f"\nSummary:\n{result.summary}")
        
        print("\n✅ AstroCouncil Agent: OK")
        return result
        
    except Exception as e:
        print(f"\n❌ AstroCouncil Agent ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_rag():
    """Тест RAG системы (опционально)"""
    print("\n" + "=" * 60)
    print("TEST 6: RAG System (Obsidian Vault)")
    print("=" * 60)
    
    try:
        from rag import ObsidianKnowledgeBase
        
        kb = ObsidianKnowledgeBase(
            vault_path="/home/workspace/obsidian-sync",
            persist_dir="/home/workspace/asurdevSentinel/data/rag_index"
        )
        
        # Build index
        print("\nBuilding index...")
        count = kb.build_index(force_rebuild=False)
        print(f"Documents indexed: {count}")
        
        # Stats
        stats = kb.get_stats()
        print(f"\nStats: {stats}")
        
        # Query
        print("\nQuery test: 'Nakshatra trading'")
        context = kb.get_context("Nakshatra trading", max_length=500)
        if context:
            print(f"Context length: {len(context)} chars")
            print(f"Sample: {context[:200]}...")
        else:
            print("No context retrieved (empty vault?)")
        
        print("\n✅ RAG System: OK")
        return True
        
    except ImportError as e:
        print(f"\n⚠ RAG not available (missing deps): {e}")
        print("   Install: pip install sentence-transformers chromadb")
        return False
    except Exception as e:
        print(f"\n❌ RAG System ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Главный тест"""
    print("\n" + "=" * 60)
    print("asurdev SENTINEL v3.0 — TEST SUITE")
    print("=" * 60)
    
    from datetime import timezone
    dt = datetime(2026, 3, 22, 12, 0, tzinfo=timezone.utc)  # Тестовая дата
    
    # 1. Swiss Ephemeris
    positions = test_swiss_ephemeris()
    if not positions:
        print("\n❌ Critical error: Swiss Ephemeris failed")
        return
    
    # 2. Western
    test_western_astrology(positions)
    
    # 3. Vedic
    test_vedic_astrology(dt, positions["moon"])
    
    # 4. Financial (combined)
    test_financial_astrologer(dt, positions)
    
    # 5. AstroCouncil Agent
    await test_astro_council_agent(dt, positions)
    
    # 6. RAG (опционально)
    test_rag()
    
    print("\n" + "=" * 60)
    print("ALL TESTS COMPLETED")
    print("=" * 60)
    print("\nTo run full analysis:")
    print("  python -m agents.orchestrator --symbol BTC")


if __name__ == "__main__":
    asyncio.run(main())
