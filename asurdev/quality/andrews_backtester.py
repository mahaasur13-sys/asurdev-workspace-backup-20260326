"""
asurdev Sentinel — Andrews Backtester v3
Tests: Pitchfork Rules + Expanding + AR1 + AR2 Methods
"""
import argparse
import json
import uuid
from datetime import datetime
from typing import Dict, Any, List


class SimpleBacktester:
    """Упрощённый бэктестер для Andrews методов"""
    
    def __init__(self, initial_balance: float = 10000.0):
        self.initial_balance = initial_balance
    
    def run(self, prices: List[float], method: str = "AR2") -> Dict[str, Any]:
        """
        method: "AR1" or "AR2"
        """
        from andrews.pitchfork import get_andrews_tools
        
        tools = get_andrews_tools()
        pivots = tools.find_pivots(prices)
        expanding = tools.detect_expanding_pattern(prices, pivots)
        
        trades = []
        position = None
        balance = self.initial_balance
        
        # Simple signal generation based on expanding
        for i in range(20, len(prices)):
            signal = tools.get_signal(prices[:i+1])
            
            if signal.signal == "buy" and position is None:
                position = {"entry_price": prices[i], "bar": i, "type": "long"}
            elif signal.signal == "sell" and position is not None:
                trades.append({
                    "entry": position["entry_price"],
                    "exit": prices[i],
                    "pnl_pct": (prices[i] - position["entry_price"]) / position["entry_price"] * 100,
                    "bars": i - position["bar"]
                })
                position = None
        
        if position:
            trades.append({
                "entry": position["entry_price"],
                "exit": prices[-1],
                "pnl_pct": (prices[-1] - position["entry_price"]) / position["entry_price"] * 100,
                "bars": len(prices) - position["bar"]
            })
        
        wins = [t for t in trades if t["pnl_pct"] > 0]
        
        return {
            "method": method,
            "total_trades": len(trades),
            "win_rate": len(wins) / len(trades) * 100 if trades else 0,
            "avg_pnl": sum(t["pnl_pct"] for t in trades) / len(trades) if trades else 0,
            "total_pnl": sum(t["pnl_pct"] for t in trades),
            "expanding_detected": expanding.pattern_type is not None,
            "expanding_direction": expanding.predicted_direction,
            "trades": trades[:10]  # First 10
        }


def main():
    parser = argparse.ArgumentParser(description="Andrews Methods Backtester v3")
    parser.add_argument("--symbol", default="BTC", help="Symbol")
    parser.add_argument("--days", type=int, default=90, help="Days to backtest")
    parser.add_argument("--method", default="AR2", choices=["AR1", "AR2", "BOTH"], help="AR Method")
    parser.add_argument("--output", help="Output JSON file")
    args = parser.parse_args()
    
    print(f"Backtesting Andrews Methods for {args.symbol} ({args.days} days)...")
    
    # Generate sample prices for testing
    import random
    random.seed(42)
    n = args.days
    base = 50000 if args.symbol == "BTC" else 3000
    prices = [base]
    for i in range(n - 1):
        change = random.gauss(0, 0.02)
        prices.append(prices[-1] * (1 + change))
    
    bt = SimpleBacktester()
    
    if args.method == "BOTH":
        results = {
            "AR1": bt.run(prices, "AR1"),
            "AR2": bt.run(prices, "AR2")
        }
    else:
        results = {args.method: bt.run(prices, args.method)}
    
    output = {
        "backtest_id": str(uuid.uuid4()),
        "symbol": args.symbol,
        "days": args.days,
        "timestamp": datetime.now().isoformat(),
        "results": results
    }
    
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(output, f, indent=2)
        print(f"Saved to {args.output}")
    else:
        print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
