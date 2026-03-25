"""
Self-Learning Engine — Feedback Loop
asurdev Sentinel v2.1

Механизм:
1. Агент делает предсказание
2. Outcome tracker проверяет результат через N часов
3. Feedback loop обновляет веса агентов
4. Паттерны сохраняются в Vector Memory
"""
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from enum import Enum
import json
import threading
import time


class OutcomeResult(Enum):
    CORRECT = "correct"
    PARTIAL = "partial"
    WRONG = "wrong"
    PENDING = "pending"


class AgentWeights:
    """Dynamic weights for agent combination based on performance"""
    
    DEFAULT_WEIGHTS = {
        "market": 0.20,
        "bull": 0.10,
        "bear": 0.10,
        "astrologer": 0.15,
        "andrews": 0.15,
        "dow": 0.10,
        "gann": 0.10,
        "cycle": 0.10
    }
    
    def __init__(self, config_path: str = "./data/agent_weights.json"):
        self.config_path = config_path
        self.weights = self.DEFAULT_WEIGHTS.copy()
        self.performance = {agent: {"correct": 0, "total": 0} for agent in self.weights}
        self.load()
    
    def update(self, agent: str, outcome: OutcomeResult, confidence: float):
        """Update agent performance based on outcome"""
        if agent not in self.performance:
            return
        
        p = self.performance[agent]
        p["total"] += 1
        
        if outcome == OutcomeResult.CORRECT:
            p["correct"] += 1
        elif outcome == OutcomeResult.PARTIAL:
            p["correct"] += 0.5
        
        # Recalculate weight based on accuracy
        self._rebalance()
        self.save()
    
    def _rebalance(self):
        """Recalculate weights based on accuracy"""
        # Calculate accuracy for each agent
        accuracies = {}
        for agent, perf in self.performance.items():
            if perf["total"] > 0:
                accuracies[agent] = perf["correct"] / perf["total"]
            else:
                accuracies[agent] = 0.5  # Neutral for new agents
        
        # Calculate total accuracy
        total_acc = sum(accuracies.values())
        if total_acc == 0:
            return
        
        # Normalize weights
        new_weights = {}
        for agent, acc in accuracies.items():
            # Base weight * (accuracy boost factor)
            base = self.DEFAULT_WEIGHTS.get(agent, 0.10)
            boost = 0.5 + (acc * 1.5)  # 0.5x to 2x boost
            new_weights[agent] = min(1.0, base * boost)
        
        # Normalize to sum to 1.0
        total = sum(new_weights.values())
        if total > 0:
            for agent in new_weights:
                new_weights[agent] /= total
        
        self.weights = new_weights
    
    def get_weight(self, agent: str) -> float:
        """Get current weight for agent"""
        return self.weights.get(agent, 0.10)
    
    def get_all_weights(self) -> Dict[str, float]:
        """Get all weights"""
        return self.weights.copy()
    
    def get_accuracy(self, agent: str) -> float:
        """Get accuracy for agent"""
        perf = self.performance.get(agent, {"correct": 0, "total": 0})
        if perf["total"] == 0:
            return 0.5
        return perf["correct"] / perf["total"]
    
    def save(self):
        """Save weights to file"""
        data = {
            "weights": self.weights,
            "performance": self.performance,
            "updated": datetime.now().isoformat()
        }
        with open(self.config_path, "w") as f:
            json.dump(data, f, indent=2)
    
    def load(self):
        """Load weights from file"""
        try:
            with open(self.config_path, "r") as f:
                data = json.load(f)
                self.weights = data.get("weights", self.DEFAULT_WEIGHTS)
                self.performance = data.get("performance", self.performance)
        except FileNotFoundError:
            pass


@dataclass
class Prediction:
    """A pending prediction to track"""
    id: str
    symbol: str
    agent: str
    signal: str
    confidence: float
    reasoning: str
    price_at_prediction: float
    timeframe_hours: int
    created_at: datetime = field(default_factory=datetime.now)
    resolved_at: Optional[datetime] = None
    outcome: Optional[OutcomeResult] = None
    actual_change: Optional[float] = None


class SelfLearningEngine:
    """
    Self-learning engine that:
    1. Tracks predictions
    2. Resolves outcomes after timeframe
    3. Updates agent weights
    4. Stores patterns
    """
    
    def __init__(
        self,
        memory=None,
        weights_path: str = "./data/agent_weights.json"
    ):
        self.memory = memory
        self.weights = AgentWeights(weights_path)
        self.predictions: Dict[str, Prediction] = {}
        self.resolution_callbacks: List[Callable] = []
        self._lock = threading.Lock()
        self._running = False
        self._thread: Optional[threading.Thread] = None
    
    def add_prediction(
        self,
        symbol: str,
        agent: str,
        signal: str,
        confidence: float,
        reasoning: str,
        price_at_prediction: float,
        timeframe_hours: int = 24
    ) -> str:
        """Add a prediction to track"""
        import hashlib
        pred_id = hashlib.sha256(
            f"{symbol}{agent}{datetime.now().isoformat()}".encode()
        ).hexdigest()[:16]
        
        prediction = Prediction(
            id=pred_id,
            symbol=symbol,
            agent=agent,
            signal=signal,
            confidence=confidence,
            reasoning=reasoning,
            price_at_prediction=price_at_prediction,
            timeframe_hours=timeframe_hours
        )
        
        with self._lock:
            self.predictions[pred_id] = prediction
        
        return pred_id
    
    def resolve_prediction(
        self,
        pred_id: str,
        current_price: float,
        market_signal: Optional[str] = None
    ) -> Optional[OutcomeResult]:
        """Resolve a prediction against actual price"""
        with self._lock:
            if pred_id not in self.predictions:
                return None
            
            pred = self.predictions[pred_id]
        
        # Calculate price change
        price_change_pct = (
            (current_price - pred.price_at_prediction) / pred.price_at_prediction
        ) * 100
        
        # Determine outcome based on signal and price movement
        if pred.signal in ["BULLISH", "BUY"]:
            expected_up = price_change_pct > 0.5
        elif pred.signal in ["BEARISH", "SELL"]:
            expected_up = price_change_pct < -0.5
        else:
            expected_up = abs(price_change_pct) < 1.0
        
        if expected_up:
            outcome = OutcomeResult.CORRECT
        elif abs(price_change_pct) < 2.0:
            outcome = OutcomeResult.PARTIAL
        else:
            outcome = OutcomeResult.WRONG
        
        # Update prediction
        pred.resolved_at = datetime.now()
        pred.outcome = outcome
        pred.actual_change = price_change_pct
        
        # Update agent weight
        self.weights.update(pred.agent, outcome, pred.confidence)
        
        # Store in memory if available
        if self.memory:
            self.memory.add_outcome(
                symbol=pred.symbol,
                prediction=pred.signal,
                timeframe_hours=pred.timeframe_hours,
                actual_direction=outcome.value,
                actual_price_change=price_change_pct
            )
            
            # Learn pattern if consistently wrong/correct
            if outcome == OutcomeResult.CORRECT:
                self.memory.learn_pattern(
                    pattern_type=f"{pred.agent}_success",
                    description=f"{pred.agent} correctly predicted {pred.signal} for {pred.symbol}",
                    confidence=pred.confidence,
                    evidence=[pred.reasoning]
                )
        
        # Call callbacks
        for callback in self.resolution_callbacks:
            try:
                callback(pred, outcome)
            except Exception as e:
                print(f"Callback error: {e}")
        
        return outcome
    
    def get_pending_predictions(self) -> List[Dict[str, Any]]:
        """Get all pending predictions"""
        with self._lock:
            return [
                {
                    "id": p.id,
                    "symbol": p.symbol,
                    "agent": p.agent,
                    "signal": p.signal,
                    "confidence": p.confidence,
                    "timeframe_hours": p.timeframe_hours,
                    "created_at": p.created_at.isoformat(),
                    "hours_remaining": max(0, p.timeframe_hours - (datetime.now() - p.created_at).total_seconds() / 3600)
                }
                for p in self.predictions.values()
                if p.resolved_at is None
            ]
    
    def get_agent_performance(self) -> Dict[str, Any]:
        """Get performance summary for all agents"""
        return {
            agent: {
                "weight": self.weights.get_weight(agent),
                "accuracy": self.weights.get_accuracy(agent),
                "total_predictions": self.weights.performance[agent]["total"],
                "correct_predictions": self.weights.performance[agent]["correct"]
            }
            for agent in self.weights.weights
        }
    
    def start_background_resolver(
        self,
        check_interval: int = 300,  # 5 minutes
        price_fetcher: Optional[Callable] = None
    ):
        """Start background thread to resolve predictions"""
        if self._running:
            return
        
        self._running = True
        self._thread = threading.Thread(
            target=self._resolver_loop,
            args=(check_interval, price_fetcher),
            daemon=True
        )
        self._thread.start()
    
    def stop_background_resolver(self):
        """Stop background resolver"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
    
    def _resolver_loop(self, interval: int, price_fetcher: Optional[Callable]):
        """Background loop to check and resolve predictions"""
        while self._running:
            try:
                with self._lock:
                    pending = [
                        p for p in self.predictions.values()
                        if p.resolved_at is None
                    ]
                
                now = datetime.now()
                for pred in pending:
                    elapsed = (now - pred.created_at).total_seconds() / 3600
                    if elapsed >= pred.timeframe_hours:
                        if price_fetcher:
                            try:
                                price = price_fetcher(pred.symbol)
                                self.resolve_prediction(pred.id, price)
                            except Exception as e:
                                print(f"Price fetch error: {e}")
                
                time.sleep(interval)
            except Exception as e:
                print(f"Resolver loop error: {e}")
                time.sleep(interval)


# Singleton
_engine: Optional[SelfLearningEngine] = None


def get_learning_engine(
    memory=None,
    weights_path: str = "./data/agent_weights.json"
) -> SelfLearningEngine:
    global _engine
    if _engine is None:
        _engine = SelfLearningEngine(memory, weights_path)
    return _engine
