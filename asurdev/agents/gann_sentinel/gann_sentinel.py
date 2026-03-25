"""
Gann Sentinel — Standalone Agent
Square of 9 levels calculator as LangChain Tool
"""
import math
from typing import Dict, List, Literal, TypedDict
from datetime import datetime
from dataclasses import dataclass


class GannLevels(TypedDict):
    pivot: float
    buy_zone: List[float]
    sell_zone: List[float]
    targets_up: List[float]
    targets_down: List[float]
    strong_support: List[float]
    strong_resistance: List[float]
    recommendation: str
    timestamp: str


@dataclass
class GannSentinelConfig:
    """Конфигурация Gann Sentinel"""
    method: Literal["square9", "cardinal", "combined"] = "square9"
    degrees: List[float] = None  # Градусы Ганна (по умолчанию: 45, 90, 135, 180, 225, 270, 315, 360)
    time_bars: int = 4  # Количество временных баров для прогноза

    def __post_init__(self):
        if self.degrees is None:
            self.degrees = [45, 90, 135, 180, 225, 270, 315, 360]


class GannSentinel:
    """
    Отдельный агент Gann Square of 9 для интрадей-уровней.
    
    Методы:
    - Square of 9 (классический)
    - Cardinal Cross (крест кардинальных осей)
    - Combined (оба метода вместе)
    
    Использование:
        agent = GannSentinel()
        result = agent.calculate(58000.0)
        print(agent.to_text(result))
    """

    def __init__(self, config: GannSentinelConfig = None):
        self.name = "GannSentinel"
        self.description = "Рассчитывает уровни поддержки/сопротивления по Square of 9"
        self.config = config or GannSentinelConfig()

    def square(self, x: float) -> float:
        """Возводит в квадрат (метод Ганна)"""
        return x * x

    def calculate(self, price: float, method: str = None) -> GannLevels:
        """
        Основной расчёт по классическому Square of 9
        
        Args:
            price: Текущая цена актива
            method: square9 | cardinal | combined
            
        Returns:
            GannLevels с уровнями и рекомендацией
        """
        if price <= 0:
            raise ValueError("Цена должна быть положительной")

        method = method or self.config.method
        
        if method == "square9":
            return self._square9_method(price)
        elif method == "cardinal":
            return self._cardinal_method(price)
        elif method == "combined":
            return self._combined_method(price)
        else:
            return self._square9_method(price)

    def _square9_method(self, price: float) -> GannLevels:
        """Классический метод Square of 9"""
        sqrt_price = math.sqrt(price)

        # Основные углы Ганна (в градусах)
        # Каждые 45° = 1/8 квадрата
        increments = [0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0]

        levels_up = [round(self.square(sqrt_price + inc), 2) for inc in increments]
        levels_down = [round(self.square(sqrt_price - inc), 2) for inc in increments if sqrt_price - inc > 0]

        result: GannLevels = {
            "pivot": round(price, 2),
            "buy_zone": [round(levels_up[1], 2), round(levels_up[2], 2)],   # 45° и 90°
            "sell_zone": [round(levels_down[1], 2), round(levels_down[2], 2)],
            "targets_up": levels_up[3:7],      # 135° → 315°
            "targets_down": levels_down[3:7],
            "strong_support": [round(levels_down[4], 2)],   # 180° — самый сильный
            "strong_resistance": [round(levels_up[4], 2)],
            "recommendation": self._generate_recommendation(price, levels_up, levels_down),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        return result

    def _cardinal_method(self, price: float) -> GannLevels:
        """Метод Cardinal Cross — 4 кардинальные оси (0°, 90°, 180°, 270°)"""
        sqrt_price = math.sqrt(price)

        # Кардинальные градусы (0, 90, 180, 270, 360)
        increments = [0, 0.5, 1.0, 1.5, 2.0]

        levels_up = [round(self.square(sqrt_price + inc), 2) for inc in increments]
        levels_down = [round(self.square(sqrt_price - inc), 2) for inc in increments if sqrt_price - inc > 0]

        result: GannLevels = {
            "pivot": round(price, 2),
            "buy_zone": [round(levels_up[1], 2), round(levels_up[2], 2)],
            "sell_zone": [round(levels_down[1], 2), round(levels_down[2], 2)],
            "targets_up": levels_up[2:5],
            "targets_down": levels_down[2:5],
            "strong_support": [round(levels_down[2], 2)],   # 180° — кардинальная поддержка
            "strong_resistance": [round(levels_up[2], 2)],
            "recommendation": self._generate_recommendation(price, levels_up, levels_down),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        return result

    def _combined_method(self, price: float) -> GannLevels:
        """Комбинированный метод — оба подхода вместе"""
        sqrt_price = math.sqrt(price)

        # Все градусы от 0 до 360 с шагом 22.5° (1/16 квадрата)
        all_levels = {}
        
        for degrees in [22.5, 45, 67.5, 90, 112.5, 135, 157.5, 180, 
                        202.5, 225, 247.5, 270, 292.5, 315, 337.5, 360]:
            inc = degrees / 360  # Конвертация градусов в increment
            all_levels[f"{degrees}°"] = {
                "up": round(self.square(sqrt_price + inc), 2),
                "down": round(self.square(sqrt_price - inc), 2) if sqrt_price - inc > 0 else None
            }

        base = self._square9_method(price)
        
        # Добавляем 22.5° и 67.5° уровни
        result: GannLevels = {
            **base,
            "all_angles": all_levels,
            "recommendation": self._generate_combined_recommendation(price, all_levels)
        }
        return result

    def _generate_recommendation(self, price: float, up: List[float], down: List[float]) -> str:
        """Генерирует текстовую рекомендацию"""
        buy_entry = up[1]
        sell_entry = down[1]
        
        if price > buy_entry:
            return (f"✅ LONG | Вход выше {buy_entry} | "
                   f"Цели: {up[3]}, {up[4]}, {up[5]} | "
                   f"SL ниже {down[1]}")
        elif price < sell_entry:
            return (f"❌ SHORT | Вход ниже {sell_entry} | "
                   f"Цели: {down[3]}, {down[4]}, {down[5]} | "
                   f"SL выше {up[1]}")
        else:
            return f"⚠️ В зоне ожидания {price} | Ждём пробоя 45° уровня"

    def _generate_combined_recommendation(self, price: float, angles: Dict) -> str:
        """Генерирует рекомендацию для комбинированного метода"""
        buy_zone = f"{angles['45°']['up']} - {angles['90°']['up']}"
        sell_zone = f"{angles['315°']['down']} - {angles['270°']['down']}"
        
        return (f"Уровни Ганна на {price}:\n"
               f"🟢 LONG зона: выше {buy_zone}\n"
               f"🔴 SHORT зона: ниже {sell_zone}\n"
               f"⚪ Сильная поддержка: {angles['180°']['down']}\n"
               f"⚪ Сильное сопротивление: {angles['180°']['up']}")

    def to_text(self, result: GannLevels) -> str:
        """Человекочитаемый вывод для голоса или дашборда"""
        text = f"""🟦 Gann Sentinel | {result['timestamp']}
Цена: {result['pivot']}

📈 Уровни покупки: {result['buy_zone'][0]} - {result['buy_zone'][1]}
📉 Уровни продажи: {result['sell_zone'][0]} - {result['sell_zone'][1]}

🟩 Цели вверх: {', '.join(map(str, result['targets_up']))}
🟥 Цели вниз: {', '.join(map(str, result['targets_down']))}

🔴 Сильное сопротивление: {result['strong_resistance'][0]}
🟢 Сильная поддержка: {result['strong_support'][0]}

📋 Рекомендация: {result['recommendation']}
"""
        return text

    def to_markdown(self, result: GannLevels) -> str:
        """Markdown формат для дашборда"""
        return f"""## Gann Square of 9 | {result['pivot']}

### Зоны
| Тип | Уровни |
|-----|--------|
| 🟢 Buy Zone | {result['buy_zone'][0]} - {result['buy_zone'][1]} |
| 🔴 Sell Zone | {result['sell_zone'][0]} - {result['sell_zone'][1]} |

### Цели
| Направление | Уровни |
|-------------|--------|
| ⬆️ Targets UP | {' → '.join(map(str, result['targets_up']))} |
| ⬇️ Targets DOWN | {' → '.join(map(str, result['targets_down']))} |

### Ключевые уровни
- **Resistance**: {result['strong_resistance'][0]}
- **Support**: {result['strong_support'][0]}

### Рекомендация
{result['recommendation']}
"""


def get_gann_sentinel() -> GannSentinel:
    """Фабричная функция для получения экземпляра"""
    return GannSentinel()
