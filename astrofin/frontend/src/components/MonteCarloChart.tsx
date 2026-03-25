// frontend/src/components/MonteCarloChart.tsx
// Визуализация Monte Carlo — распределение исходов

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';

interface MonteCarloProps {
  data: {
    expected_change: number;
    prob_up: number;
    prob_down: number;
    monte_carlo: {
      mean: number;
      median: number;
      std: number;
    };
  };
  symbol: string;
}

const MonteCarloChart: React.FC<MonteCarloProps> = ({ data, symbol }) => {
  // Симулируем распределение для отображения (в реальности получаем с бэкенда)
  const simulateDistribution = () => {
    const mean = data.monte_carlo.mean;
    const std = data.monte_carlo.std;
    const points: { change: number; density: number }[] = [];
    
    for (let i = -15; i <= 15; i += 1) {
      const x = i;
      const y = Math.exp(-0.5 * Math.pow((x - mean) / std, 2));
      points.push({ change: x, density: y * 100 });
    }
    return points;
  };

  const distributionData = simulateDistribution();

  return (
    <Card>
      <CardHeader>
        <CardTitle>Monte Carlo Прогноз — {symbol}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="mb-4 text-sm text-muted-foreground">
          <span className="text-green-600">{data.prob_up.toFixed(1)}% ↑</span>
          {' | '}
          <span className="text-red-600">{data.prob_down.toFixed(1)}% ↓</span>
        </div>

        <ResponsiveContainer width="100%" height={250}>
          <BarChart data={distributionData} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
            <XAxis 
              dataKey="change" 
              label={{ value: 'Изменение цены (%)', position: 'insideBottom', offset: -10 }} 
            />
            <YAxis 
              label={{ value: 'Плотность вероятности', angle: -90, position: 'insideLeft' }} 
            />
            <Tooltip 
              formatter={(value: number) => [`${value.toFixed(2)}%`, 'Вероятность']} 
              labelFormatter={(label) => `Изменение: ${label}%`} 
            />
            <ReferenceLine x={0} stroke="#666" strokeDasharray="3 3" />
            <Bar dataKey="density" fill="#3b82f6" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>

        <div className="grid grid-cols-3 gap-4 text-center mt-6 text-sm">
          <div>
            <div className="text-muted-foreground">Ожидаемое изменение</div>
            <div className={`text-2xl font-semibold ${data.expected_change >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {data.expected_change >= 0 ? '+' : ''}{data.expected_change.toFixed(1)}%
            </div>
          </div>
          <div>
            <div className="text-muted-foreground">Вероятность роста</div>
            <div className="text-2xl font-semibold text-green-600">
              {data.prob_up.toFixed(1)}%
            </div>
          </div>
          <div>
            <div className="text-muted-foreground">Среднеквадратичное отклонение</div>
            <div className="text-2xl font-semibold">
              ±{data.monte_carlo.std.toFixed(1)}%
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default MonteCarloChart;
