"""
Market Data Provider — рыночные данные
======================================
Загружает OHLCV данные с Binance / CoinGecko.
"""

from __future__ import annotations
import requests
from datetime import datetime
from dataclasses import dataclass
from typing import Optional

from agents.base.base_agent import RawMarketData


@dataclass
class MarketDataConfig:
    source: str = "binance"  # "binance" | "coingecko"
    api_key: str = ""
    cache_ttl_seconds: int = 60


class MarketDataProvider:
    """
    Provider рыночных данных.
    В режиме fallback использует публичные API без ключа.
    """

    BINANCE_SPOT = "https://api.binance.com/api/v3"
    COINGECKO = "https://api.coingecko.com/api/v3"

    def __init__(self, config: MarketDataConfig | None = None):
        self.config = config or MarketDataConfig()
        self._cache: dict[str, tuple[float, RawMarketData]] = {}

    def get_market_data(
        self,
        symbol: str,
        timeframe: str = "1h",
    ) -> RawMarketData:
        """
        Получает рыночные данные для символа.

        Args:
            symbol: например "BTCUSDT", "ETH/USDT"
            timeframe: "1m", "5m", "15m", "1h", "4h", "1d"

        Returns:
            RawMarketData с OHLCV и индикаторами
        """
        cache_key = f"{symbol}_{timeframe}"
        now = datetime.utcnow().timestamp()

        if cache_key in self._cache:
            ts, data = self._cache[cache_key]
            if now - ts < self.config.cache_ttl_seconds:
                return data

        if self.config.source == "binance":
            data = self._fetch_binance(symbol, timeframe)
        else:
            data = self._fetch_coingecko(symbol, timeframe)

        self._cache[cache_key] = (now, data)
        return data

    def _fetch_binance(self, symbol: str, timeframe: str) -> RawMarketData:
        """Загрузка с Binance public API."""
        # Нормализуем символ
        sym = symbol.upper().replace("/", "")
        interval_map = {
            "1m": "1m", "5m": "5m", "15m": "15m",
            "1h": "1h", "4h": "4h", "1d": "1d",
        }
        interval = interval_map.get(timeframe, "1h")

        url = f"{self.BINANCE_SPOT}/klines"
        params = {"symbol": sym, "interval": interval, "limit": 100}

        try:
            r = requests.get(url, params=params, timeout=10)
            r.raise_for_status()
            klines = r.json()

            if not klines:
                return self._empty_market_data(symbol)

            closes = [float(k[4]) for k in klines]
            highs = [float(k[2]) for k in klines]
            lows = [float(k[3]) for k in klines]
            volumes = [float(k[5]) for k in klines]

            price = closes[-1]
            change_24h = ((price - closes[0]) / closes[0]) * 100

            # RSI (14)
            rsi = self._calc_rsi(closes, 14)

            # MACD
            macd_signal = self._calc_macd(closes)

            # Support / Resistance
            support, resistance = self._calc_sr_levels(highs, lows, closes)

            # Тренд
            trend = self._determine_trend(closes)

            return RawMarketData(
                symbol=symbol,
                timeframe=timeframe,
                price=price,
                volume_24h=sum(volumes[-24:]),
                change_24h=change_24h,
                high_24h=max(highs[-24:]),
                low_24h=min(lows[-24:]),
                rsi=rsi,
                macd_signal=macd_signal,
                trend=trend,
                support=support,
                resistance=resistance,
                raw_ohlcv=klines[-1],
            )
        except Exception as e:
            print(f"Binance fetch error: {e}")
            return self._empty_market_data(symbol)

    def _fetch_coingecko(self, symbol: str, timeframe: str) -> RawMarketData:
        """Fallback — CoinGecko public API."""
        # CoinGecko не поддерживает timeframe напрямую
        url = f"{self.COINGECKO}/coins/{symbol.lower()}"
        params = {
            "localization": False,
            "tickers": False,
            "community_data": False,
            "developer_data": False,
        }

        try:
            r = requests.get(url, params=params, timeout=10)
            r.raise_for_status()
            data = r.json()

            market = data.get("market_data", {})
            price = market.get("current_price", {}).get("usd", 0)
            change = market.get("price_change_percentage_24h", 0)
            vol = market.get("total_volume", {}).get("usd", 0)
            high = market.get("high_24h", {}).get("usd", 0)
            low = market.get("low_24h", {}).get("usd", 0)

            return RawMarketData(
                symbol=symbol,
                timeframe=timeframe,
                price=price,
                volume_24h=vol,
                change_24h=change or 0,
                high_24h=high,
                low_24h=low,
                rsi=50,
                macd_signal="neutral",
                trend="neutral",
                support=price * 0.97,
                resistance=price * 1.03,
                raw_ohlcv=[],
            )
        except Exception as e:
            print(f"CoinGecko fetch error: {e}")
            return self._empty_market_data(symbol)

    def _empty_market_data(self, symbol: str) -> RawMarketData:
        return RawMarketData(
            symbol=symbol,
            timeframe="1h",
            price=0.0,
            volume_24h=0.0,
            change_24h=0.0,
            high_24h=0.0,
            low_24h=0.0,
            rsi=50.0,
            macd_signal="neutral",
            trend="neutral",
            support=0.0,
            resistance=0.0,
        )

    @staticmethod
    def _calc_rsi(prices: list[float], period: int = 14) -> float:
        if len(prices) < period + 1:
            return 50.0

        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        gains = [d if d > 0 else 0 for d in deltas[-period:]]
        losses = [-d if d < 0 else 0 for d in deltas[-period:]]

        avg_gain = sum(gains) / period
        avg_loss = sum(losses) / period

        if avg_loss == 0:
            return 100.0
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))

    @staticmethod
    def _calc_macd(prices: list[float], fast: int = 12, slow: int = 26, signal: int = 9) -> str:
        if len(prices) < slow + signal:
            return "neutral"

        def ema(data, n):
            k = 2 / (n + 1)
            ema_val = data[0]
            for d in data[1:]:
                ema_val = d * k + ema_val * (1 - k)
            return ema_val

        ema_fast = ema(prices, fast)
        ema_slow = ema(prices, slow)
        macd_line = ema_fast - ema_slow

        return "bullish" if macd_line > 0 else "bearish"

    @staticmethod
    def _calc_sr_levels(
        highs: list[float],
        lows: list[float],
        closes: list[float],
    ) -> tuple[float, float]:
        """Простой расчёт support/resistance по последним 20 свечам."""
        window = 20
        h = highs[-window:]
        l = lows[-window:]
        c = closes[-window:]

        resistance = max(h)
        support = min(l)

        # Корректируем по текущей цене
        current = closes[-1]
        if resistance < current:
            resistance = current * 1.02
        if support > current:
            support = current * 0.98

        return round(support, 2), round(resistance, 2)

    @staticmethod
    def _determine_trend(closes: list[float], period: int = 20) -> str:
        if len(closes) < period:
            return "neutral"
        recent = closes[-period:]
        first_half = sum(recent[:period//2]) / (period//2)
        second_half = sum(recent[period//2:]) / (period - period//2)

        if second_half > first_half * 1.01:
            return "uptrend"
        elif second_half < first_half * 0.99:
            return "downtrend"
        return "neutral"
