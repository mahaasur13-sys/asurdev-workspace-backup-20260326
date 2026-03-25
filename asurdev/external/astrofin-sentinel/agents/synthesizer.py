"""
Synthesizer Agent ("Board of Directors") for AstroFin Sentinel

Combines reports from Technical, Fundamental, and Astrological analysts
into a unified recommendation.
"""

import json
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional

from agents.technical_analyst import TechnicalReport
from agents.fundamental_analyst import FundamentalReport
from agents.astrologer import AstroReport


@dataclass
class SynthesizerReport:
    """Output from Synthesizer Agent - final recommendation."""
    summary: str
    scenarios: dict  # bull, base, bear
    board_opinions: dict
    weighted_score: dict
    recommendation: dict  # action, position_size, entry, stop_loss, targets
    muhurta_time: str
    risk_warnings: list
    timestamp: str
    symbol: str = ""


class SynthesizerAgent:
    """
    Synthesizer Agent - "Board of Directors".
    
    Takes reports from all three analysts and synthesizes
    a final recommendation using weighted scoring.
    """
    
    # Default weights — астрология снижена до 20%
    DEFAULT_WEIGHTS = {
        "technical": 0.40,
        "fundamental": 0.40,
        "astrological": 0.20
    }
    
    # Astro nuance settings
    ASTRO_UNDEFINED_PENALTY = 0.5
    ASTRO_MIN_CONFIDENCE = 0.30
    ASTRO_MAX_RELATIVE_CONF = 0.80
    
    def __init__(self, weights: dict = None, astro_nuance: dict = None):
        """
        Initialize Synthesizer.
        
        Args:
            weights: Custom weights for each analyst. Must sum to 1.0
            astro_nuance: Optional dict with astrology nuance settings
        """
        self.weights = weights or self.DEFAULT_WEIGHTS
        
        # Override astro nuance settings if provided
        if astro_nuance:
            self.astro_nuance = astro_nuance
        else:
            self.astro_nuance = {
                "undefined_penalty": self.ASTRO_UNDEFINED_PENALTY,
                "min_confidence": self.ASTRO_MIN_CONFIDENCE,
                "max_relative_confidence": self.ASTRO_MAX_RELATIVE_CONF
            }
        
        # Validate weights sum to 1 (with floating point tolerance)
        total = sum(self.weights.values())
        if abs(round(total, 2) - 1.0) > 0.01:
            raise ValueError(f"Weights must sum to 1.0, got {total}")
    
    def synthesize(self, technical: TechnicalReport,
                   fundamental: FundamentalReport,
                   astrological: AstroReport,
                   symbol: str = "") -> SynthesizerReport:
        """
        Synthesize final recommendation from all reports.
        
        Args:
            technical: Technical Analyst report
            fundamental: Fundamental Analyst report
            astrological: Vedic Astrologer report
            symbol: Trading pair symbol
            
        Returns:
            SynthesizerReport with final recommendation
        """
        # Calculate scores
        tech_score = self._signal_to_score(technical.signal, technical.confidence)
        fund_score = self._verdict_to_score(fundamental.verdict, fundamental.strength)
        astro_score = self._signal_to_score(astrological.signal, astrological.confidence)
        
        # Calculate weighted score
        weighted = {
            "technical": tech_score * self.weights["technical"],
            "fundamental": fund_score * self.weights["fundamental"],
            "astrological": astro_score * self.weights["astrological"]
        }
        composite = sum(weighted.values())
        
        # Generate scenarios
        scenarios = self._generate_scenarios(
            technical, fundamental, astrological, composite
        )
        
        # Generate board opinions with full astro details
        board_opinions = {
            "technical": {
                "opinion": technical.reasoning,
                "signal": technical.signal,
                "confidence": technical.confidence,
                "levels": technical.levels
            },
            "fundamental": {
                "opinion": fundamental.reasoning,
                "verdict": fundamental.verdict,
                "strength": fundamental.strength,
                "factors": fundamental.factors[:3],
                "risk_factors": fundamental.risk_factors[:2]
            },
            "astrological": {
                "opinion": astrological.reasoning,
                "signal": astrological.signal,
                "confidence": astrological.confidence,
                "muhurta": astrological.muhurta,
                # NEW: Pass full astrologer details
                "planet_strength": astrological.planet_strength or {},
                "nakshatra_influence": getattr(astrological, 'nakshatra_influence', ''),
                "moon_phase": getattr(astrological, 'moon_phase', ''),
                "eclipse_risk": getattr(astrological, 'eclipse_risk', False),
                "planetary_yoga": astrological.planetary_yoga,
                "transits": astrological.transits,
                "favorable": astrological.favorable,
                "unfavorable": astrological.unfavorable,
                "dasha": astrological.dasha
            }
        }
        
        # Generate recommendation
        recommendation = self._generate_recommendation(
            technical, fundamental, composite
        )
        
        # Generate summary
        summary = self._generate_summary(
            technical, fundamental, astrological, composite
        )
        
        # Extract best time
        muhurta_time = astrological.muhurta.get("best_time", "Уточните у астролога")
        
        # Risk warnings
        risk_warnings = self._generate_risk_warnings(
            technical, fundamental, astrological
        )
        
        return SynthesizerReport(
            summary=summary,
            scenarios=scenarios,
            board_opinions=board_opinions,
            weighted_score={
                "technical": round(tech_score, 3),
                "fundamental": round(fund_score, 3),
                "astrological": round(astro_score, 3),
                "weights": self.weights,
                "composite": round(composite, 3)
            },
            recommendation=recommendation,
            muhurta_time=muhurta_time,
            risk_warnings=risk_warnings,
            timestamp=datetime.now().isoformat(),
            symbol=symbol
        )
    
    def _signal_to_score(self, signal: str, confidence: float) -> float:
        """Convert signal to numeric score."""
        signal_scores = {
            "BUY": 0.75,
            "STRONG_BUY": 0.85,
            "SELL": 0.25,
            "STRONG_SELL": 0.15,
            "NEUTRAL": 0.50,
            "HOLD": 0.50,
            "WAIT": 0.35
        }
        
        base = signal_scores.get(signal.upper(), 0.50)
        
        # Blend with confidence
        return base * 0.7 + confidence * 0.3
    
    def _verdict_to_score(self, verdict: str, strength: float) -> float:
        """Convert fundamental verdict to numeric score."""
        verdict_scores = {
            "STRONG_BUY": 0.85,
            "BUY": 0.70,
            "NEUTRAL": 0.50,
            "SELL": 0.30,
            "STRONG_SELL": 0.15
        }
        
        base = verdict_scores.get(verdict.upper(), 0.50)
        return base * 0.7 + strength * 0.3
    
    def _generate_scenarios(self, tech: TechnicalReport, fund: FundamentalReport,
                           astro: AstroReport, composite: float) -> dict:
        """Generate Bull/Base/Bear scenarios."""
        # Get entry from technical levels
        entry_str = tech.levels.get("entry", "0")
        if isinstance(entry_str, str):
            entry_str = entry_str.split(" - ")[0].replace(",", "")
        try:
            entry = float(entry_str) if entry_str else 0
        except (ValueError, AttributeError):
            entry = 0
        
        if entry == 0:
            entry = tech.indicators.get("current_price", 100000) if tech.indicators else 100000
        
        # Calculate scenarios based on composite score
        if composite >= 0.65:
            bull_prob, base_prob, bear_prob = 0.40, 0.45, 0.15
            target_mult = 1.10
            stop_mult = 0.97
        elif composite >= 0.50:
            bull_prob, base_prob, bear_prob = 0.30, 0.50, 0.20
            target_mult = 1.06
            stop_mult = 0.96
        else:
            bull_prob, base_prob, bear_prob = 0.20, 0.45, 0.35
            target_mult = 1.04
            stop_mult = 0.95
        
        return {
            "bull": {
                "probability": bull_prob,
                "entry": entry,
                "target": round(entry * target_mult * 1.05, 2),
                "stop_loss": round(entry * 0.97, 2),
                "risk_reward": round((target_mult * 1.05 - 1) / 0.03, 1)
            },
            "base": {
                "probability": base_prob,
                "entry": entry,
                "target": round(entry * target_mult, 2),
                "stop_loss": round(entry * 0.975, 2),
                "risk_reward": round((target_mult - 1) / 0.025, 1)
            },
            "bear": {
                "probability": bear_prob,
                "entry": entry,
                "target": round(entry * 0.93, 2),
                "stop_loss": round(entry * 1.02, 2),
                "risk_reward": 0.5
            }
        }
    
    def _generate_recommendation(self, tech: TechnicalReport,
                                fund: FundamentalReport,
                                composite: float) -> dict:
        """Generate final trading recommendation."""
        # Action based on composite score
        if composite >= 0.65:
            action = "BUY"
            position_pct = 10
        elif composite >= 0.55:
            action = "HOLD + PREPARE TO BUY"
            position_pct = 5
        elif composite >= 0.45:
            action = "HOLD"
            position_pct = 0
        elif composite >= 0.35:
            action = "REDUCE"
            position_pct = -5
        else:
            action = "SELL"
            position_pct = -10
        
        # Get levels from technical
        entry = tech.levels.get("entry", "market")
        stop_loss = tech.levels.get("stop_loss", "установите стоп")
        
        return {
            "action": action,
            "position_size": f"{position_pct}% от депозита",
            "entry_zone": entry,
            "stop_loss": stop_loss,
            "targets": {
                "tp1": tech.levels.get("take_profit_1", ""),
                "tp2": tech.levels.get("take_profit_2", ""),
                "tp3": tech.levels.get("take_profit_3", "")
            },
            "timeframe": "SHORT-TERM (1-2 недели)"
        }
    
    def _generate_summary(self, tech: TechnicalReport,
                         fund: FundamentalReport,
                         astro: AstroReport,
                         composite: float) -> str:
        """Generate executive summary."""
        # Count consensus
        signals = [tech.signal, fund.verdict, astro.signal]
        buys = sum(1 for s in signals if s in ["BUY", "STRONG_BUY"])
        sells = sum(1 for s in signals if s in ["SELL", "STRONG_SELL"])
        
        if buys >= 2:
            direction = "рекомендует покупку"
        elif sells >= 2:
            direction = "рекомендует продажу"
        else:
            direction = "рекомендует удержание"
        
        consensus = "консенсус" if buys == 3 or sells == 3 else "большинство"
        
        summary = f"Совет директоров ({consensus}) {direction}. "
        summary += f"Композитный скор: {composite:.2f}/1.00. "
        summary += f"Технически: {tech.signal} ({tech.confidence:.0%}), "
        summary += f"фундаментально: {fund.verdict}, "
        summary += f"астрологически: {astro.signal}."
        
        return summary
    
    def _generate_risk_warnings(self, tech: TechnicalReport,
                               fund: FundamentalReport,
                               astro: AstroReport) -> list:
        """Generate risk warnings."""
        warnings = []
        
        # Technical risks
        if tech.indicators.get("volatility") == "HIGH":
            warnings.append("⚠️ Высокая волатильность — возможны резкие движения")
        
        if tech.signal in ["SELL", "STRONG_SELL"]:
            warnings.append("⚠️ Технические индикаторы указывают на слабость")
        
        # Fundamental risks
        if fund.risk_factors:
            for risk in fund.risk_factors[:2]:
                warnings.append(f"⚠️ {risk['risk']}")
        
        # Astrological warnings
        if astro.muhurta.get("overall") in ["UNFAVORABLE", "HIGHLY_UNFAVORABLE"]:
            warnings.append("⚠️ Астрологически неблагоприятное время")
        
        # General warnings
        warnings.append("🚫 Это НЕ финансовая рекомендация. Принимайте решения самостоятельно.")
        warnings.append("🚫 Прошлые результаты не гарантируют будущих.")
        
        return warnings[:5]  # Limit to 5 warnings
    
    def to_markdown(self, report: SynthesizerReport) -> str:
        """Convert report to formatted markdown with full agent details."""
        md = "# 🎯 AstroFin Sentinel — Board Report\n\n"
        md += f"## Резюме\n{report.summary}\n\n"
        
        # Scenarios table
        md += "## 📊 Scenarios\n\n"
        md += "| Scenario | Probability | Target | Stop-Loss | R/R |\n"
        md += "|----------|-------------|--------|-----------|-----|\n"
        for name, data in report.scenarios.items():
            md += f"| **{name.capitalize()}** | {data['probability']*100:.0f}% | "
            md += f"${data['target']:.2f} | ${data['stop_loss']:.2f} | "
            md += f"1:{data['risk_reward']:.1f} |\n"
        md += "\n"
        
        # =============================================
        # DETAILED AGENT REPORTS
        # =============================================
        md += "## 🗣️ Board Opinions (Детальный разбор)\n\n"
        
        # ---- TECHNICAL ANALYST ----
        md += "### 💹 Technical Analyst\n"
        tech = report.board_opinions["technical"]
        md += f"> {tech['opinion']}\n\n"
        md += f"**Signal:** {tech['signal']} | **Confidence:** {tech['confidence']:.0%}\n\n"
        md += "**Ключевые уровни:**\n"
        for level_name, level_value in tech.get("levels", {}).items():
            if level_value:
                md += f"- {level_name.replace('_', ' ').title()}: `{level_value}`\n"
        md += "\n"
        
        # ---- FUNDAMENTAL ANALYST ----
        md += "### 📈 Fundamental Analyst\n"
        fund = report.board_opinions["fundamental"]
        md += f"> {fund['opinion']}\n\n"
        md += f"**Verdict:** {fund['verdict']} | **Strength:** {fund['strength']:.0%}\n\n"
        
        if fund.get("factors"):
            md += "**Фундаментальные факторы:**\n"
            for factor in fund["factors"]:
                emoji = "🟢" if factor.get("type") == "positive" else "🔴"
                impact_emoji = "🔴" if factor.get("impact") == "HIGH" else ("🟡" if factor.get("impact") == "MEDIUM" else "⚪")
                md += f"- {emoji} {factor.get('factor', '')} [{impact_emoji} {factor.get('impact', 'LOW')}]\n"
            md += "\n"
        
        if fund.get("risk_factors"):
            md += "**Риск-факторы:**\n"
            for risk in fund["risk_factors"]:
                severity_emoji = "🔴" if risk.get("severity") == "HIGH" else ("🟡" if risk.get("severity") == "MEDIUM" else "⚪")
                md += f"- ⚠️ {risk.get('risk', '')} [{severity_emoji} {risk.get('severity', 'LOW')}]\n"
            md += "\n"
        
        # ---- ASTROLOGER ----
        md += "### 🔮 Vedic Astrologer\n"
        astro = report.board_opinions["astrological"]
        md += f"> {astro['opinion']}\n\n"
        md += f"**Signal:** {astro['signal']} | **Confidence:** {astro['confidence']:.0%}\n\n"
        
        muhurta = astro.get("muhurta", {})
        md += f"**Muhurta:** {muhurta.get('overall', 'NEUTRAL')}\n"
        if muhurta.get("best_time"):
            md += f"**Лучшее время:** {muhurta['best_time']}\n"
        if muhurta.get("worst_time"):
            md += f"**Худшее время:** {muhurta['worst_time']}\n"
        if muhurta.get("reasoning"):
            md += f"** Reasoning:** {muhurta['reasoning']}\n"
        md += "\n"
        
        # NEW: Astro nuance details
        astro_report = getattr(report, 'astrologer_details', None)
        if astro_report:
            # Planet strength
            if astro_report.get("planet_strength"):
                md += "**Сила планет:**\n"
                for planet, strength in astro_report["planet_strength"].items():
                    if strength == "exalted":
                        md += f"- {planet}: ✱ экзальтация\n"
                    elif strength == "fallen":
                        md += f"- {planet}: ⚠️ падение\n"
                    else:
                        md += f"- {planet}: норма\n"
                md += "\n"
            
            # Nakshatra
            if astro_report.get("nakshatra_influence"):
                md += f"**Накшатра:** {astro_report['nakshatra_influence']}\n\n"
            
            # Moon phase
            if astro_report.get("moon_phase") and astro_report.get("moon_phase") != "Не определено":
                md += f"**Лунная фаза:** {astro_report['moon_phase']}\n\n"
            
            # Eclipse risk
            if astro_report.get("eclipse_risk"):
                md += "⚠️ **ВНИМАНИЕ: Риск затмения!**\n\n"
            
            # Yogas
            if astro_report.get("planetary_yoga", {}).get("active"):
                yogas = astro_report["planetary_yoga"]["active"]
                md += f"**Активные йоги:** {', '.join(yogas)}\n\n"
            
            # Transits
            transits = astro_report.get("transits", {})
            if transits.get("benefic"):
                md += f"**Благоприятные транзиты:** {', '.join(transits['benefic'])}\n"
            if transits.get("malefic"):
                md += f"**Осторожно с транзитами:** {', '.join(transits['malefic'])}\n"
            md += "\n"
        
        # Weighted score
        md += "## ⚖️ Weighted Score\n\n"
        ws = report.weighted_score
        md += f"```\n"
        md += f"Technical:    {ws['technical']:.2f} × {ws['weights']['technical']:.2f} = {ws['technical'] * ws['weights']['technical']:.3f}\n"
        md += f"Fundamental:  {ws['fundamental']:.2f} × {ws['weights']['fundamental']:.2f} = {ws['fundamental'] * ws['weights']['fundamental']:.3f}\n"
        md += f"Astrological: {ws['astrological']:.2f} × {ws['weights']['astrological']:.2f} = {ws['astrological'] * ws['weights']['astrological']:.3f}\n"
        md += f"────────────────────────────────────\n"
        md += f"COMPOSITE:    {ws['composite']:.3f} / 1.00\n"
        md += f"```\n\n"
        
        # Recommendation
        md += "## 📋 Final Recommendation\n\n"
        rec = report.recommendation
        md += f"### Action: **{rec['action']}**\n"
        md += f"### Position Size: {rec['position_size']}\n"
        md += f"### Entry Zone: {rec['entry_zone']}\n"
        md += f"### Stop-Loss: {rec['stop_loss']}\n"
        md += f"### Timeframe: {rec['timeframe']}\n\n"
        
        # Muhurta
        md += f"## ⏰ Muhurta (Best Time)\n"
        md += f"**{report.muhurta_time}**\n\n"
        
        # Risk warnings
        md += "## ⚠️ Risk Warnings\n\n"
        for warning in report.risk_warnings:
            md += f"{warning}\n"
        
        md += "\n---\n"
        md += f"*AstroFin Sentinel v2.0 | {report.timestamp}*\n"
        
        return md
    
    def to_dict(self, report: SynthesizerReport) -> dict:
        """Convert report to dictionary."""
        return asdict(report)


# Global instance
_synthesizer_agent = None

def get_synthesizer(weights: dict = None) -> SynthesizerAgent:
    global _synthesizer_agent
    if _synthesizer_agent is None:
        _synthesizer_agent = SynthesizerAgent(weights)
    return _synthesizer_agent
