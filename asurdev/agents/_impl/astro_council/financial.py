"""
Financial Astrologer — объединяет Western + Vedic для рыночного тайминга
ДETERMINISTIC VERSION
"""
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from .western import WesternAstrologer
from .vedic import VedicAstrologerAgent


@dataclass
class AstroSignal:
    """Сигнал от астрологии"""
    source: str
    signal: str
    confidence: int
    score: float
    reasoning: str


class FinancialAstrologer:
    """
    Financial Astrologer — финальный астрологический советник.
    
    Объединяет Western + Vedic анализ и выдаёт финальный сигнал.
    
    Использует ТОЛЬКО детерминированные расчёты:
    1. Western: Essential Dignities + Aspects
    2. Vedic: Nakshatras + Choghadiya + Muhurta
    3. Moon Phase (традиционный индикатор)
    """

    def __init__(self):
        self.western = WesternAstrologer()
        self.vedic = VedicAstrologerAgent()

    def analyze(
        self,
        dt: datetime,
        positions: Dict[str, float],  # {planet: longitude}
        rag_context: Optional[str] = None
    ) -> Dict:
        """
        Полный финансовый астрологический анализ.
        
        Args:
            dt: Дата/время
            positions: Планетарные позиции {planet: degree}
            rag_context: Опциональный контекст из RAG
            
        Returns:
            Dict с финальным сигналом и всеми компонентами
        """
        # 1. Western Analysis
        western_result = self.western.analyze(positions, is_day=True)
        
        # 2. Vedic Analysis
        moon_long = positions.get("Moon", 0)
        # Create mock eph for vedic (it expects full eph structure)
        mock_eph = {"positions": positions, "panchanga": {}, "current_choghadiya": {}}
        vedic_result = self.vedic.analyze(mock_eph, moon_long)
        
        # 3. Moon Phase (простой расчёт)
        moon_phase = self._calculate_moon_phase(dt)
        
        # 4. Final signal через weighted combination
        signals = []
        
        # Western signal (вес 40%)
        west_signal = self._convert_western_signal(
            western_result["signal"],
            western_result["confidence"]
        )
        signals.append(("Western", west_signal, 0.40))
        
        # Vedic signal (вес 40%)
        vedic_signal = self._convert_vedic_signal(
            vedic_result["signal"],
            vedic_result["confidence"]
        )
        signals.append(("Vedic", vedic_signal, 0.40))
        
        # Moon phase (вес 20%)
        moon_signal = self._moon_phase_signal(moon_phase)
        signals.append(("Moon Phase", moon_signal, 0.20))
        
        # Calculate weighted score
        final_score = sum(s[1]["score"] * s[2] for s in signals)
        final_signal = self._score_to_signal(final_score)
        
        # Confidence based on agreement
        agreements = sum(1 for s in signals if s[1]["signal"] == final_signal)
        confidence = int(50 + (agreements / 3) * 40)  # 50-90%
        
        return {
            "timestamp": dt.isoformat(),
            "components": {
                "western": {
                    "signal": western_result["signal"],
                    "confidence": western_result["confidence"],
                    "moon_dignity": western_result["dignities"].get("Moon", {}),
                    "aspects_count": len(western_result["aspects"])
                },
                "vedic": {
                    "signal": vedic_result["signal"],
                    "confidence": vedic_result["confidence"],
                    "nakshatra": vedic_result["nakshatra"],
                    "choghadiya": vedic_result["choghadiya"],
                    "muhurta_score": vedic_result["muhurta_score"]
                },
                "moon_phase": {
                    "name": moon_phase["name"],
                    "illumination": moon_phase["illumination"],
                    "signal": moon_signal["signal"]
                }
            },
            "weighted_score": round(final_score, 1),
            "signal": final_signal,
            "confidence": confidence,
            "interpretation": self._format_interpretation(
                western_result, vedic_result, moon_phase, final_signal
            ),
            "trading_advice": self._get_trading_advice(
                final_signal, confidence, vedic_result
            ),
            "rag_context_used": rag_context is not None
        }

    def _calculate_moon_phase(self, dt: datetime) -> Dict:
        """
        Расчёт фазы Луны.
        Новолуние = 0%, Полнолуние = 100%
        """
        # Julian Day
        a = (14 - dt.month) // 12
        y = dt.year + 4800 - a
        m = dt.month + 12 * a - 3
        jd = dt.day + (153 * m + 2) // 5 + 365 * y + y // 4 - y // 100 + y // 400 - 32045
        
        # Lunar cycle (synodic month = 29.53059 days)
        days_since_new = (jd - 2451550.1) % 29.53059
        illumination = (1 - abs(days_since_new - 14.765) / 14.765) * 100
        
        if illumination < 12.5:
            phase_name = "New Moon"
        elif illumination < 37.5:
            phase_name = "Waxing Crescent"
        elif illumination < 62.5:
            phase_name = "First Quarter"
        elif illumination < 87.5:
            phase_name = "Waxing Gibbous"
        elif illumination < 112.5:
            phase_name = "Full Moon"
        elif illumination < 137.5:
            phase_name = "Waning Gibbous"
        elif illumination < 162.5:
            phase_name = "Last Quarter"
        else:
            phase_name = "Waning Crescent"
        
        return {
            "name": phase_name,
            "illumination": round(illumination, 1),
            "days_since_new": round(days_since_new, 1)
        }

    @staticmethod
    def _convert_western_signal(signal: str, confidence: int) -> Dict:
        """Конвертация western сигнала в унифицированный формат"""
        score_map = {
            "STRONG_BULLISH": 100,
            "BULLISH": 70,
            "NEUTRAL": 50,
            "BEARISH": 30,
            "STRONG_BEARISH": 0
        }
        return {
            "signal": signal,
            "score": score_map.get(signal, 50),
            "confidence": confidence
        }

    @staticmethod
    def _convert_vedic_signal(signal: str, confidence: int) -> Dict:
        """Конвертация vedic сигнала в унифицированный формат"""
        return FinancialAstrologer._convert_western_signal(signal, confidence)

    @staticmethod
    def _moon_phase_signal(phase: Dict) -> Dict:
        """Сигнал на основе фазы Луны"""
        bullish_phases = ["Waxing Crescent", "First Quarter", "Waxing Gibbous"]
        bearish_phases = ["Waning Gibbous", "Last Quarter", "Waning Crescent"]
        
        illumination = phase["illumination"]
        
        # New Moon и Full Moon имеют особое значение
        if phase["name"] == "New Moon":
            score = 60  # Начало нового цикла — хороший момент для входа
            signal = "BULLISH"
        elif phase["name"] == "Full Moon":
            score = 40  # Фиксация прибыли
            signal = "BEARISH"
        elif phase["name"] in bullish_phases:
            score = 65
            signal = "BULLISH"
        elif phase["name"] in bearish_phases:
            score = 35
            signal = "BEARISH"
        else:
            score = 50
            signal = "NEUTRAL"
        
        return {"signal": signal, "score": score, "confidence": 60}

    @staticmethod
    def _score_to_signal(score: float) -> str:
        """Конвертация weighted score в signal"""
        if score >= 75:
            return "STRONG_BULLISH"
        elif score >= 60:
            return "BULLISH"
        elif score >= 45:
            return "NEUTRAL"
        elif score >= 30:
            return "BEARISH"
        else:
            return "STRONG_BEARISH"

    @staticmethod
    def _format_interpretation(western, vedic, moon, final_signal) -> str:
        """Форматирование для человека"""
        lines = ["=" * 50]
        lines.append("ASTRONOMICAL ASTROLOGY ANALYSIS")
        lines.append("=" * 50)
        
        lines.append("\n📊 WESTERN (Lilly):")
        lines.append(f"   Signal: {western['signal']}")
        lines.append(f"   Moon in: {western['dignities'].get('Moon', {}).get('sign', 'N/A')}")
        lines.append(f"   Aspects: {len(western.get('aspects', []))} found")
        
        lines.append("\n📊 VEDIC (Muhurta):")
        lines.append(f"   Signal: {vedic['signal']}")
        lines.append(f"   Nakshatra: {vedic['nakshatra']}")
        lines.append(f"   Choghadiya: {vedic['choghadiya']}")
        lines.append(f"   Muhurta Score: {vedic['muhurta_score']}")
        
        lines.append("\n🌙 MOON PHASE:")
        lines.append(f"   {moon['name']} ({moon['illumination']}% illumination)")
        
        lines.append(f"\n{'=' * 50}")
        lines.append(f"FINAL SIGNAL: {final_signal}")
        lines.append("=" * 50)
        
        return "\n".join(lines)

    @staticmethod
    def _get_trading_advice(signal: str, confidence: int, vedic: Dict) -> Dict:
        """Генерация торговых рекомендаций"""
        if signal == "STRONG_BULLISH" and confidence >= 70:
            action = "CONSIDER_LONG"
            risk = "2% max"
            position_size = "15-20%"
        elif signal == "BULLISH" and confidence >= 60:
            action = "CAUTIOUS_LONG"
            risk = "1.5% max"
            position_size = "10-15%"
        elif signal == "NEUTRAL":
            action = "WAIT_AND_WATCH"
            risk = "1% max"
            position_size = "5-10%"
        elif signal == "BEARISH" and confidence >= 60:
            action = "CAUTIOUS_SHORT"
            risk = "1.5% max"
            position_size = "10-15%"
        elif signal == "STRONG_BEARISH" and confidence >= 70:
            action = "CONSIDER_SHORT"
            risk = "2% max"
            position_size = "15-20%"
        else:
            action = "NO_POSITION"
            risk = "0%"
            position_size = "0%"
        
        # Добавить Vedic предупреждения
        warnings = []
        if vedic.get("choghadiya") in ["Kaal", "Rog", "Ari"]:
            warnings.append(f"Avoid: Choghadiya {vedic['choghadiya']}")
        if vedic.get("nakshatra") in ["Mula", "Ardra", "Ashlesha"]:
            warnings.append(f"Caution: Nakshatra {vedic['nakshatra']}")
        
        return {
            "action": action,
            "risk_per_trade": risk,
            "position_size": position_size,
            "warnings": warnings
        }

    def analyze_with_ephemeris(
        self,
        dt: datetime,
        eph: Dict[str, Any],
        rag_context: Optional[str] = None
    ) -> Dict:
        """
        Analyze using pre-computed ephemeris data from Swiss Ephemeris.
        
        This is the PRIMARY method called by AstroCouncilAgent.
        Ensures all calculations go through swiss_ephemeris.
        
        Args:
            dt: Date/time for the analysis
            eph: Pre-computed ephemeris data from swiss_ephemeris tool
                 Contains: positions, houses, panchanga, choghadiya, etc.
            rag_context: Optional RAG context
            
        Returns:
            Dict with final signal and all components
        """
        # Extract positions from ephemeris result
        positions = {}
        raw_positions = eph.get("positions", {})
        
        for planet, data in raw_positions.items():
            if isinstance(data, dict):
                positions[planet] = data.get("lon", 0)
            else:
                positions[planet] = data
        
        # Also extract from positions_formatted if available
        if not positions and "positions_formatted" in eph:
            for planet, data in eph.get("positions_formatted", {}).items():
                if isinstance(data, dict):
                    positions[planet] = data.get("lon", 0)
                else:
                    positions[planet] = data
        
        # Get panchanga from ephemeris
        panchanga = eph.get("panchanga", {})
        current_choghadiya = eph.get("current_choghadiya", {})
        
        # Call the base analyze method with extracted positions
        result = self.analyze(
            dt=dt,
            positions=positions,
            rag_context=rag_context
        )
        
        # Override vedic components with actual ephemeris data if available
        if panchanga:
            result["components"]["vedic"]["nakshatra"] = panchanga.get("nakshatra", 
                result["components"]["vedic"].get("nakshatra"))
            result["components"]["vedic"]["choghadiya"] = panchanga.get("choghadiya", 
                current_choghadiya.get("type", "Unknown"))
        
        return result
