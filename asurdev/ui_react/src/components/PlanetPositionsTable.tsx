import React from 'react';
import { Orbit } from 'lucide-react';
import type { PlanetPosition } from '../services/api';

const ZODIAC_SIGNS = [
  'Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
  'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'
];

const PLANET_SYMBOLS: Record<string, string> = {
  Sun: '☉', Moon: '☽', Mercury: '☿', Venus: '♀', Mars: '♂',
  Jupiter: '♃', Saturn: '♄', Uranus: '♅', Neptune: '♆', Pluto: '♇',
  North_Node: '☊', South_Node: '☋', North_Node: '☊'
};

const PLANET_COLORS: Record<string, string> = {
  Sun: 'text-yellow-400', Moon: 'text-slate-300', Mercury: 'text-teal-400',
  Venus: 'text-pink-400', Mars: 'text-red-400', Jupiter: 'text-orange-400',
  Saturn: 'text-amber-600', Uranus: 'text-cyan-400', Neptune: 'text-blue-400',
  Pluto: 'text-purple-400', North_Node: 'text-indigo-400'
};

function formatDegree(lon: number): string {
  const signIdx = Math.floor(lon / 30) % 12;
  const degInSign = lon % 30;
  return `${ZODIAC_SIGNS[signIdx]} ${degInSign.toFixed(2)}°`;
}

interface PlanetPositionsTableProps {
  positions: Record<string, PlanetPosition>;
  houses?: Record<string, number>;
}

export function PlanetPositionsTable({ positions, houses }: PlanetPositionsTableProps) {
  const planetOrder = ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto'];

  return (
    <div className="bg-slate-900 rounded-xl p-4 border border-slate-800">
      <h3 className="text-sm font-medium text-slate-400 mb-3 flex items-center gap-2">
        <Orbit className="w-4 h-4 text-yellow-400" />
        Позиции планет
      </h3>

      <div className="space-y-1">
        {planetOrder.map(planet => {
          const pos = positions[planet];
          if (!pos) return null;

          const symbol = PLANET_SYMBOLS[planet] || '●';
          const colorClass = PLANET_COLORS[planet] || 'text-slate-400';

          return (
            <div key={planet} className="flex items-center justify-between py-1.5 border-b border-slate-800/50 last:border-0">
              <div className="flex items-center gap-2">
                <span className={`text-lg ${colorClass}`}>{symbol}</span>
                <span className="text-sm text-slate-300">{planet}</span>
              </div>
              <div className="text-right">
                <span className="text-sm font-medium text-white">
                  {formatDegree(pos.lon)}
                </span>
                <span className="text-xs text-slate-500 ml-2">
                  {pos.speed >= 0 ? '+' : ''}{pos.speed.toFixed(3)}°/d
                </span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Houses display */}
      {houses && Object.keys(houses).length > 0 && (
        <div className="mt-4 pt-3 border-t border-slate-700">
          <h4 className="text-xs font-medium text-slate-500 mb-2">Дома (куспы)</h4>
          <div className="grid grid-cols-4 gap-1">
            {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12].map(house => {
              const lon = houses[`house_${house}`] || houses[house];
              if (!lon) return <div key={house} />;
              return (
                <div key={house} className="text-center">
                  <div className="text-xs text-slate-500">{house}</div>
                  <div className="text-xs text-cyan-400">{formatDegree(lon).split(' ')[0]}</div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
