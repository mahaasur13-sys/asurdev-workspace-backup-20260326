import React from 'react';
import { Clock, CheckCircle, XCircle } from 'lucide-react';
import type { ChoghadiyaEntry } from '../services/api';

interface ChoghadiyaTimelineProps {
  choghadiya: ChoghadiyaEntry[];
  sunrise?: string;
  sunset?: string;
}

const CHOGHADIYA_COLORS: Record<string, string> = {
  'Amrit': 'bg-green-900/50 border-green-700 text-green-300',
  'Shubh': 'bg-emerald-900/50 border-emerald-700 text-emerald-300',
  'Labh': 'bg-teal-900/50 border-teal-700 text-teal-300',
  'Chal': 'bg-blue-900/50 border-blue-700 text-blue-300',
  'Udveg': 'bg-orange-900/50 border-orange-700 text-orange-300',
  'Rog': 'bg-red-900/50 border-red-700 text-red-300',
  'Kaal': 'bg-slate-800/50 border-slate-600 text-slate-300',
  'Muhurt': 'bg-purple-900/50 border-purple-700 text-purple-300',
};

export function ChoghadiyaTimeline({ choghadiya, sunrise, sunset }: ChoghadiyaTimelineProps) {
  if (!choghadiya || choghadiya.length === 0) {
    return (
      <div className="bg-slate-900 rounded-xl p-4 border border-slate-800">
        <h3 className="text-sm font-medium text-slate-400 mb-2 flex items-center gap-2">
          <Clock className="w-4 h-4 text-blue-400" />
          Чохгадия
        </h3>
        <p className="text-xs text-slate-500">Нет данных</p>
      </div>
    );
  }

  return (
    <div className="bg-slate-900 rounded-xl p-4 border border-slate-800">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-medium text-slate-400 flex items-center gap-2">
          <Clock className="w-4 h-4 text-blue-400" />
          Чохгадия
        </h3>
        {sunrise && sunset && (
          <div className="text-xs text-slate-500">
            ☀ {sunrise} → {sunset}
          </div>
        )}
      </div>

      {/* Legend */}
      <div className="flex gap-3 mb-3 text-xs">
        <div className="flex items-center gap-1">
          <div className="w-2 h-2 rounded-full bg-green-500"></div>
          <span className="text-slate-400">Благоприятная</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-2 h-2 rounded-full bg-red-500"></div>
          <span className="text-slate-400">Неблагоприятная</span>
        </div>
      </div>

      {/* Timeline */}
      <div className="space-y-1">
        {choghadiya.map((chog, idx) => {
          const colorClass = CHOGHADIYA_COLORS[chog.name] || 'bg-slate-800 border-slate-700 text-slate-300';
          const isFavorable = chog.favorable;

          return (
            <div
              key={idx}
              className={`flex items-center gap-2 px-3 py-2 rounded-lg border ${colorClass}`}
            >
              <div className="w-12 text-xs font-mono text-slate-400">
                {chog.period}
              </div>
              <div className="flex-1">
                <div className="text-sm font-medium">{chog.name}</div>
                {chog.description && (
                  <div className="text-xs opacity-70">{chog.description}</div>
                )}
              </div>
              <div className="flex items-center gap-1">
                {isFavorable ? (
                  <CheckCircle className="w-4 h-4 text-green-400" />
                ) : (
                  <XCircle className="w-4 h-4 text-red-400" />
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Summary */}
      <div className="mt-3 pt-3 border-t border-slate-700 text-xs text-slate-400">
        {choghadiya.filter(c => c.favorable).length} благоприятных из {choghadiya.length}
      </div>
    </div>
  );
}
