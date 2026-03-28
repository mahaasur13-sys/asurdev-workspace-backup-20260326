import React from 'react';
import { useMemo } from 'react';

// Знаки зодиака
const ZODIAC_SIGNS = [
  { name: 'Овен', symbol: '♈', en: 'Aries' },
  { name: 'Телец', symbol: '♉', en: 'Taurus' },
  { name: 'Близнецы', symbol: '♊', en: 'Gemini' },
  { name: 'Рак', symbol: '♋', en: 'Cancer' },
  { name: 'Лев', symbol: '♌', en: 'Leo' },
  { name: 'Дева', symbol: '♍', en: 'Virgo' },
  { name: 'Весы', symbol: '♎', en: 'Libra' },
  { name: 'Скорпион', symbol: '♏', en: 'Scorpio' },
  { name: 'Стрелец', symbol: '♐', en: 'Sagittarius' },
  { name: 'Козерог', symbol: '♑', en: 'Capricorn' },
  { name: 'Водолей', symbol: '♒', en: 'Aquarius' },
  { name: 'Рыбы', symbol: '♓', en: 'Pisces' },
];

// Цвета планет
const PLANET_COLORS: Record<string, string> = {
  Sun: '#FFD700',
  Moon: '#C0C0C0',
  Mercury: '#00BFFF',
  Venus: '#FF69B4',
  Mars: '#FF4500',
  Jupiter: '#DAA520',
  Saturn: '#8B4513',
  Uranus: '#40E0D0',
  Neptune: '#4169E1',
  Pluto: '#800080',
};

// Символы планет
const PLANET_SYMBOLS: Record<string, string> = {
  Sun: '☉',
  Moon: '☽',
  Mercury: '☿',
  Venus: '♀',
  Mars: '♂',
  Jupiter: '♃',
  Saturn: '♄',
  Uranus: '⛢',
  Neptune: '♆',
  Pluto: '♇',
};

interface PlanetPosition {
  sign: number; // 0-11 индекс знака
  degree: number; // 0-29.99 градус в знаке
}

interface ZodiacWheelProps {
  /** Позиции планет */
  positions: Record<string, PlanetPosition>;
  /** Позиции домов (куспиды) - градусы от Асцендента */
  houses?: Record<number, number>;
  /** Размер компонента */
  size?: number;
  /** Стиль отображения */
  variant?: 'modern' | 'classic' | 'minimal';
}

export function ZodiacWheel({
  positions,
  houses = {},
  size = 400,
  variant = 'modern',
}: ZodiacWheelProps) {
  const center = size / 2;
  const outerRadius = size * 0.45;
  const innerRadius = outerRadius * 0.7;
  const houseLineRadius = outerRadius * 0.85;
  const planetOrbit = outerRadius * 0.55;

  // Цвета по варианту
  const colors = useMemo(() => {
    switch (variant) {
      case 'classic':
        return {
          bg: '#f5f5dc',
          sign: '#333333',
          line: '#8b4513',
          house: '#a0522d',
          text: '#333',
          planetBg: '#fff',
        };
      case 'minimal':
        return {
          bg: 'transparent',
          sign: '#888',
          line: '#ccc',
          house: '#aaa',
          text: '#666',
          planetBg: '#fafafa',
        };
      default: // modern
        return {
          bg: '#1a1a2e',
          sign: '#e0e0e0',
          line: '#404060',
          house: '#606080',
          text: '#fff',
          planetBg: '#2a2a4e',
        };
    }
  }, [variant]);

  // Преобразуем градусы в координаты на круге
  const degreeToCoords = (totalDegree: number, radius: number) => {
    // 0° = Север (верх), отсчёт по часовой стрелке
    const rad = ((270 + totalDegree) % 360) * (Math.PI / 180);
    return {
      x: center + radius * Math.cos(rad),
      y: center + radius * Math.sin(rad),
    };
  };

  // Генерируем путь для сегмента знака
  const createSignPath = (startDeg: number, endDeg: number, r: number) => {
    const start = degreeToCoords(startDeg, r);
    const end = degreeToCoords(endDeg, r);
    const largeArc = endDeg - startDeg > 180 ? 1 : 0;
    return `M ${center} ${center} L ${start.x} ${start.y} A ${r} ${r} 0 ${largeArc} 1 ${end.x} ${end.y} Z`;
  };

  // Позиции планет
  const planetPositions = useMemo(() => {
    return Object.entries(positions).map(([planet, pos]) => {
      const totalDegree = pos.sign * 30 + pos.degree;
      const coords = degreeToCoords(totalDegree, planetOrbit);
      return {
        planet,
        symbol: PLANET_SYMBOLS[planet] || '✦',
        color: PLANET_COLORS[planet] || '#fff',
        x: coords.x,
        y: coords.y,
        sign: ZODIAC_SIGNS[pos.sign],
        degree: pos.degree,
      };
    });
  }, [positions, planetOrbit]);

  // Дома
  const houseLines = useMemo(() => {
    return Object.entries(houses).map(([num, degree]) => {
      const start = degreeToCoords(degree, innerRadius * 0.3);
      const end = degreeToCoords(degree, houseLineRadius);
      return { num: Number(num), start, end };
    });
  }, [houses, innerRadius, houseLineRadius]);

  return (
    <div className="relative inline-block">
      <svg
        width={size}
        height={size}
        viewBox={`0 0 ${size} ${size}`}
        className="overflow-visible"
      >
        {/* Фон круга */}
        <circle cx={center} cy={center} r={outerRadius} fill={colors.bg} />

        {/* Сегменты знаков */}
        {ZODIAC_SIGNS.map((sign, i) => {
          const startDeg = i * 30;
          const endDeg = (i + 1) * 30;
          const fillColor = i % 2 === 0 ? colors.bg : variant === 'modern' ? '#2a2a4e' : '#e8e8d0';
          return (
            <path
              key={sign.en}
              d={createSignPath(startDeg, endDeg, outerRadius)}
              fill={fillColor}
              stroke={colors.line}
              strokeWidth={0.5}
            />
          );
        })}

        {/* Внутренний круг (орбис планет) */}
        <circle
          cx={center}
          cy={center}
          r={innerRadius * 0.9}
          fill="none"
          stroke={colors.line}
          strokeWidth={1}
        />

        {/* Линии домов */}
        {houseLines.map(({ num, start, end }) => (
          <g key={num}>
            <line
              x1={start.x}
              y1={start.y}
              x2={end.x}
              y2={end.y}
              stroke={colors.house}
              strokeWidth={1}
              opacity={0.7}
            />
            {/* Номер дома */}
            {(() => {
              const mid = degreeToCoords(
                ((houses[num] || 0) + (houses[num + 1 > 12 ? 1 : num + 1] || 0)) / 2,
                houseLineRadius * 1.05
              );
              return (
                <text
                  x={mid.x}
                  y={mid.y}
                  fill={colors.house}
                  fontSize={8}
                  textAnchor="middle"
                  dominantBaseline="middle"
                >
                  {num}
                </text>
              );
            })()}
          </g>
        ))}

        {/* Символы знаков на внешнем краю */}
        {ZODIAC_SIGNS.map((sign, i) => {
          const midDeg = i * 30 + 15;
          const outerPos = degreeToCoords(midDeg, outerRadius * 0.92);
          const innerPos = degreeToCoords(midDeg, outerRadius * 0.78);
          return (
            <g key={`sign-${sign.en}`}>
              <text
                x={outerPos.x}
                y={outerPos.y}
                fill={colors.text}
                fontSize={12}
                fontWeight="bold"
                textAnchor="middle"
                dominantBaseline="middle"
              >
                {sign.symbol}
              </text>
              <text
                x={innerPos.x}
                y={innerPos.y}
                fill={colors.sign}
                fontSize={6}
                textAnchor="middle"
                dominantBaseline="middle"
              >
                {sign.name.slice(0, 3)}
              </text>
            </g>
          );
        })}

        {/* Планеты */}
        {planetPositions.map(({ planet, symbol, color, x, y }) => (
          <g key={planet}>
            {/* Круг планеты */}
            <circle
              cx={x}
              cy={y}
              r={14}
              fill={colors.planetBg}
              stroke={color}
              strokeWidth={2}
            />
            {/* Символ */}
            <text
              x={x}
              y={y}
              fill={color}
              fontSize={10}
              fontWeight="bold"
              textAnchor="middle"
              dominantBaseline="middle"
            >
              {symbol}
            </text>
            {/* Название */}
            <text
              x={x}
              y={y + 22}
              fill={colors.text}
              fontSize={6}
              textAnchor="middle"
            >
              {planet.slice(0, 3)}
            </text>
          </g>
        ))}

        {/* Центр */}
        <circle cx={center} cy={center} r={4} fill={colors.line} />
      </svg>
    </div>
  );
}

export default ZodiacWheel;
