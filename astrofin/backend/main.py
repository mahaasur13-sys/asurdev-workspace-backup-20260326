"""AstroFin Sentinel v4.4 — Main Entry Point."""
import asyncio
import logging
import sys
from datetime import datetime

# Add parent to path for imports
sys.path.insert(0, "/home/workspace/astrofin")

from backend.agents.astro_council.agent import AstroCouncilAgent

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)


async def main():
    """Run full AstroFin analysis."""
    logger.info("Starting AstroFin Sentinel v4.4")

    council = AstroCouncilAgent()

    result = await council.analyze({
        "symbol": "BTC",
        "price": 68250,
        "datetime": datetime.now(),
        "query": "Analyze BTC for swing trade",
        "timeframe": "SWING",
    })

    print("\n" + "=" * 60)
    print(f"Signal:      {result.signal.value}")
    print(f"Confidence:  {result.confidence:.0%}")
    print(f"Reasoning:   {result.reasoning}")
    print(f"Sources:     {result.sources}")
    print(f"Metadata:     {result.metadata}")
    print("=" * 60)

    metrics = council.get_metrics()
    print(f"\nMetrics: {metrics}")

    return result


if __name__ == "__main__":
    asyncio.run(main())
