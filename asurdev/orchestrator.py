#!/usr/bin/env python3
"""asurdev Sentinel — Orchestrator (Multi-Agent Coordination)"""
import sys
sys.path.insert(0, '/home/workspace/asurdevSentinel')
from astro_agents import PlanetaryCalculatorAgent, PanchangaAgent, MuhurtaAgent, AstrologerAgent, SynthesizerAgent
import json

class asurdevSentinel:
    """
    asurdev Core Orchestrator.
    RULE №1: Все агенты используют ТОЛЬКО Swiss Ephemeris для расчётов.
    """
    def __init__(self):
        self.planetary_agent = PlanetaryCalculatorAgent()
        self.panchanga_agent = PanchangaAgent()
        self.muhurta_agent = MuhurtaAgent()
        self.astrologer_agent = AstrologerAgent()
        self.synthesizer_agent = SynthesizerAgent()
        
    def analyze(self, date: str, time: str, lat: float, lon: float) -> dict:
        """
        Полный анализ через мультиагентную систему.
        1. PlanetaryCalculator — планетарные позиции
        2. Panchanga — Tithi, Nakshatra, Yoga, Karana, Vara
        3. Muhurta — благоприятное время
        4. Astrologer — интерпретация
        5. Synthesizer — финальное решение
        """
        # Step 1: Planetary Calculator (Swiss Ephemeris)
        planetary_data = self.planetary_agent.run(date, time, lat, lon)
        
        # Step 2: Panchanga (Swiss Ephemeris)
        panchang_data = self.panchanga_agent.run(date, time, lat, lon)
        
        # Step 3: Muhurta (Swiss Ephemeris)
        muhurta_data = self.muhurta_agent.run(date, time, lat, lon)
        
        # Step 4: Astrologer (interpretation based on RAW data)
        interpretation = self.astrologer_agent.interpret(planetary_data, panchang_data)
        
        # Step 5: Synthesizer (final decision)
        final = self.synthesizer_agent.synthesize(planetary_data, panchang_data, interpretation)
        
        return {
            'status': 'success',
            'source': 'Swiss Ephemeris 2.10.03',
            'jd': planetary_data['raw_planets']['jd'],
            'datetime_utc': planetary_data['raw_planets']['datetime_utc'],
            'planetary_data': planetary_data,
            'panchang_data': panchang_data,
            'muhurta_data': muhurta_data,
            'interpretation': interpretation,
            'final_recommendation': final
        }

if __name__ == '__main__':
    print("="*60)
    print("asurdev SENTINEL — Multi-Agent System v2.10.03")
    print("Swiss Ephemeris: ONLY source of truth")
    print("="*60)
    
    sentinel = asurdevSentinel()
    
    # Example: March 22, 2026, 10:00 UTC, Moscow (55.7558, 37.6173)
    result = sentinel.analyze('2026-03-22', '10:00:00', 55.7558, 37.6173)
    
    print(f"\n📅 Date: {result['datetime_utc']}")
    print(f"   JD: {result['jd']}")
    print(f"\n🌟 Final Recommendation:")
    print(f"   Mood: {result['final_recommendation']['final_recommendation']['mood']}")
    print(f"   Focus: {result['final_recommendation']['final_recommendation']['key_focus']}")
    print(f"   Action: {result['final_recommendation']['final_recommendation']['action']}")
    print(f"   Avoid: {result['final_recommendation']['final_recommendation']['avoid']}")
    
    print(f"\n🌙 Moon: {result['interpretation']['interpretation']['moon_sign']} {result['interpretation']['interpretation']['moon_nakshatra']}")
    print(f"   Advice: {result['interpretation']['interpretation']['advice']}")
    
    print(f"\n📊 Panchanga:")
    print(f"   Tithi: {result['panchang_data']['panchang']['tithi']['name']}")
    print(f"   Nakshatra: {result['panchang_data']['panchang']['nakshatra']['name']}")
    print(f"   Yoga: {result['panchang_data']['panchang']['yoga']['name']}")
    print(f"   Vara: {result['panchang_data']['panchang']['vara']['name']}")
    
    print(f"\n⏰ Choghadiya: {result['muhurta_data']['choghadiya_today']['type']}")
    print(f"   {result['muhurta_data']['choghadiya_today']['description']}")
    print(f"   Verdict: {result['muhurta_data']['choghadiya_today']['verdict']}")
    
    print(f"\n🔗 Aspects (Moon):")
    for asp in result['planetary_data']['aspects']:
        if asp['planet1'] == 'Moon' or asp['planet2'] == 'Moon':
            print(f"   Moon {asp['aspect']} {asp['planet2' if asp['planet1'] == 'Moon' else 'planet1']} ({asp['angle']:.2f}°)")
