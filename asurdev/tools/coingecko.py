"""
CoinGecko API интеграция для asurdev Sentinel
"""
import requests
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from functools import lru_cache


BASE_URL = "https://api.coingecko.com/api/v3"


@dataclass
class OHLC:
    """Свеча OHLC"""
    timestamp: int
    open: float
    high: float
    low: float
    close: float


@dataclass
class CoinMarketData:
    """Данные рынка для монеты"""
    symbol: str
    name: str
    current_price: float
    market_cap: float
    volume_24h: float
    price_change_24h: float
    price_change_pct: float
    high_24h: float
    low_24h: float
    ath: float
    ath_change_pct: float
    circulating_supply: float
    total_supply: float
    sparkline: List[float]


class CoinGeckoClient:
    """Клиент CoinGecko API"""
    
    def __init__(self, rate_limit_delay: float = 1.5):
        """
        rate_limit_delay: Задержка между запросами (API ограничен 10-50 calls/min)
        """
        self.rate_limit_delay = rate_limit_delay
        self.last_request = 0
    
    def _rate_limit(self):
        """Ожидание между запросами"""
        elapsed = time.time() - self.last_request
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)
        self.last_request = time.time()
    
    def _get(self, endpoint: str, params: Dict = None) -> Dict:
        """GET запрос"""
        self._rate_limit()
        response = requests.get( timeout=30, url=f"{BASE_URL}{endpoint}", params=params)
        response.raise_for_status()
        return response.json()
    
    def get_coin_list(self) -> List[Dict]:
        """Список всех монет с id для API"""
        return self._get("/coins/list")
    
    @lru_cache(maxsize=32)
    def get_coin_market_data(
        self,
        coin_id: str,
        vs_currency: str = "usd",
        days: int = 7
    ) -> CoinMarketData:
        """Данные рынка монеты"""
        data = self._get(
            f"/coins/{coin_id}",
            params={
                "localization": False,
                "tickers": False,
                "community_data": False,
                "developer_data": False,
                "sparkline": True,
            }
        )
        
        market = data["market_data"]
        return CoinMarketData(
            symbol=data["symbol"].upper(),
            name=data["name"],
            current_price=market["current_price"].get(vs_currency, 0),
            market_cap=market["market_cap"].get(vs_currency, 0),
            volume_24h=market["total_volume"].get(vs_currency, 0),
            price_change_24h=market["price_change_24h"] or 0,
            price_change_pct=market["price_change_percentage_24h"] or 0,
            high_24h=market["high_24h"].get(vs_currency, 0),
            low_24h=market["low_24h"].get(vs_currency, 0),
            ath=market["ath"].get(vs_currency, 0),
            ath_change_pct=market["ath_change_percentage"].get(vs_currency, 0),
            circulating_supply=market["circulating_supply"] or 0,
            total_supply=market["total_supply"] or 0,
            sparkline=market["sparkline_7d"]["price"] if market.get("sparkline_7d") else []
        )
    
    def get_multiple_market_data(
        self,
        coin_ids: List[str],
        vs_currency: str = "usd"
    ) -> Dict[str, CoinMarketData]:
        """Данные для нескольких монет"""
        self._rate_limit()
        data = self._get(
            "/coins/markets",
            params={
                "vs_currency": vs_currency,
                "ids": ",".join(coin_ids),
                "order": "market_cap_desc",
                "sparkline": True,
                "price_change_percentage": "24h,7d",
            }
        )
        
        result = {}
        for coin in data:
            result[coin["id"]] = CoinMarketData(
                symbol=coin["symbol"].upper(),
                name=coin["name"],
                current_price=coin["current_price"],
                market_cap=coin["market_cap"],
                volume_24h=coin["total_volume"],
                price_change_24h=coin["price_change_24h"] or 0,
                price_change_pct=coin["price_change_percentage_24h"] or 0,
                high_24h=coin["high_24h"],
                low_24h=coin["low_24h"],
                ath=coin["ath"],
                ath_change_pct=coin["ath_change_percentage"],
                circulating_supply=coin["circulating_supply"],
                total_supply=coin["total_supply"],
                sparkline=coin["sparkline_in_7d"]["price"] if coin.get("sparkline_in_7d") else []
            )
        return result
    
    def get_ohlc(self, coin_id: str, days: int = 7) -> List[OHLC]:
        """OHLC свечи"""
        data = self._get(
            f"/coins/{coin_id}/ohlc",
            params={"vs_currency": "usd", "days": days}
        )
        
        return [
            OHLC(
                timestamp=candle[0],
                open=candle[1],
                high=candle[2],
                low=candle[3],
                close=candle[4]
            )
            for candle in data
        ]
    
    def get_global_data(self) -> Dict[str, Any]:
        """Глобальные данные рынка"""
        data = self._get("/global")
        return {
            "market_cap_change_24h": data["data"]["market_cap_change_percentage_24h_usd"],
            "total_market_cap": data["data"]["total_market_cap"]["usd"],
            "total_volume": data["data"]["total_volume"]["usd"],
            "btc_dominance": data["data"]["market_cap_percentage"]["btc"],
            "active_coins": data["data"]["active_cryptocurrencies"],
        }
    
    def get_trending(self) -> List[Dict]:
        """Trending монеты"""
        data = self._get("/search/trending")
        return [
            {
                "symbol": coin["item"]["symbol"],
                "name": coin["item"]["name"],
                "market_cap_rank": coin["item"]["market_cap_rank"],
                "price_btc": coin["item"]["price_btc"],
            }
            for coin in data["coins"][:10]
        ]


# Глобальный клиент
_client = None

def get_client() -> CoinGeckoClient:
    global _client
    if _client is None:
        _client = CoinGeckoClient()
    return _client
