"""
Fuzzy Memory — Adaptive Weights for Agent Synthesis
asurdev Sentinel v3.2
"""

from __future__ import annotations
from typing import Dict, Any, Optional

from .chroma import ChromaMemory


class FuzzyMemory:
    """
    Adaptive weight system for agent synthesis.
    
    Learns from:
    - Outcomes: Did the agent's prediction come true?
    - Feedback: Did the user find the analysis helpful?
    
    Adjusts agent weights dynamically based on recent performance.
    
    Usage:
        fuzzy = FuzzyMemory(chroma)
        weights = fuzzy.get_weights(symbol="BTC", market_condition="BULLISH")
    """
    
    # Default weights (equal baseline)
    DEFAULT_WEIGHTS = {
        "market": 0.20,
        "bull": 0.10,
        "bear": 0.10,
        "astro": 0.15,
        "cycle": 0.10,
        "dow": 0.10,
        "andrews": 0.08,
        "gann": 0.07,
        "meridian": 0.10,
    }
    
    def __init__(self, chroma_memory: Optional[ChromaMemory] = None):
        self.chroma = chroma_memory
        
        # Base weights
        self.weights = self.DEFAULT_WEIGHTS.copy()
        
        # Per-symbol adjustments
        self.symbol_weights: Dict[str, Dict[str, float]] = {}
        
        # Per-market-condition adjustments
        self.condition_weights: Dict[str, Dict[str, float]] = {}
    
    def get_weights(
        self,
        symbol: Optional[str] = None,
        market_condition: Optional[str] = None,
    ) -> Dict[str, float]:
        """
        Get effective weights for current context.
        
        Combines base weights with symbol and condition adjustments.
        """
        weights = self.weights.copy()
        
        # Apply symbol-specific adjustments
        if symbol and symbol in self.symbol_weights:
            for agent, adj in self.symbol_weights[symbol].items():
                if agent in weights:
                    weights[agent] = weights[agent] * (1 + adj)
        
        # Apply market condition adjustments
        if market_condition and market_condition in self.condition_weights:
            for agent, adj in self.condition_weights[market_condition].items():
                if agent in weights:
                    weights[agent] = weights[agent] * (1 + adj)
        
        # Normalize to sum to 1
        total = sum(weights.values())
        if total > 0:
            weights = {k: v / total for k, v in weights.items()}
        
        return weights
    
    def update_from_outcome(
        self,
        agent: str,
        symbol: str,
        outcome: str,  # "correct", "partial", "incorrect"
        confidence: float,
    ):
        """
        Update weights based on prediction outcome.
        
        Correct predictions increase weight, incorrect decrease.
        """
        # Score: correct=1.0, partial=0.5, incorrect=-0.3
        if outcome == "correct":
            score = 1.0
        elif outcome == "partial":
            score = 0.5
        else:
            score = -0.3
        
        # Initialize symbol entry if needed
        if symbol not in self.symbol_weights:
            self.symbol_weights[symbol] = {}
        
        # Exponential moving average
        current = self.symbol_weights[symbol].get(agent, 0)
        self.symbol_weights[symbol][agent] = current * 0.7 + score * 0.3 * confidence / 100
    
    def update_from_feedback(self, agent: str, helpful: bool, rating: int):
        """
        Update weights based on user feedback.
        
        Rating: 1-5 scale, 3 is neutral.
        """
        if agent not in self.weights:
            return
        
        # Adjust based on rating deviation from neutral (3)
        rating_adj = (rating - 3) / 10
        
        if helpful:
            boost = 1 + rating_adj  # e.g., 5->1.2, 4->1.1, 3->1.0
        else:
            boost = 1 - abs(rating_adj)  # e.g., 1->0.8, 2->0.9
        
        self.weights[agent] = self.weights[agent] * boost
    
    def get_recommendation(
        self,
        agent: str,
        symbol: Optional[str] = None,
        market_condition: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get weight recommendation for specific agent.
        
        Returns weight value and whether agent is favored vs baseline.
        """
        weights = self.get_weights(symbol, market_condition)
        weight = weights.get(agent, 0.1)
        baseline = self.DEFAULT_WEIGHTS.get(agent, 0.1)
        
        return {
            "weight": weight,
            "confidence_boost": weight / baseline if baseline > 0 else 1.0,
            "is_favored": weight > baseline,
        }
