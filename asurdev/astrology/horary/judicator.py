"""
LillyJudicator — Render verdict based on Lilly's Christian Astrology.
Based on William Lilly "Christian Astrology" (1647), Chapter 17: Of Judgement upon the Question
"""

from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum

from .chart import HoraryChart, Significator
from .parser import QuestionParser, QuestionType


class Verdict(str, Enum):
    """Horary verdict options."""
    STRONG_YES = "STRONG_YES"      # Very strong indication to act
    YES = "YES"                    # Favorable indication
    NEUTRAL = "NEUTRAL"           # Indecisive, wait
    NO = "NO"                     # Unfavorable indication
    STRONG_NO = "STRONG_NO"       # Very strong indication not to act
    ASK_LATER = "ASK_LATER"       # Chart not ready, ask again


@dataclass
class Judgement:
    """Complete judgement for a horary question."""
    verdict: Verdict
    confidence: int  # 0-100
    summary: str
    reasons_for: List[str]
    reasons_against: List[str]
    key_aspects: List[Dict]
    dignities: Dict[str, int]
    recommendation: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "verdict": self.verdict.value,
            "confidence": self.confidence,
            "summary": self.summary,
            "reasons_for": self.reasons_for,
            "reasons_against": self.reasons_against,
            "key_aspects": self.key_aspects,
            "dignities": self.dignities,
            "recommendation": self.recommendation,
        }


class LillyJudicator:
    """
    Judge a horary chart based on Lilly's rules.
    
    Key principles from Chapter 17:
    1. Consider the Quesitor's significator (planet representing the asker)
    2. Consider the Quesited's significator (planet representing what is asked about)
    3. Judge by their dignity, accidental strength, and aspects
    4. The one with better dignity and stronger aspects wins
    5. Always consider the 5th and 8th houses for speculation
    """
    
    def __init__(self, chart: HoraryChart, parser: QuestionParser):
        self.chart = chart
        self.parser = parser
        self.mapping = parser.get_significator_mapping()
    
    def judge(self) -> Judgement:
        """Render the final judgement."""
        verdict, confidence = self._determine_verdict()
        reasons_for = self._get_reasons_for()
        reasons_against = self._get_reasons_against()
        key_aspects = self._analyze_key_aspects()
        dignities = self._analyze_dignities()
        summary = self._create_summary(verdict, confidence, reasons_for, reasons_against)
        recommendation = self._create_recommendation(verdict)
        
        return Judgement(
            verdict=verdict,
            confidence=confidence,
            summary=summary,
            reasons_for=reasons_for,
            reasons_against=reasons_against,
            key_aspects=key_aspects,
            dignities=dignities,
            recommendation=recommendation,
        )
    
    def _determine_verdict(self) -> Tuple[Verdict, int]:
        """Determine the overall verdict based on chart analysis."""
        # Get significators
        quesitor = self._get_quesitor_significator()
        thing = self._get_thing_significator()
        counsel = self._get_counsel_significator()
        
        if not quesitor or not thing:
            return Verdict.NEUTRAL, 50
        
        # Calculate scores
        quesitor_score = quesitor.total_score
        thing_score = thing.total_score
        
        # Check aspects between significators
        aspect_bonus = self._calculate_aspect_bonus(quesitor, thing)
        counsel_bonus = self._calculate_counsel_bonus(counsel, thing)
        
        # Final score calculation
        # Weighted: dignities 40%, aspects 40%, counsel 20%
        final_score = (
            (quesitor_score * 0.2) +
            (thing_score * 0.3) +
            (aspect_bonus * 0.3) +
            (counsel_bonus * 0.2)
        )
        
        # Normalize to 0-100
        normalized = max(0, min(100, 50 + final_score * 5))
        
        # Determine verdict
        if normalized >= 80:
            return Verdict.STRONG_YES, normalized
        elif normalized >= 65:
            return Verdict.YES, normalized
        elif normalized >= 55:
            return Verdict.NEUTRAL, normalized
        elif normalized >= 40:
            return Verdict.NO, 100 - normalized
        else:
            return Verdict.STRONG_NO, 100 - normalized
    
    def _get_quesitor_significator(self) -> Optional[Significator]:
        """Get the quesitor's significator."""
        planet = self.mapping.quesitor_planet
        try:
            return self.chart.get_significator(planet)
        except ValueError:
            return None
    
    def _get_thing_significator(self) -> Optional[Significator]:
        """Get the significator for what is asked about."""
        # For financial questions, use Jupiter as money significator
        # or the planet associated with the asset class
        planet = self.parser.get_asset_significator(
            self.parser.symbol,
            self.parser.asset_class
        )
        try:
            return self.chart.get_significator(planet)
        except ValueError:
            return None
    
    def _get_counsel_significator(self) -> Optional[Significator]:
        """Get the significator for counsel/action."""
        planet = self.mapping.counsel_planet
        try:
            return self.chart.get_significator(planet)
        except ValueError:
            return None
    
    def _calculate_aspect_bonus(self, quesitor: Significator, thing: Significator) -> float:
        """Calculate aspect score between significators."""
        score = 0.0
        
        for asp in quesitor.aspects_to_other:
            if asp["to"] == thing.planet.name:
                if asp["nature"] == "good":
                    score += 2.0 - (asp["orb"] / 5)  # Good aspect bonus
                elif asp["nature"] == "bad":
                    score -= 2.0 - (asp["orb"] / 5)  # Bad aspect penalty
        
        # Trine is better than sextile
        for asp in quesitor.aspects_to_other:
            if asp["to"] == thing.planet.name:
                if asp["aspect"] == "trine":
                    score += 1.0
                elif asp["aspect"] == "sextile":
                    score += 0.5
                elif asp["aspect"] == "square":
                    score -= 1.0
                elif asp["aspect"] == "opposition":
                    score -= 1.5
        
        # Conjunction is powerful
        for asp in quesitor.aspects_to_other:
            if asp["to"] == thing.planet.name:
                if asp["aspect"] == "conjunction":
                    score += 2.0
        
        return score
    
    def _calculate_counsel_bonus(self, counsel: Optional[Significator], 
                                  thing: Significator) -> float:
        """Calculate if counsel planet is well positioned."""
        if not counsel:
            return 0.0
        
        score = counsel.total_score / 10.0
        
        # Check if counsel aspects the thing favorably
        for asp in counsel.aspects_to_other:
            if asp["to"] == thing.planet.name:
                if asp["nature"] == "good":
                    score += 1.0
        
        return score
    
    def _get_reasons_for(self) -> List[str]:
        """Get reasons supporting a positive outcome."""
        reasons = []
        
        quesitor = self._get_quesitor_significator()
        thing = self._get_thing_significator()
        
        if not quesitor or not thing:
            return ["Chart analysis incomplete"]
        
        # Check dignities
        if quesitor.dignity_score > 3:
            reasons.append(f"Quesitor ({quesitor.planet.name}) in strong dignity")
        
        if thing.dignity_score > 3:
            reasons.append(f"Thing ({thing.planet.name}) well dignified")
        
        # Check aspects
        for asp in quesitor.aspects_to_other:
            if asp["to"] == thing.planet.name and asp["nature"] == "good":
                reasons.append(f"Benefic {asp['aspect']} between significators")
        
        # Check accidental dignities
        if quesitor.planet.is_orient:
            reasons.append("Quesitor oriental (rising before Sun) - active")
        
        if thing.planet.is_exalted:
            reasons.append(f"{thing.planet.name} in exaltation")
        
        # Check house placement
        if thing.house in [1, 5, 10, 11]:
            reasons.append(f"Thing in favorable house ({HOUSE_NAMES.get(thing.house, thing.house)})")
        
        return reasons if reasons else ["No strong positive indications"]
    
    def _get_reasons_against(self) -> List[str]:
        """Get reasons against a positive outcome."""
        reasons = []
        
        quesitor = self._get_quesitor_significator()
        thing = self._get_thing_significator()
        
        if not quesitor or not thing:
            return []
        
        # Check debilities
        if quesitor.dignity_score < -2:
            reasons.append(f"Quesitor ({quesitor.planet.name}) in weak dignity")
        
        if thing.dignity_score < -2:
            reasons.append(f"Thing ({thing.planet.name}) in fall or detriment")
        
        # Check bad aspects
        for asp in quesitor.aspects_to_other:
            if asp["to"] == thing.planet.name and asp["nature"] == "bad":
                reasons.append(f"Malefic {asp['aspect']} between significators")
        
        # Check accidental debilities
        if quesitor.planet.is_fall:
            reasons.append(f"{quesitor.planet.name} in fall")
        
        # Check house placement
        if thing.house in [6, 8, 12]:
            reasons.append(f"Thing in challenging house ({HOUSE_NAMES.get(thing.house, thing.house)})")
        
        return reasons if reasons else ["No strong negative indications"]
    
    def _analyze_key_aspects(self) -> List[Dict]:
        """Get the most important aspects in the chart."""
        key_aspects = []
        
        quesitor = self._get_quesitor_significator()
        thing = self._get_thing_significator()
        
        if quesitor and thing:
            for asp in quesitor.aspects_to_other:
                if asp["to"] == thing.planet.name:
                    key_aspects.append({
                        "from": quesitor.planet.name,
                        "to": asp["to"],
                        "aspect": asp["aspect"],
                        "nature": asp["nature"],
                        "orb": asp["orb"],
                        "significance": "KEY" if asp["orb"] < 3 else "minor"
                    })
        
        return key_aspects
    
    def _analyze_dignities(self) -> Dict[str, int]:
        """Get dignity analysis for all planets."""
        dignities = {}
        for name, pos in self.chart.positions.items():
            score, _ = EssentialDignities.get_dignity_score(
                name, pos.sign, self.chart.is_day
            )
            dignities[name] = score
        return dignities
    
    def _create_summary(self, verdict: Verdict, confidence: int,
                        reasons_for: List[str], reasons_against: List[str]) -> str:
        """Create a human-readable summary."""
        verdict_text = {
            Verdict.STRONG_YES: "STRONGLY FAVORABLE",
            Verdict.YES: "FAVORABLE",
            Verdict.NEUTRAL: "UNCERTAIN",
            Verdict.NO: "UNFAVORABLE",
            Verdict.STRONG_NO: "STRONGLY UNFAVORABLE",
            Verdict.ASK_LATER: "ASK AGAIN LATER",
        }
        
        return (
            f"Verdict: {verdict_text.get(verdict, 'UNKNOWN')}\n"
            f"Confidence: {confidence}%\n"
            f"Reasons for: {len(reasons_for)}\n"
            f"Reasons against: {len(reasons_against)}"
        )
    
    def _create_recommendation(self, verdict: Verdict) -> str:
        """Create actionable recommendation."""
        recommendations = {
            Verdict.STRONG_YES: "ACT NOW - Very strong indication. Execute with confidence.",
            Verdict.YES: "Proceed - Favorable conditions. Consider position sizing.",
            Verdict.NEUTRAL: "WAIT - Uncertain. Seek more confirmation or ask again.",
            Verdict.NO: "Avoid - Unfavorable conditions. Consider opposite action.",
            Verdict.STRONG_NO: "DO NOT ACT - Very strong negative indication.",
            Verdict.ASK_LATER: "Chart unclear - Wait for better conditions to ask.",
        }
        return recommendations.get(verdict, "Unable to determine.")


# Helper for house names
HOUSE_NAMES = {
    1: "1st (Self)",
    2: "2nd (Money)",
    3: "3rd (Communication)",
    4: "4th (Home)",
    5: "5th (Speculation)",
    6: "6th (Work)",
    7: "7th (Partnership)",
    8: "8th (Shared Resources)",
    9: "9th (Expansion)",
    10: "10th (Career)",
    11: "11th (Gains)",
    12: "12th (Hidden Matters)",
}


# Need to import EssentialDignities
from astrology.core import EssentialDignities
