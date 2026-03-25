"""
Square of 9 — Gann's Price/Time Calculator
Implementation based on W.D. Gann methodology
"""
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import math


@dataclass
class Square9Result:
    """Результат расчёта Квадрата 9"""
    levels: List[float]  # Ценовые уровни
    angles: List[Dict]     # Углы Ганна
    cardinal_cross: List[float]   # Кардинальный крест
    fixed_cross: List[float]      # Фиксированный крест
    death_zones_days: List[int]   # Зоны смерти в днях


class Square9:
    """
    Квадрат 9 — числовая спираль Ганна
    
    Использование:
        sq = Square9()
        result = sq.calculate_levels(start_price=100, size=100)
    """
    
    def __init__(self):
        self.directions = ["NE", "SE", "SW", "NW"]  # Quadrants
        
    def generate_spiral(self, max_n: int) -> Dict[int, Tuple[int, int]]:
        """
        Генерирует спираль Квадрата 9.
        
        Returns dict: {number: (row, col)}
        Start from center (1), spiral counter-clockwise.
        """
        # Квадрат 9 генерируется от центра
        spiral = {}
        
        if max_n < 1:
            return spiral
            
        size = int(math.ceil(math.sqrt(max_n))) + 2
        grid = [[None] * size for _ in range(size)]
        
        # Центр
        center = size // 2
        row, col = center, center
        direction = 0  # 0=right, 1=down, 2=left, 3=up
        steps = 1
        num = 1
        
        spiral[1] = (row, col)
        grid[row][col] = 1
        
        while num < max_n:
            for _ in range(2):  # Two directions per step count
                # Move
                for _ in range(steps):
                    if num >= max_n:
                        break
                    if direction == 0: col += 1
                    elif direction == 1: row += 1
                    elif direction == 2: col -= 1
                    elif direction == 3: row -= 1
                    num += 1
                    grid[row][col] = num
                    spiral[num] = (row, col)
                direction = (direction + 1) % 4
            steps += 1
        
        return spiral
    
    def get_cardinal_cross(self, numbers: List[int]) -> List[float]:
        """
        Кардинальный крест — горизонтальная и вертикальная линии.
        Числа на позициях 2, 4, 6, 8 от центра (чётные квадраты).
        """
        return [n for n in numbers if n % 4 == 2 or n % 4 == 0][:20]
    
    def get_fixed_cross(self, numbers: List[int]) -> List[float]:
        """
        Фиксированный крест — диагональные линии.
        Числа на позициях 3, 5, 7, 9 от центра (нечётные квадраты).
        """
        return [n for n in numbers if n % 4 in (1, 3) and n > 1][:20]
    
    def calculate_levels(
        self, 
        start_price: float, 
        size: int = 144,
        scale: str = "log"
    ) -> Square9Result:
        """
        Рассчитывает ценовые уровни из Квадрата 9.
        
        Args:
            start_price: Базовая цена (исторический экстремум)
            size: Размер квадрата (144 = 12×12, библейское число)
            scale: 'linear' или 'log'
        
        Returns:
            Square9Result с уровнями и углами
        """
        spiral = self.generate_spiral(size * size)
        numbers = sorted(spiral.keys())
        
        # Конвертируем числа в ценовые уровни
        if scale == "log":
            # Логарифмическая шкала (для BTC, где диапазон большой)
            def num_to_price(n):
                return start_price * (1 + math.log(n) / 10)
        else:
            def num_to_price(n):
                return start_price * n / 10
        
        all_levels = [num_to_price(n) for n in numbers]
        
        # Кардинальный крест (чётные)
        cardinal_nums = self.get_cardinal_cross(numbers)
        cardinal_levels = [num_to_price(n) for n in cardinal_nums]
        
        # Фиксированный крест (нечётные)
        fixed_nums = self.get_fixed_cross(numbers)
        fixed_levels = [num_to_price(n) for n in fixed_nums]
        
        # Углы Ганна (45°, 90°, 180°, 270°, 360°)
        angles = []
        for deg in [45, 90, 135, 180, 225, 270, 315, 360]:
            # Число на данном градусе
            n_on_angle = int(deg / 360 * size * size)
            price_on_angle = num_to_price(n_on_angle)
            angles.append({
                "degrees": deg,
                "number": n_on_angle,
                "price": round(price_on_angle, 2)
            })
        
        # Зоны смерти (дни)
        death_zones = self._get_death_zones()
        
        return Square9Result(
            levels=all_levels,
            angles=angles,
            cardinal_cross=cardinal_levels,
            fixed_cross=fixed_levels,
            death_zones_days=death_zones
        )
    
    def _get_death_zones(self) -> List[int]:
        """
        Зоны смерти по Ганну.
        Циклы, когда рынок подвержен катастрофам:
        7-10, 21-28, 43, 73 дней
        """
        zones = []
        # Основные циклы
        zones.extend([7, 8, 9, 10])  # 7-10 дней
        zones.extend([21, 22, 23, 24, 25, 26, 27, 28])  # 21-28 дней
        zones.extend([43])  # 43 дня
        zones.extend([73])  # 73 дня
        # Расширенные (второй круг)
        zones.extend([79, 81])  # 79-81 дней (Биткоин цикл)
        zones.extend([144, 154])  # Квадрат 12 (144) и далее
        return sorted(set(zones))
    
    def find_nearest_levels(
        self, 
        current_price: float, 
        levels: List[float], 
        count: int = 5
    ) -> Dict:
        """
        Находит ближайшие уровни к текущей цене.
        """
        if not levels:
            return {}
        
        sorted_levels = sorted(levels)
        
        # Ближайшие сверху
        above = [l for l in sorted_levels if l >= current_price][:count]
        
        # Ближайшие снизу
        below = [l for l in sorted_levels if l < current_price][-count:]
        
        return {
            "resistance": above,
            "support": below,
            "current": current_price,
            "nearest_resistance": above[0] if above else None,
            "nearest_support": below[-1] if below else None
        }
    
    def calculate_time_windows(
        self,
        start_date: str,
        death_zones: List[int]
    ) -> List[Dict]:
        """
        Рассчитывает временные окна на основе зон смерти.
        
        Args:
            start_date: Дата начала в формате ISO
            death_zones: Список дней
        
        Returns:
            Список дат временных окон
        """
        from datetime import datetime, timedelta
        
        start = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
        if start.tzinfo is None:
            start = datetime.strptime(start_date, "%Y-%m-%d")
        
        windows = []
        for days in death_zones:
            window_date = start + timedelta(days=days)
            windows.append({
                "day": days,
                "date": window_date.strftime("%Y-%m-%d"),
                "type": self._classify_zone(days)
            })
        
        return windows
    
    def _classify_zone(self, day: int) -> str:
        """Классифицирует зону смерти."""
        if day in range(7, 11):
            return "minor"
        elif day in range(21, 29):
            return "medium"
        elif day == 43:
            return "major"
        elif day == 73:
            return "major"
        elif day in [79, 81]:
            return "bitcoin_cycle"
        else:
            return "extended"


# Singleton
_square9 = None

def get_square9() -> Square9:
    global _square9
    if _square9 is None:
        _square9 = Square9()
    return _square9
