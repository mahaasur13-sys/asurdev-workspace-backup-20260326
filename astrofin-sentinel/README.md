# AstroFin Sentinel

Multi-agent trading assistant combining technical analysis with financial astrology.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        USER QUERY                            │
│                    "What's on BTC?"                          │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                     DATA FETCHER                            │
│  ┌─────────────────┐    ┌─────────────────────────────────┐│
│  │  Market Data    │    │        Astro Calculator         ││
│  │  (CoinGecko)    │    │    (Swiss Ephemeris + Moon,      ││
│  │  + TA           │    │     Nakshatra, Yoga, Paksha)     ││
│  └─────────────────┘    └─────────────────────────────────┘│
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                   BOARD OF DIRECTORS                        │
│         (Parallel Agent Execution)                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │Market Analyst │  │Bull Researcher│  │Bear Researcher│     │
│  │   Neutral    │  │   Bullish    │  │   Bearish    │     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │
│         │                 │                 │              │
│         └─────────────────┼─────────────────┘              │
│                           │                                 │
│                    ┌──────▼───────┐                         │
│                    │  Astrologer  │                         │
│                    │  (Celestial) │                         │
│                    └──────┬───────┘                         │
└───────────────────────────┼─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                       SYNTHESIZER                           │
│              (Weighted Voting + Consensus)                   │
│                                                              │
│  • Weighted average of all agent opinions                   │
│  • Astro weight: 50% (configurable)                        │
│  • Output: STRONG_BUY/BUY/NEUTRAL/SELL/STRONG_SELL        │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    FINAL RECOMMENDATION                     │
│                                                              │
│  ⚠️ NOT FINANCIAL ADVICE - Make your own decisions         │
└─────────────────────────────────────────────────────────────┘
```

## Agents

| Agent | Role | Weight |
|-------|------|--------|
| Market Analyst | Technical analysis (RSI, Support/Resistance, Trend) | 1.0 |
| Bull Researcher | Finds bullish arguments and catalysts | 0.8 |
| Bear Researcher | Finds bearish arguments and risks | 0.8 |
| Astrologer | Financial astrology (Moon, Nakshatra, Yoga) | 0.5 |

## Installation

```bash
cd astrofin-sentinel
pip install -e .
```

## Configuration

Copy `.env.example` to `.env` and fill in your API keys:

```bash
COINGECKO_API_KEY=your_coingecko_api_key
OPENAI_API_KEY=your_openai_api_key
```

## Usage

### Python API

```python
from src.main import run

result = run("BTC", timeframe="4h")
print(result.final_decision)  # Decision.SELL
print(result.final_confidence)  # 0.72
print(result.final_recommendation)
```

### CLI

```bash
python -m src.main BTC --timeframe 4h
```

### Docker

```bash
docker build -t astrofin-sentinel .
docker run --env-file .env astrofin-sentinel BTC
```

## Astrological Signals

The system uses Swiss Ephemeris for accurate planetary calculations:

- **Moon Phase**: New Moon, First Quarter, Full Moon, Last Quarter
- **Nakshatra**: 27 lunar mansions with individual characteristics
- **Yoga**: 27 planetary combinations (Shubh, Amrit, Kaal, etc.)
- **Paksha**: Shukla (waxing) vs Krishna (waning) lunar month half
- **Karana**: Half of a tithi (lunar day)

Favorable conditions for trading:
- Waxing moon (Shukla Paksha)
- Favorable nakshatras: Rohini, Mrigashira, Pushya, Swati, Hasta, Chitra, Shravana, Revati
- Favorable yogas: Shubh, Amrit, Siddha, Sadhya

## Warning

⚠️ **This is NOT financial advice.** The system is a cognitive assistant for decision-making support, not an automated trading bot. Always do your own research before making investment decisions.

## Tech Stack

- **LangGraph** - Multi-agent orchestration
- **LangChain** - LLM chains and tools
- **Swiss Ephemeris** - Astrological calculations
- **CoinGecko API** - Market data
- **OpenAI GPT-4o** - LLM backend (configurable to local Ollama)
