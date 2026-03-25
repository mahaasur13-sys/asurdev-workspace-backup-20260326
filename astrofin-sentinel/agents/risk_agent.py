"""
RiskAgent — Agent #10 в мультиагентной системе AstroFin Sentinel.

Роль: Управление рисками и позиционированием.
Вычисляет position sizing, stop-loss, risk/reward.

Ключевые данные:
- Position Size (Binance API)
- Stop Loss / Take Profit
- Portfolio Exposure
- Risk/Reward Ratio
"""

from .base import BaseAgent, AgentInput, AgentOutput
import logging

logger = logging.getLogger(__name__)


class RiskAgent(BaseAgent):
    """
    Risk Manager — расчёт рисков и размера позиции.
    
    Ключевые функции:
    1. Position Sizing — размер позиции на основе капитала и риска
    2. Stop Loss / Take Profit — уровни выхода
    3. Risk/Reward Ratio — оценка качества сделки
    4. Portfolio Exposure — управление суммарным риском
    5. Max Drawdown tracking
    """
    
    # Риск-параметры по умолчанию
    DEFAULT_RISK_PER_TRADE = 0.02  # 2% капитала на сделку
    DEFAULT_MAX_PORTFOLIO_RISK = 0.06  # 6% суммарный риск
    
    def __init__(
        self,
        model: str | None = None,
        account_balance: float = 10000.0,
        risk_per_trade: float = DEFAULT_RISK_PER_TRADE,
        max_portfolio_risk: float = DEFAULT_MAX_PORTFOLIO_RISK
    ):
        # Set instance attributes BEFORE calling parent init
        self.account_balance = account_balance
        self.risk_per_trade = risk_per_trade
        self.max_portfolio_risk = max_portfolio_risk
        
        # Build system prompt with actual values
        system_prompt = self._build_system_prompt()
        
        super().__init__(
            name="RiskAgent",
            model=model,
            system_prompt=system_prompt,
        )
    
    def _build_system_prompt(self) -> str:
        """Build system prompt with current instance values."""
        return f"""Ты — эксперт по УПРАВЛЕНИЮ РИСКАМИ в трейдинге.

Твоя специализация:
1. POSITION SIZING — расчёт размера позиции
   - Формула: Position = (Account × Risk%) / (Entry - StopLoss)
2. STOP LOSS / TAKE PROFIT — уровни выхода
3. RISK/REWARD RATIO — оценка качества сделки (минимум 1:2)
4. PORTFOLIO EXPOSURE — суммарный риск портфеля
5. KELLY CRITERION — оптимальный размер позиции

Параметры:
- Account Balance: ${self.account_balance:,.2f}
- Risk Per Trade: {self.risk_per_trade:.1%}
- Max Portfolio Risk: {self.max_portfolio_risk:.1%}

Анализ для symbol с текущей ценой.

Верни строго JSON:

{{
    "recommendation": "buy|sell|hold",
    "confidence": 0.0-1.0,
    "reasoning": "2-4 предложения о рисках",
    "key_factors": [
        "position_size: 0.15 BTC",
        "stop_loss: 65000 (-3.5%)",
        "take_profit: 72000 (+6.5%)",
        "risk_reward: 1:1.86"
    ],
    "warnings": [
        "portfolio_risk_near_limit",
        "high_volatility_zone"
    ],
    "metadata": {{
        "position_size": 0.15,
        "position_value": 10200,
        "stop_loss": 65000,
        "take_profit": 72000,
        "risk_reward_ratio": 1.86,
        "max_loss_amount": 366,
        "max_gain_amount": 680,
        "kelly_percentage": 0.18,
        "portfolio_exposure_pct": 0.045
    }}
}}

Верни ТОЛЬКО валидный JSON без markdown."""
    
    def get_system_prompt(self) -> str:
        return self._build_system_prompt()
    
    async def analyze(self, input_data: AgentInput) -> AgentOutput:
        """Выполняет риск-анализ."""
        logger.info(f"[RiskAgent] Risk analysis for {input_data.symbol}")
        
        extra_context = f"""
## Торговые параметры:

Account Balance: ${self.account_balance:,.2f}
Risk Per Trade: {self.risk_per_trade:.2%}
Max Portfolio Risk: {self.max_portfolio_risk:.2%}

Current Trade:
- Entry Price: ${input_data.price:,.2f}
- Direction: {input_data.action.upper()}
- Current ML Confidence: {input_data.ml_confidence:.2%}

Рассчитай:
1. Optimal position size
2. Stop loss level (защита от убытков)
3. Take profit level (фиксация прибыли)
4. Risk/Reward ratio
5. Is trade within Kelly criterion?
"""
        
        prompt = self._build_prompt(input_data, extra_context)
        result = await self._call_llm(prompt)
        
        # Обработка результата
        metadata = result.get("metadata", {})
        
        return AgentOutput(
            agent="RiskAgent",
            recommendation=result.get("recommendation", "hold"),
            confidence=result.get("confidence", 0.7),
            reasoning=result.get("reasoning", "Risk analysis completed"),
            key_factors=result.get("key_factors", []),
            warnings=result.get("warnings", []),
            metadata={
                "model": self.model,
                "position_size": metadata.get("position_size"),
                "position_value": metadata.get("position_value"),
                "stop_loss": metadata.get("stop_loss"),
                "take_profit": metadata.get("take_profit"),
                "risk_reward_ratio": metadata.get("risk_reward_ratio"),
                "max_loss_amount": metadata.get("max_loss_amount"),
                "max_gain_amount": metadata.get("max_gain_amount"),
                "account_balance": self.account_balance,
                "risk_per_trade": self.risk_per_trade,
                **metadata
            }
        )
    
    def calculate_position_size(
        self,
        entry_price: float,
        stop_loss: float,
        direction: str = "buy"
    ) -> dict:
        """
        Рассчитывает размер позиции по классической формуле.
        
        Position = (Account × Risk%) / (Entry - StopLoss)
        """
        risk_amount = self.account_balance * self.risk_per_trade
        
        if direction.lower() == "buy":
            risk_per_unit = abs(entry_price - stop_loss)
        else:
            risk_per_unit = abs(stop_loss - entry_price)
        
        if risk_per_unit == 0:
            return {
                "position_size": 0,
                "error": "Stop loss too close to entry"
            }
        
        position_size = risk_amount / risk_per_unit
        
        return {
            "position_size": position_size,
            "position_value": position_size * entry_price,
            "risk_amount": risk_amount,
            "risk_per_unit": risk_per_unit,
            "risk_pct": self.risk_per_trade
        }
    
    def calculate_risk_reward(
        self,
        entry_price: float,
        stop_loss: float,
        take_profit: float,
        direction: str = "buy"
    ) -> dict:
        """Рассчитывает Risk/Reward ratio."""
        if direction.lower() == "buy":
            risk = abs(entry_price - stop_loss)
            reward = abs(take_profit - entry_price)
        else:
            risk = abs(stop_loss - entry_price)
            reward = abs(entry_price - take_profit)
        
        if risk == 0:
            return {"risk_reward_ratio": 0, "error": "Invalid stop loss"}
        
        ratio = reward / risk
        
        return {
            "risk_reward_ratio": round(ratio, 2),
            "risk": risk,
            "reward": reward,
            "is_acceptable": ratio >= 2.0
        }


class TimeWindowAgent(BaseAgent):
    """
    TimeWindow Agent — определение оптимального времени входа/выхода.
    
    Использует:
    - Intraday timing (лучшие часы для торговли)
    - Day-of-week analysis
    - Month-of-year patterns
    - Choghadiya / Muhurta для астрологического тайминга
    """
    
    def __init__(self, model: str | None = None):
        super().__init__(
            name="TimeWindowAgent",
            model=model,
        )
    
    def get_system_prompt(self) -> str:
        return """Ты — эксперт по ТАЙМИНГУ ВХОДА/ВЫХОДА в трейдинге.

Твоя специализация:
1. INTRADAY TIMING — лучшие часы дня для торговли
2. DAY OF WEEK — какой день недели лучше для входа
3. MONTH OF YEAR — сезонные паттерны (Sell in May, etc.)
4. CHOGHADIYA / MUHURTA — астрологический тайминг (опционально)
5. SESSION ANALYSIS — какая сессия (Asia/London/NY)

Анализ для symbol:

Верни строго JSON:

{
    "recommendation": "buy|sell|hold",
    "confidence": 0.0-1.0,
    "reasoning": "2-4 предложения о тайминге",
    "key_factors": [
        "best_entry_window: 14:00-16:00 UTC",
        "day_of_week: Tuesday",
        "session: London/NY overlap",
        "choghadiya: Labh (13:30-15:00 UTC)"
    ],
    "warnings": [
        "ny_session_ending",
        "low_volume_period"
    ],
    "metadata": {
        "best_entry_time": "14:00-16:00 UTC",
        "best_exit_time": "21:00-23:00 UTC",
        "worst_hours": ["00:00-06:00 UTC"],
        "day_of_week": "Tuesday",
        "session_confluence": "London-NY overlap",
        "choghadiya_window": "Labh",
        "muhurta_score": 0.78
    }
}

Верни ТОЛЬКО валидный JSON без markdown."""
    
    async def analyze(self, input_data: AgentInput) -> AgentOutput:
        """Выполняет анализ временного окна."""
        logger.info(f"[TimeWindowAgent] Time analysis for {input_data.symbol}")
        
        extra_context = f"""
## Текущие условия:

symbol: {input_data.symbol}
Current Time: {input_data.timeframe}
Entry Price: ${input_data.price:,.2f}

Проанализируй:
1. Какие часы оптимальны для входа?
2. Какой день недели?
3. Какая торговая сессия сейчас?
4. Есть ли астрологическое окно (Choghadiya)?
"""
        
        prompt = self._build_prompt(input_data, extra_context)
        result = await self._call_llm(prompt)
        
        return AgentOutput(
            agent="TimeWindowAgent",
            recommendation=result.get("recommendation", "hold"),
            confidence=result.get("confidence", 0.6),
            reasoning=result.get("reasoning", "Time window analysis completed"),
            key_factors=result.get("key_factors", []),
            warnings=result.get("warnings", []),
            metadata={
                "model": self.model,
                "best_entry_time": result.get("metadata", {}).get("best_entry_time"),
                "best_exit_time": result.get("metadata", {}).get("best_exit_time"),
                "day_of_week": result.get("metadata", {}).get("day_of_week"),
                "session_confluence": result.get("metadata", {}).get("session_confluence"),
                "choghadiya_window": result.get("metadata", {}).get("choghadiya_window"),
                **result.get("metadata", {})
            }
        )
