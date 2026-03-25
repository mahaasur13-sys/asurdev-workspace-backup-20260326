"""
Planning Agent — Central Planning для AgentOrchestra.

Декомпозирует запросы пользователя на подзадачи с учётом доступных агентов.
"""
from __future__ import annotations

import asyncio
import logging
from enum import Enum
from typing import Any

from pydantic import BaseModel


class OrchestrationStrategy(str, Enum):
    """Strategy for executing subtasks."""
    PARALLEL = "parallel"
    SEQUENTIAL = "sequential"
    CONDITIONAL = "conditional"


class SubTask(BaseModel):
    """Sub-task для планирования."""
    id: str
    description: str
    assigned_agent: str
    required_tools: list[str] = []
    priority: int = 5
    expected_output: str = ""
    depends_on: list[str] = []


class Plan(BaseModel):
    """План выполнения."""
    goal: str
    subtasks: list[SubTask]
    orchestration_strategy: OrchestrationStrategy = OrchestrationStrategy.PARALLEL
    estimated_duration_seconds: int = 30
    risk_level: str = "MEDIUM"


class PlanningAgent:
    """
    Центральный Planning Agent.

    Анализирует запрос, выбирает агентов и декомпозирует на подзадачи.
    """

    AGENT_CAPABILITIES: dict[str, list[str]] = {
        "FundamentalAgent": ["earnings", "fundamentals", "valuation"],
        "MacroAgent": ["vix", "dxy", "fed_rate", "macro_indicators"],
        "QuantAgent": ["backtest", "optimization", "ml_models", "pattern_recognition"],
        "PredictorAgent": ["price_prediction", "trend_forecast", "monte_carlo"],
        "OptionsFlowAgent": ["gamma_exposure", "unusual_activity", "squeeze"],
        "SentimentAgent": ["fear_greed", "news", "market_sentiment"],
        "TechnicalAgent": ["rsi", "macd", "bollinger", "patterns", "support_resistance"],
        "BullResearcherAgent": ["bullish_case", "growth_thesis"],
        "BearResearcherAgent": ["bearish_case", "risk_thesis"],
        "RiskAgent": ["risk_assessment", "position_sizing", "volatility"],
    }

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

    async def create_plan(
        self, user_query: str, context: dict[str, Any] | None = None
    ) -> Plan:
        """
        Create execution plan from user query.

        Args:
            user_query: The user's request
            context: Additional context (symbol, timeframe, etc.)
        """
        context = context or {}
        symbol = context.get("symbol", "BTC")
        timeframe = context.get("timeframe", "1d")

        task_type = self._classify_query(user_query)
        subtasks = self._create_subtasks(task_type, symbol, timeframe)
        strategy = self._determine_strategy(subtasks)

        return Plan(
            goal=user_query,
            subtasks=subtasks,
            orchestration_strategy=strategy,
            estimated_duration_seconds=self._estimate_duration(strategy, len(subtasks)),
            risk_level=self._assess_risk(subtasks),
        )

    def _classify_query(self, query: str) -> str:
        """Classify query type."""
        q = query.lower()
        if any(w in q for w in ["short", "sell"]):
            return "SHORT_SIGNAL"
        if any(w in q for w in ["long", "buy"]):
            return "LONG_SIGNAL"
        if any(w in q for w in ["predict", "forecast", "прогноз"]):
            return "PREDICTION"
        if any(w in q for w in ["Muhurta", "election", "muhurta"]):
            return "ELECTION"
        return "FULL_ANALYSIS"

    def _create_subtasks(self, task_type: str, symbol: str, timeframe: str) -> list[SubTask]:
        """Create subtasks based on task type."""
        subtasks = [
            SubTask(
                id="astro",
                description=f"Get planetary positions and Panchanga for {symbol}",
                assigned_agent="AstroCouncilAgent",
                required_tools=["swiss_ephemeris"],
                priority=1,
                expected_output="planetary_positions, nakshatra, choghadiya",
            ),
            SubTask(
                id="fundamental",
                description=f"Fundamental analysis for {symbol}",
                assigned_agent="FundamentalAgent",
                required_tools=["binance"],
                priority=2,
                expected_output="fundamentals, on_chain_data",
            ),
            SubTask(
                id="macro",
                description=f"Macroeconomic analysis for {symbol}",
                assigned_agent="MacroAgent",
                required_tools=["fred", "polygon.io"],
                priority=3,
                expected_output="macro_indicators, vix, dxy",
            ),
        ]

        if task_type in ("LONG_SIGNAL", "SHORT_SIGNAL", "FULL_ANALYSIS"):
            subtasks.extend([
                SubTask(
                    id="quant",
                    description=f"Quantitative analysis for {symbol}",
                    assigned_agent="QuantAgent",
                    required_tools=["binance", "polygon.io"],
                    priority=4,
                    expected_output="ml_prediction, backtest_results",
                ),
                SubTask(
                    id="options_flow",
                    description=f"Options flow analysis for {symbol}",
                    assigned_agent="OptionsFlowAgent",
                    required_tools=["polygon.io"],
                    priority=5,
                    expected_output="gamma_exposure, unusual_activity",
                ),
                SubTask(
                    id="sentiment",
                    description=f"Market sentiment for {symbol}",
                    assigned_agent="SentimentAgent",
                    required_tools=["fred"],
                    priority=6,
                    expected_output="fear_greed_index, market_sentiment",
                ),
                SubTask(
                    id="technical",
                    description=f"Technical analysis for {symbol}",
                    assigned_agent="TechnicalAgent",
                    required_tools=["binance"],
                    priority=7,
                    expected_output="rsi, macd, bollinger",
                ),
                SubTask(
                    id="risk",
                    description=f"Risk assessment for {symbol}",
                    assigned_agent="RiskAgent",
                    required_tools=[],
                    priority=8,
                    expected_output="risk_assessment, position_size",
                    depends_on=["technical", "quant"],
                ),
            ])

        if task_type == "PREDICTION":
            subtasks.append(
                SubTask(
                    id="predictor",
                    description=f"ML price prediction for {symbol}",
                    assigned_agent="PredictorAgent",
                    required_tools=["binance"],
                    priority=2,
                    expected_output="price_prediction, confidence_interval",
                )
            )

        return sorted(subtasks, key=lambda x: x.priority)

    def _determine_strategy(self, subtasks: list[SubTask]) -> OrchestrationStrategy:
        """Determine execution strategy."""
        has_dependencies = any(t.depends_on for t in subtasks)
        if has_dependencies:
            return OrchestrationStrategy.CONDITIONAL
        if len(subtasks) > 5:
            return OrchestrationStrategy.PARALLEL
        return OrchestrationStrategy.PARALLEL

    def _estimate_duration(self, strategy: OrchestrationStrategy, num_tasks: int) -> int:
        """Estimate execution duration in seconds."""
        base = 3
        if strategy == OrchestrationStrategy.PARALLEL:
            return base * 2
        return base * num_tasks

    def _assess_risk(self, subtasks: list[SubTask]) -> str:
        """Assess risk level of the plan."""
        high_risk = {"RiskAgent", "OptionsFlowAgent"}
        has_high = any(t.assigned_agent in high_risk for t in subtasks)
        if has_high or len(subtasks) > 7:
            return "HIGH"
        if len(subtasks) > 4:
            return "MEDIUM"
        return "LOW"
