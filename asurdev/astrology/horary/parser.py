"""
QuestionParser — Determine question type and significators.
Based on Lilly Chapter 4: "Of the varios Questions or Demands"
"""

import re
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum


class QuestionType(Enum):
    """Major horary question types."""
    FINANCIAL_BUY = "financial_buy"       # "Should I buy X?"
    FINANCIAL_SELL = "financial_sell"      # "Should I sell X?"
    FINANCIAL_HOLD = "financial_hold"      # "Should I hold X?"
    FINANCIAL_OUTLOOK = "financial_outlook"  # "What will happen to X?"
    PARTNERSHIP = "partnership"            # "Should I partner with X?"
    CAREER = "career"                     # "Should I take this job?"
    TRAVEL = "travel"                     # "Should I travel?"
    GENERAL = "general"                   # Generic question


@dataclass
class SignificatorMapping:
    """Maps question to significators per Lilly."""
    quesitor_planet: str      # Planet representing the querier
    quesitor_house: int       # House for the quesitor's interest
    thing_planet: str         # Planet representing the thing/asset
    thing_house: int          # House for the thing/asset
    counsel_planet: str       # Planet for counsel/action
    counsel_house: int        # House for action


# Lilly's significator mappings
QUESTION_MAPPINGS = {
    QuestionType.FINANCIAL_BUY: SignificatorMapping(
        quesitor_planet="Mars",      # Queritor = person asking
        quesitor_house=1,
        thing_planet="Jupiter",        # 2nd house lord = money
        thing_house=2,
        counsel_planet="Mercury",     # 10th from question = action
        counsel_house=10,
    ),
    QuestionType.FINANCIAL_SELL: SignificatorMapping(
        quesitor_planet="Mars",
        quesitor_house=1,
        thing_planet="Venus",         # Possessions = Venus
        thing_house=2,
        counsel_planet="Mercury",
        counsel_house=10,
    ),
    QuestionType.PARTNERSHIP: SignificatorMapping(
        quesitor_planet="Mars",
        quesitor_house=1,
        thing_planet="Venus",         # Partner = Venus (7th house)
        thing_house=7,
        counsel_planet="Jupiter",
        counsel_house=11,
    ),
    QuestionType.CAREER: SignificatorMapping(
        quesitor_planet="Mars",
        quesitor_house=1,
        thing_planet="Jupiter",
        thing_house=10,
        counsel_planet="Mercury",
        counsel_house=6,
    ),
}


class QuestionParser:
    """
    Parse horary question and determine significators.
    
    Based on Lilly Chapter 4: The four parts of a question
    1. The Quesited (thing asked about)
    2. The Quesitor (person asking)
    3. The Significator of the Quesited
    4. The Significator of the Quesitor
    """
    
    # Financial keywords
    BUY_KEYWORDS = ["buy", "purchase", "acquire", "invest in", "go long", "bull"]
    SELL_KEYWORDS = ["sell", "short", "liquidate", "exit", "dump", "bear"]
    HOLD_KEYWORDS = ["hold", "keep", "maintain", "stay in", "wait"]
    
    # Asset class keywords
    CRYPTO_KEYWORDS = ["btc", "bitcoin", "eth", "ethereum", "crypto", "sol", "solana"]
    STOCK_KEYWORDS = ["aapl", "apple", "msft", "microsoft", "googl", "google", 
                      "tsla", "tesla", "amzn", "amazon", "stock", "share"]
    FOREX_KEYWORDS = ["eur", "usd", "gbp", "jpy", "forex", "currency", "pair"]
    COMMODITY_KEYWORDS = ["gold", "silver", "oil", "gas", "commodity"]
    
    def __init__(self):
        self.question_type: QuestionType = QuestionType.GENERAL
        self.symbol: str = ""
        self.action: str = ""  # buy/sell/hold
        self.asset_class: str = ""  # crypto/stock/forex/commodity
        self.raw_question: str = ""
    
    def parse(self, question: str) -> "QuestionParser":
        """Parse a question string into components."""
        self.raw_question = question
        q_lower = question.lower()
        
        # Determine action
        if any(kw in q_lower for kw in self.BUY_KEYWORDS):
            self.action = "buy"
            self.question_type = QuestionType.FINANCIAL_BUY
        elif any(kw in q_lower for kw in self.SELL_KEYWORDS):
            self.action = "sell"
            self.question_type = QuestionType.FINANCIAL_SELL
        elif any(kw in q_lower for kw in self.HOLD_KEYWORDS):
            self.action = "hold"
            self.question_type = QuestionType.FINANCIAL_HOLD
        else:
            self.action = "analyze"
            self.question_type = QuestionType.FINANCIAL_OUTLOOK
        
        # Determine symbol
        self.symbol = self._extract_symbol(question)
        
        # Determine asset class
        self.asset_class = self._determine_asset_class(q_lower)
        
        # Set the mapping after parsing
        self.mapping = self.get_significator_mapping()
        
        return self
    
    def _extract_symbol(self, question: str) -> str:
        """Extract trading symbol from question."""
        # Common patterns: "buy AAPL", "BTC to the moon", "should I sell TSLA"
        patterns = [
            r"\b([A-Z]{2,5})\b",  # Uppercase ticker-like
            r"\b(btc|eth|sol|bitcoin|ethereum|solana)\b",
            r"\b(gold|silver|oil)\b",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, question, re.IGNORECASE)
            if match:
                return match.group(1).upper()
        
        return "UNKNOWN"
    
    def _determine_asset_class(self, q_lower: str) -> str:
        """Determine the asset class being traded."""
        if any(kw in q_lower for kw in self.CRYPTO_KEYWORDS):
            return "CRYPTO"
        elif any(kw in q_lower for kw in self.STOCK_KEYWORDS):
            return "STOCK"
        elif any(kw in q_lower for kw in self.FOREX_KEYWORDS):
            return "FOREX"
        elif any(kw in q_lower for kw in self.COMMODITY_KEYWORDS):
            return "COMMODITY"
        return "GENERIC"
    
    def get_significator_mapping(self) -> SignificatorMapping:
        """Get the significator mapping for this question type."""
        return QUESTION_MAPPINGS.get(
            self.question_type,
            SignificatorMapping(
                quesitor_planet="Mars",
                quesitor_house=1,
                thing_planet="Jupiter",
                thing_house=2,
                counsel_planet="Mercury",
                counsel_house=10,
            )
        )
    
    def get_financial_houses(self) -> Dict[str, int]:
        """
        Get relevant houses for financial question.
        
        Per Lilly:
        - 1st: The Querier
        - 2nd: Money/ possessions
        - 5th: Speculation
        - 7th: Partnership / Open enemies
        - 8th: Other people's money / Debt
        - 10th: Career / Public reputation
        - 11th: Hopes / Gains
        """
        return {
            "querier": 1,
            "money": 2,
            "speculation": 5,
            "partnership": 7,
            "debts": 8,
            "career": 10,
            "gains": 11,
        }
    
    def get_asset_significator(self, symbol: str, asset_class: str) -> str:
        """
        Get the planet that signifies a specific asset.
        
        Traditional associations:
        - Gold/Forever Bull = Sun (Leo)
        - Silver = Moon (Cancer)
        - Copper/Mercury = Mercury
        - Iron/Mars = Mars
        - Tin/Jupiter = Jupiter
        - Lead/Saturn = Saturn
        - Crypto (digital, decentralized) = Uranus (modern) or Mercury (traditional)
        """
        if asset_class == "CRYPTO":
            return "Mercury"  # Communication, exchange
        elif asset_class == "STOCK":
            return "Jupiter"  # Growth, expansion
        elif asset_class == "FOREX":
            return "Mercury"  # Exchange, commerce
        elif asset_class == "COMMODITY":
            return "Venus"  # Value, resources
        return "Jupiter"
    
    def describe(self) -> str:
        """Get a description of the parsed question."""
        return (
            f"Question: {self.raw_question}\n"
            f"Type: {self.question_type.value}\n"
            f"Action: {self.action}\n"
            f"Symbol: {self.symbol}\n"
            f"Asset Class: {self.asset_class}"
        )


def parse_question(question: str) -> QuestionParser:
    """Convenience function to parse a question."""
    return QuestionParser().parse(question)
