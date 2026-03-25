"""
Astrology Tools for AstroFin Sentinel
Integrates with Mankashi forecast system
"""

import json
import subprocess
from datetime import datetime, timezone
from typing import Optional


class MankashiAstrologyTool:
    """Tool for generating Mankashi Vedic astrology forecasts."""
    
    def __init__(self, forecast_script_path: str = None):
        self.forecast_script = forecast_script_path or "/home/workspace/asurdev/manjasi_forecast_2026_03_23.py"
    
    def get_daily_forecast(self, date: str = None) -> dict:
        """
        Get Mankashi forecast for a specific date.
        
        Args:
            date: Date in YYYY-MM-DD format. Defaults to today.
            
        Returns:
            Dictionary with forecast data
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        # Run the Mankashi forecast script
        try:
            result = subprocess.run(
                ["python3", self.forecast_script],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return {
                    "status": "success",
                    "forecast": result.stdout,
                    "date": date,
                    "source": "Mankashi"
                }
            else:
                return {
                    "status": "error",
                    "error": result.stderr,
                    "date": date
                }
        except subprocess.TimeoutExpired:
            return {"status": "error", "error": "Script timeout"}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def get_birth_chart(self, birth_date: str, birth_time: str, latitude: float, longitude: float) -> dict:
        """
        Calculate birth chart (S BCS - Janma Kundali).
        
        Args:
            birth_date: Date of birth (DD.MM.YYYY)
            birth_time: Time of birth (HH:MM)
            latitude: Geographic latitude
            longitude: Geographic longitude
            
        Returns:
            Dictionary with birth chart data
        """
        # Placeholder - would integrate with astrological calculation library
        # like swisseph, pytz, or custom implementation
        return {
            "status": "placeholder",
            "message": "Birth chart calculation requires Swiss Ephemeris integration",
            "input": {
                "date": birth_date,
                "time": birth_time,
                "location": {"lat": latitude, "lon": longitude}
            }
        }
    
    def analyze_trading_muhurta(self, symbol: str, side: str = "buy") -> dict:
        """
        Analyze best time (muhurta) for trading a specific symbol.
        
        Args:
            symbol: Trading pair (e.g., "BTC/USDT")
            side: "buy" or "sell"
            
        Returns:
            Dictionary with muhurta analysis
        """
        forecast = self.get_daily_forecast()
        
        # Simple logic based on Mankashi forecast
        # In production, this would be more sophisticated
        return {
            "symbol": symbol,
            "side": side,
            "muhurta": forecast.get("forecast", ""),
            "recommendation": self._extract_recommendation(forecast),
            "best_time": self._get_best_time(forecast),
            "worst_time": self._get_worst_time(forecast)
        }
    
    def _extract_recommendation(self, forecast: dict) -> str:
        """Extract trading recommendation from forecast text."""
        text = forecast.get("forecast", "").lower()
        
        if "благоприятно" in text or "благоприятный" in text:
            return "FAVORABLE"
        elif "неблагоприятно" in text or "неблагоприятный" in text:
            return "UNFAVORABLE"
        else:
            return "NEUTRAL"
    
    def _get_best_time(self, forecast: dict) -> Optional[str]:
        """Extract best time from forecast."""
        text = forecast.get("forecast", "")
        # Simple extraction - would be more sophisticated in production
        if "14:00" in text or "14:00" in text:
            return "14:00 - 17:00"
        return None
    
    def _get_worst_time(self, forecast: dict) -> Optional[str]:
        """Extract worst time from forecast."""
        text = forecast.get("forecast", "")
        if "15:00" in text or "15:00" in text:
            return "15:00 - 18:00"
        return None


# Global instance
_astrology_tool = None

def get_astrology_tool() -> MankashiAstrologyTool:
    global _astrology_tool
    if _astrology_tool is None:
        _astrology_tool = MankashiAstrologyTool()
    return _astrology_tool
