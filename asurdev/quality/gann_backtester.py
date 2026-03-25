"""
asurdev Sentinel — Gann Signals Backtester
Tests Square of 9, Death Zones, and Gann Astrology signals
"""
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from collections import defaultdict

from gann import get_gann_agent, Square9, DeathZones, GannAstrology
from tools.coingecko import get_client


@dataclass
class GannSignal:
    """A Gann-generated signal"""
    timestamp: str
    symbol: str
    signal_type: str  # square9, death_zone, astro
    signal: str  # Bullish, Bearish, Neutral
    confidence: int
    price: float
    details: Dict[str, Any]
    
    def to_dict(self) -> dict:
        return asdict(self)


@dataclass  
class BacktestResult:
    """Result of backtesting"""
    total_signals: int
    correct_direction: int
    accuracy: float
    avg_confidence: float
    brier_score: float
    
    # Per signal type
    by_type: Dict[str, Dict[str, float]]
    
    # Per asset
    by_asset: Dict[str, Dict[str, float]]
    
    # Per market regime
    by_regime: Dict[str, Dict[str, float]]
    
    # Death zone stats
    death_zone_hits: int
    death_zone_total: int
    
    # Calibration
    calibration_buckets: List[Dict[str, Any]]


class GannBacktester:
    """
    Backtester for Gann signals
    
    Usage:
        bt = GannBacktester()
        results = bt.run_backtest(
            symbol="BTC",
            days=90,
            initial_capital=10000
        )
        bt.print_summary(results)
    """
    
    def __init__(self, db_client=None):
        self.gann = get_gann_agent()
        self.coingecko = get_client()
        self.db = db_client
    
    def get_historical_prices(self, symbol: str, days: int) -> List[Dict]:
        """Get historical price data"""
        coin_map = {
            "BTC": "bitcoin", "ETH": "ethereum", "SOL": "solana"
        }
        coin_id = coin_map.get(symbol, symbol.lower())
        
        try:
            data = self.coingecko.get_coin_market_data(coin_id)
            
            # Generate synthetic history for testing
            # In production, use historical OHLCV data
            history = []
            base_price = data.current_price
            
            for i in range(days, 0, -1):
                date = datetime.now() - timedelta(days=i)
                
                # Add some variation
                import random
                variation = 1 + (random.random() - 0.5) * 0.3
                price = base_price * variation
                
                history.append({
                    "date": date,
                    "price": price,
                    "volume": data.volume_24h * (0.8 + random.random() * 0.4)
                })
            
            return history
            
        except Exception as e:
            print(f"Error getting history: {e}")
            return []
    
    def classify_regime(self, prices: List[float]) -> str:
        """Classify market regime based on recent volatility"""
        if len(prices) < 20:
            return "unknown"
        
        recent = prices[-20:]
        changes = [abs(recent[i] - recent[i-1]) / recent[i-1] for i in range(1, len(recent))]
        avg_change = sum(changes) / len(changes)
        
        if avg_change > 0.04:
            return "high_volatility"
        elif avg_change > 0.02:
            return "trending"
        else:
            return "flat"
    
    def check_signal_accuracy(
        self, 
        signal: GannSignal, 
        future_prices: List[float],
        horizon: int = 7
    ) -> bool:
        """Check if signal was correct"""
        if len(future_prices) < horizon:
            return False
        
        entry_price = signal.price
        future_price = future_prices[horizon - 1]
        
        if signal.signal == "Bullish":
            return future_price > entry_price
        elif signal.signal == "Bearish":
            return future_price < entry_price
        else:
            return abs(future_price - entry_price) / entry_price < 0.02
    
    def calculate_brier_score(
        self, 
        predicted_prob: float, 
        actual: int
    ) -> float:
        """Calculate Brier score for confidence calibration"""
        return (predicted_prob - actual) ** 2
    
    def run_backtest(
        self,
        symbol: str = "BTC",
        days: int = 90,
        initial_capital: float = 10000,
        signal_horizon: int = 7
    ) -> BacktestResult:
        """
        Run backtest on historical data
        
        Args:
            symbol: Trading symbol
            days: Number of days to backtest
            initial_capital: Starting capital
            signal_horizon: Days to look ahead for signal verification
        
        Returns:
            BacktestResult with detailed metrics
        """
        print(f"Running Gann backtest for {symbol}, {days} days...")
        
        history = self.get_historical_prices(symbol, days)
        if not history:
            return None
        
        signals: List[GannSignal] = []
        results: List[Dict] = []
        
        capital = initial_capital
        position = None
        
        # Process each day (leave buffer for signal verification)
        for i in range(0, len(history) - signal_horizon):
            day = history[i]
            future_prices = [h["price"] for h in history[i:i + signal_horizon]]
            
            # Generate Gann signal for this day
            gann_result = self.gann.analyze({
                "symbol": symbol,
                "current_price": day["price"],
                "date": day["date"].strftime("%Y-%m-%d")
            })
            
            signal = GannSignal(
                timestamp=day["date"].isoformat(),
                symbol=symbol,
                signal_type="gann",
                signal=gann_result.signal,
                confidence=gann_result.confidence,
                price=day["price"],
                details=gann_result.details
            )
            signals.append(signal)
            
            # Check accuracy
            correct = self.check_signal_accuracy(signal, future_prices, signal_horizon)
            
            # Update capital (simplified)
            if signal.signal == "Bullish" and capital > 0:
                # Simple position taking
                price_change = (future_prices[-1] - day["price"]) / day["price"]
                capital *= (1 + price_change)
                position = "long"
            elif signal.signal == "Bearish":
                position = "short"
            
            results.append({
                "timestamp": signal.timestamp,
                "signal": signal.signal,
                "confidence": signal.confidence,
                "correct": correct,
                "price": day["price"],
                "future_price": future_prices[-1],
                "capital": capital,
                "position": position
            })
        
        # Calculate metrics
        return self._calculate_metrics(results, signals, symbol)
    
    def _calculate_metrics(
        self,
        results: List[Dict],
        signals: List[GannSignal],
        symbol: str
    ) -> BacktestResult:
        """Calculate backtest metrics"""
        
        total = len(results)
        if total == 0:
            return None
        
        correct = sum(1 for r in results if r["correct"])
        accuracy = (correct / total) * 100
        
        # Confidence calibration
        confidence_sum = sum(r["confidence"] for r in results)
        avg_confidence = confidence_sum / total
        
        # Brier score
        brier_scores = []
        for r in results:
            pred_prob = r["confidence"] / 100
            actual = 1 if r["correct"] else 0
            brier_scores.append(self.calculate_brier_score(pred_prob, actual))
        
        avg_brier = sum(brier_scores) / len(brier_scores)
        
        # By signal type (if available)
        by_type = defaultdict(lambda: {"total": 0, "correct": 0})
        for s, r in zip(signals, results):
            stype = s.signal_type
            by_type[stype]["total"] += 1
            if r["correct"]:
                by_type[stype]["correct"] += 1
        
        by_type_stats = {}
        for stype, stats in by_type.items():
            by_type_stats[stype] = {
                "accuracy": (stats["correct"] / stats["total"]) * 100 if stats["total"] > 0 else 0,
                "count": stats["total"]
            }
        
        # By asset
        by_asset = {
            symbol: {
                "accuracy": accuracy,
                "count": total,
                "avg_confidence": avg_confidence
            }
        }
        
        # By regime
        by_regime = {}
        
        # Death zone stats
        death_zone_hits = sum(
            1 for s in signals 
            if "death_zone" in str(s.details)
        )
        
        # Calibration buckets
        calibration_buckets = []
        for bucket_start in range(0, 100, 20):
            bucket_end = bucket_start + 20
            bucket_results = [
                r for r in results 
                if bucket_start <= r["confidence"] < bucket_end
            ]
            
            if bucket_results:
                bucket_accuracy = sum(1 for r in bucket_results if r["correct"]) / len(bucket_results)
                calibration_buckets.append({
                    "range": f"{bucket_start}-{bucket_end}",
                    "count": len(bucket_results),
                    "actual_accuracy": bucket_accuracy * 100,
                    "expected": (bucket_start + bucket_end) / 2
                })
        
        return BacktestResult(
            total_signals=total,
            correct_direction=correct,
            accuracy=accuracy,
            avg_confidence=avg_confidence,
            brier_score=avg_brier,
            by_type=by_type_stats,
            by_asset=by_asset,
            by_regime=by_regime,
            death_zone_hits=death_zone_hits,
            death_zone_total=len(signals),
            calibration_buckets=calibration_buckets
        )
    
    def print_summary(self, result: BacktestResult):
        """Print backtest summary"""
        if not result:
            print("No results to display")
            return
        
        print("\n" + "="*60)
        print("GANN BACKTEST RESULTS")
        print("="*60)
        
        print(f"\n📊 Overall Metrics:")
        print(f"   Total Signals: {result.total_signals}")
        print(f"   Accuracy: {result.accuracy:.1f}%")
        print(f"   Avg Confidence: {result.avg_confidence:.1f}%")
        print(f"   Brier Score: {result.brier_score:.3f}")
        
        print(f"\n📐 By Signal Type:")
        for stype, stats in result.by_type.items():
            print(f"   {stype}: {stats['accuracy']:.1f}% ({stats['count']} signals)")
        
        print(f"\n📈 By Asset:")
        for asset, stats in result.by_asset.items():
            print(f"   {asset}: {stats['accuracy']:.1f}% ({stats['count']} signals)")
        
        print(f"\n💀 Death Zones:")
        print(f"   Hits: {result.death_zone_hits}/{result.death_zone_total}")
        
        print(f"\n🎯 Calibration:")
        for bucket in result.calibration_buckets:
            print(f"   {bucket['range']}%: actual={bucket['actual_accuracy']:.1f}%, expected={bucket['expected']:.1f}%")
        
        print("\n" + "="*60)
        
        # Interpretation
        if result.accuracy >= 55:
            print("✅ Accuracy above 55% threshold — signals have predictive value")
        else:
            print("⚠️ Accuracy below 55% — signals need refinement")
        
        if result.brier_score <= 0.25:
            print("✅ Brier score good — confidence well calibrated")
        else:
            print("⚠️ Brier score high — confidence miscalibrated")
    
    def save_result(self, result: BacktestResult, filename: str = None):
        """Save backtest result to JSON"""
        if not result:
            return
        
        data = asdict(result)
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"/home/workspace/asurdevSentinel/data/backtest_{timestamp}.json"
        
        with open(filename, "w") as f:
            json.dump(data, f, indent=2, default=str)
        
        print(f"Saved to {filename}")
        return filename


def run_gann_backtest_cli():
    """CLI entry point for Gann backtest"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Gann Backtester")
    parser.add_argument("--symbol", default="BTC", help="Symbol to test")
    parser.add_argument("--days", type=int, default=90, help="Days to backtest")
    parser.add_argument("--capital", type=float, default=10000, help="Initial capital")
    parser.add_argument("--horizon", type=int, default=7, help="Signal horizon (days)")
    parser.add_argument("--save", action="store_true", help="Save results")
    
    args = parser.parse_args()
    
    bt = GannBacktester()
    result = bt.run_backtest(
        symbol=args.symbol,
        days=args.days,
        initial_capital=args.capital,
        signal_horizon=args.horizon
    )
    
    bt.print_summary(result)
    
    if args.save and result:
        bt.save_result(result)


if __name__ == "__main__":
    run_gann_backtest_cli()
