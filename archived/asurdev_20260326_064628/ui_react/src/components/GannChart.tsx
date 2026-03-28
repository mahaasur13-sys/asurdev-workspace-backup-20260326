import React, { useMemo } from 'react';
import {
  ComposedChart,
  Line,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
  Area,
} from 'recharts';
import { TrendingUp, TrendingDown } from 'lucide-react';

interface GannLevel {
  price: number;
  type: 'resistance' | 'support' | 'pivot' | 'gann_line';
  label: string;
  strength?: number;
}

interface AstroMarker {
  date: string;
  type: string;
  planet?: string;
  description?: string;
}

interface ChartDataPoint {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume?: number;
}

interface GannChartProps {
  /** Данные графика */
  data: ChartDataPoint[];
  /** Уровни Ганна */
  levels?: GannLevel[];
  /** Астрологические маркеры */
  astroMarkers?: AstroMarker[];
  /** Высота графика */
  height?: number;
  /** Показывать объёмы */
  showVolume?: boolean;
  /** Текущая цена (для вертикальной линии) */
  currentPrice?: number;
}

// Цвета для разных типов уровней
const LEVEL_COLORS = {
  resistance: '#EF5350',
  support: '#26A69A',
  pivot: '#FFD700',
  gann_line: '#9B59B6',
};

export function GannChart({
  data,
  levels = [],
  astroMarkers = [],
  height = 400,
  showVolume = true,
  currentPrice,
}: GannChartProps) {
  // Форматируем данные для графика
  const chartData = useMemo(() => {
    return data.map((d) => ({
      ...d,
      // Цена для свечей (средняя)
      price: (d.high + d.low + d.close) / 3,
      // Ось X
      time: new Date(d.date).getTime(),
    }));
  }, [data]);

  // Находим границы цены
  const priceRange = useMemo(() => {
    if (chartData.length === 0) return { min: 0, max: 100 };
    const highs = chartData.map((d) => d.high);
    const lows = chartData.map((d) => d.low);
    const min = Math.min(...lows);
    const max = Math.max(...highs);
    const padding = (max - min) * 0.1;
    return { min: min - padding, max: max + padding };
  }, [chartData]);

  // Генерируем уровни для recharts ReferenceLine
  const resistanceLevels = useMemo(
    () => levels.filter((l) => l.type === 'resistance'),
    [levels]
  );
  const supportLevels = useMemo(
    () => levels.filter((l) => l.type === 'support'),
    [levels]
  );
  const pivotLevels = useMemo(
    () => levels.filter((l) => l.type === 'pivot'),
    [levels]
  );
  const gannLevels = useMemo(
    () => levels.filter((l) => l.type === 'gann_line'),
    [levels]
  );

  // Астрологические маркеры
  const astroDates = useMemo(() => {
    return astroMarkers.map((m) => new Date(m.date).getTime());
  }, [astroMarkers]);

  // Кастомный tooltip
  const CustomTooltip = ({
    active,
    payload,
    label,
  }: {
    active?: boolean;
    payload?: Array<{ value: number; dataKey: string; color: string }>;
    label?: string;
  }) => {
    if (!active || !payload?.length) return null;

    const data = payload[0]?.payload;
    if (!data) return null;

    return (
      <div className="bg-slate-900 border border-slate-700 rounded-lg p-3 shadow-xl">
        <p className="text-xs text-slate-400 mb-2">
          {new Date(label).toLocaleDateString('ru-RU', {
            day: 'numeric',
            month: 'short',
            year: 'numeric',
          })}
        </p>
        <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-sm">
          <span className="text-slate-400">Open:</span>
          <span className="text-white font-mono">${data.open?.toLocaleString()}</span>
          <span className="text-slate-400">High:</span>
          <span className="text-green-400 font-mono">${data.high?.toLocaleString()}</span>
          <span className="text-slate-400">Low:</span>
          <span className="text-red-400 font-mono">${data.low?.toLocaleString()}</span>
          <span className="text-slate-400">Close:</span>
          <span
            className={`font-mono ${
              data.close >= data.open ? 'text-green-400' : 'text-red-400'
            }`}
          >
            ${data.close?.toLocaleString()}
          </span>
        </div>
        {data.volume && (
          <p className="text-xs text-slate-500 mt-2">
            Volume: {data.volume.toLocaleString()}
          </p>
        )}
      </div>
    );
  };

  if (chartData.length === 0) {
    return (
      <div
        className="flex items-center justify-center bg-slate-900/30 rounded-xl border border-slate-800 border-dashed"
        style={{ height }}
      >
        <div className="text-center text-slate-500">
          <TrendingUp className="w-12 h-12 mx-auto mb-4 opacity-50" />
          <p>Нет данных для отображения</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-slate-900/50 rounded-xl border border-slate-800 p-4">
      {/* Уровни Ганна - боковая панель */}
      <div className="flex gap-4">
        {/* Основной график */}
        <div className="flex-1">
          <ResponsiveContainer width="100%" height={height}>
            <ComposedChart
              data={chartData}
              margin={{ top: 20, right: 30, left: 20, bottom: 20 }}
            >
              <defs>
                {/* Gradient для объёмов */}
                <linearGradient id="volumeGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#26A69A" stopOpacity={0.8} />
                  <stop offset="100%" stopColor="#26A69A" stopOpacity={0.1} />
                </linearGradient>
                <linearGradient id="volumeGradientRed" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#EF5350" stopOpacity={0.8} />
                  <stop offset="100%" stopColor="#EF5350" stopOpacity={0.1} />
                </linearGradient>
              </defs>

              {/* Сетка */}
              <XAxis
                dataKey="time"
                tickFormatter={(t) =>
                  new Date(t).toLocaleDateString('en-US', {
                    month: 'short',
                    day: 'numeric',
                  })
                }
                stroke="#334155"
                tick={{ fill: '#94a3b8', fontSize: 11 }}
                axisLine={{ stroke: '#334155' }}
              />
              <YAxis
                domain={[priceRange.min, priceRange.max]}
                tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`}
                stroke="#334155"
                tick={{ fill: '#94a3b8', fontSize: 11 }}
                axisLine={{ stroke: '#334155' }}
                yAxisId="price"
              />

              {/* Объёмы */}
              {showVolume && (
                <Bar
                  yAxisId="volume"
                  dataKey="volume"
                  fill="url(#volumeGradient)"
                  opacity={0.4}
                  name="Volume"
                />
              )}
              <YAxis
                yAxisId="volume"
                orientation="right"
                stroke="#334155"
                tick={{ fill: '#94a3b8', fontSize: 10 }}
                axisLine={{ stroke: '#334155' }}
              />

              {/* Свечной график (Area для простоты) */}
              <Area
                type="monotone"
                dataKey="price"
                stroke="#26A69A"
                fill="#26A69A"
                fillOpacity={0.1}
                strokeWidth={2}
                name="Price"
              />

              {/* Линии максимума и минимума */}
              <Line
                type="monotone"
                dataKey="high"
                stroke="#26A69A"
                strokeWidth={1}
                dot={false}
                strokeDasharray="2 2"
                opacity={0.3}
              />
              <Line
                type="monotone"
                dataKey="low"
                stroke="#EF5350"
                strokeWidth={1}
                dot={false}
                strokeDasharray="2 2"
                opacity={0.3}
              />

              {/* Уровни сопротивления */}
              {resistanceLevels.map((level, i) => (
                <ReferenceLine
                  key={`r-${i}`}
                  yAxisId="price"
                  y={level.price}
                  stroke={LEVEL_COLORS.resistance}
                  strokeDasharray="5 5"
                  strokeWidth={1}
                  label={{
                    value: `R: $${level.price.toLocaleString()}`,
                    position: 'right',
                    fill: LEVEL_COLORS.resistance,
                    fontSize: 10,
                  }}
                />
              ))}

              {/* Уровни поддержки */}
              {supportLevels.map((level, i) => (
                <ReferenceLine
                  key={`s-${i}`}
                  yAxisId="price"
                  y={level.price}
                  stroke={LEVEL_COLORS.support}
                  strokeDasharray="5 5"
                  strokeWidth={1}
                  label={{
                    value: `S: $${level.price.toLocaleString()}`,
                    position: 'right',
                    fill: LEVEL_COLORS.support,
                    fontSize: 10,
                  }}
                />
              ))}

              {/* Pivot уровни */}
              {pivotLevels.map((level, i) => (
                <ReferenceLine
                  key={`p-${i}`}
                  yAxisId="price"
                  y={level.price}
                  stroke={LEVEL_COLORS.pivot}
                  strokeWidth={2}
                  label={{
                    value: level.label,
                    position: 'left',
                    fill: LEVEL_COLORS.pivot,
                    fontSize: 10,
                  }}
                />
              ))}

              {/* Gann линии */}
              {gannLevels.map((level, i) => (
                <ReferenceLine
                  key={`g-${i}`}
                  yAxisId="price"
                  y={level.price}
                  stroke={LEVEL_COLORS.gann_line}
                  strokeDasharray="3 3"
                  strokeWidth={1}
                  opacity={0.6}
                />
              ))}

              {/* Текущая цена */}
              {currentPrice && (
                <ReferenceLine
                  yAxisId="price"
                  y={currentPrice}
                  stroke="#FFD700"
                  strokeWidth={2}
                />
              )}

              {/* Tooltip */}
              <Tooltip content={<CustomTooltip />} />

              {/* Legend */}
              <Legend
                wrapperStyle={{ paddingTop: 10 }}
                formatter={(value) => (
                  <span className="text-slate-300 text-sm">{value}</span>
                )}
              />
            </ComposedChart>
          </ResponsiveContainer>
        </div>

        {/* Боковая панель с уровнями */}
        {levels.length > 0 && (
          <div className="w-48 space-y-4 text-sm">
            {/* Сопротивления */}
            {resistanceLevels.length > 0 && (
              <div>
                <h4 className="text-red-400 font-medium mb-2 flex items-center gap-1">
                  <TrendingUp className="w-4 h-4" />
                  Resistance
                </h4>
                <div className="space-y-1">
                  {resistanceLevels.slice(0, 4).map((l, i) => (
                    <div key={i} className="flex justify-between text-slate-300">
                      <span className="text-red-300">{l.label}</span>
                      <span className="font-mono">${l.price.toLocaleString()}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Поддержки */}
            {supportLevels.length > 0 && (
              <div>
                <h4 className="text-green-400 font-medium mb-2 flex items-center gap-1">
                  <TrendingDown className="w-4 h-4" />
                  Support
                </h4>
                <div className="space-y-1">
                  {supportLevels.slice(0, 4).map((l, i) => (
                    <div key={i} className="flex justify-between text-slate-300">
                      <span className="text-green-300">{l.label}</span>
                      <span className="font-mono">${l.price.toLocaleString()}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Астрологические метки */}
            {astroMarkers.length > 0 && (
              <div>
                <h4 className="text-purple-400 font-medium mb-2">☽ Astro</h4>
                <div className="space-y-2">
                  {astroMarkers.slice(0, 5).map((m, i) => (
                    <div key={i} className="text-slate-300">
                      <div className="text-purple-300 text-xs">
                        {new Date(m.date).toLocaleDateString('ru-RU', {
                          day: 'numeric',
                          month: 'short',
                        })}
                      </div>
                      <div>{m.type}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default GannChart;
