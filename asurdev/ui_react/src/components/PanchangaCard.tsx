import React from 'react';
import { Star, Moon, Sun, Clock } from 'lucide-react';
import type { PanchangaData } from '../services/api';

interface PanchangaCardProps {
  panchanga: PanchangaData;
}

export function PanchangaCard({ panchanga }: PanchangaCardProps) {
  const items = [
    {
      icon: <Sun className="w-4 h-4 text-yellow-400" />,
      label: 'Вара',
      value: panchanga.vara,
      sub: `День недели`,
    },
    {
      icon: <Moon className="w-4 h-4 text-slate-300" />,
      label: 'Титхи',
      value: panchanga.tithi,
      sub: `${panchanga.tithi_paksha} (${panchanga.tithi_number}/15)`,
    },
    {
      icon: <Star className="w-4 h-4 text-purple-400" />,
      label: 'Накшатра',
      value: panchanga.nakshatra,
      sub: `#${panchanga.nakshatra_number} / Pada ${panchanga.nakshatra_pada}`,
    },
    {
      icon: <Clock className="w-4 h-4 text-teal-400" />,
      label: 'Йога',
      value: panchanga.yoga,
      sub: panchanga.yoga_category,
    },
  ];

  return (
    <div className="bg-slate-900 rounded-xl p-4 border border-slate-800">
      <h3 className="text-sm font-medium text-slate-400 mb-3 flex items-center gap-2">
        <Star className="w-4 h-4 text-green-400" />
        Панчанга
      </h3>

      <div className="space-y-3">
        {items.map(item => (
          <div key={item.label} className="flex items-start gap-3">
            <div className="mt-0.5">{item.icon}</div>
            <div className="flex-1 min-w-0">
              <div className="flex items-baseline justify-between gap-2">
                <span className="text-xs text-slate-500">{item.label}</span>
                <span className="text-sm font-medium text-white truncate">
                  {item.value}
                </span>
              </div>
              <div className="text-xs text-slate-500">{item.sub}</div>
            </div>
          </div>
        ))}

        {/* Sunrise/Sunset */}
        {panchanga.sunrise && panchanga.sunset && (
          <div className="pt-2 border-t border-slate-700 flex justify-between text-xs text-slate-400">
            <span>↑ {panchanga.sunrise}</span>
            <span>↓ {panchanga.sunset}</span>
          </div>
        )}
      </div>
    </div>
  );
}
