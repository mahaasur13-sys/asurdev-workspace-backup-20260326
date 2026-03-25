import React, { useState } from 'react';
import { MapPin, Calendar, Clock, Settings, Calculator } from 'lucide-react';
import type { ChartResult } from '../services/api';

interface ChartFormProps {
  onCalculate: (params: ChartParams) => void;
  isLoading?: boolean;
}

export interface ChartParams {
  date: string;
  time: string;
  lat: number;
  lon: number;
  ayanamsa: string;
  zodiac: string;
  house_system: string;
  compute_panchanga: boolean;
  compute_choghadiya: boolean;
  compute_ashtakavarga: boolean;
}

const AYANAMSA_OPTIONS = [
  { value: 'lahiri', label: 'Лахiry (default)' },
  { value: 'raman', label: 'Raman' },
  { value: 'krishnamurti', label: 'Krishnamurti' },
  { value: 'fagan_bradley', label: 'Fagan Bradley' },
  { value: 'surya_siddhanta', label: 'Surya Siddhanta' },
  { value: 'true_citra', label: 'True Citra' },
  { value: 'tropical', label: 'Tropical' },
];

const HOUSE_SYSTEMS = [
  { value: 'W', label: 'Whole Sign (W)' },
  { value: 'P', label: 'Placidus (P)' },
  { value: 'K', label: 'Koch (K)' },
  { value: 'C', label: 'Campanus (C)' },
  { value: 'E', label: 'Equal (E)' },
];

const COMMON_LOCATIONS = [
  { name: 'Москва', lat: 55.7558, lon: 37.6173 },
  { name: 'Санкт-Петербург', lat: 59.9311, lon: 30.3609 },
  { name: 'Нью-Йорк', lat: 40.7128, lon: -74.0060 },
  { name: 'Лондон', lat: 51.5074, lon: -0.1278 },
  { name: 'Токио', lat: 35.6762, lon: 139.6503 },
  { name: 'Дубай', lat: 25.2048, lon: 55.2708 },
];

export function ChartForm({ onCalculate, isLoading }: ChartFormProps) {
  const now = new Date();
  const [params, setParams] = useState<ChartParams>({
    date: now.toISOString().split('T')[0],
    time: now.toTimeString().slice(0, 8),
    lat: 55.7558,
    lon: 37.6173,
    ayanamsa: 'lahiri',
    zodiac: 'sidereal',
    house_system: 'W',
    compute_panchanga: true,
    compute_choghadiya: true,
    compute_ashtakavarga: false,
  });

  const [showAdvanced, setShowAdvanced] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onCalculate(params);
  };

  const setLocation = (lat: number, lon: number) => {
    setParams(p => ({ ...p, lat, lon }));
  };

  return (
    <form onSubmit={handleSubmit} className="bg-slate-900 rounded-xl p-4 border border-slate-800">
      <h3 className="text-sm font-medium text-slate-400 mb-4 flex items-center gap-2">
        <Calculator className="w-4 h-4 text-cyan-400" />
        Расчёт карты
      </h3>

      {/* Basic inputs */}
      <div className="grid grid-cols-2 gap-3 mb-4">
        <div>
          <label className="block text-xs text-slate-500 mb-1 flex items-center gap-1">
            <Calendar className="w-3 h-3" /> Дата
          </label>
          <input
            type="date"
            value={params.date}
            onChange={e => setParams(p => ({ ...p, date: e.target.value }))}
            className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white"
          />
        </div>

        <div>
          <label className="block text-xs text-slate-500 mb-1 flex items-center gap-1">
            <Clock className="w-3 h-3" /> Время (UTC)
          </label>
          <input
            type="time"
            value={params.time}
            onChange={e => setParams(p => ({ ...p, time: e.target.value }))}
            className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white"
          />
        </div>

        <div>
          <label className="block text-xs text-slate-500 mb-1 flex items-center gap-1">
            <MapPin className="w-3 h-3" /> Широта
          </label>
          <input
            type="number"
            step="0.0001"
            min="-90"
            max="90"
            value={params.lat}
            onChange={e => setParams(p => ({ ...p, lat: parseFloat(e.target.value) }))}
            className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white"
          />
        </div>

        <div>
          <label className="block text-xs text-slate-500 mb-1 flex items-center gap-1">
            <MapPin className="w-3 h-3" /> Долгота
          </label>
          <input
            type="number"
            step="0.0001"
            min="-180"
            max="180"
            value={params.lon}
            onChange={e => setParams(p => ({ ...p, lon: parseFloat(e.target.value) }))}
            className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white"
          />
        </div>
      </div>

      {/* Quick locations */}
      <div className="mb-4">
        <label className="block text-xs text-slate-500 mb-2">Быстрый выбор</label>
        <div className="flex flex-wrap gap-1">
          {COMMON_LOCATIONS.map(loc => (
            <button
              key={loc.name}
              type="button"
              onClick={() => setLocation(loc.lat, loc.lon)}
              className={`px-2 py-1 rounded text-xs ${
                params.lat === loc.lat && params.lon === loc.lon
                  ? 'bg-cyan-600 text-white'
                  : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
              }`}
            >
              {loc.name}
            </button>
          ))}
        </div>
      </div>

      {/* Advanced options */}
      <button
        type="button"
        onClick={() => setShowAdvanced(!showAdvanced)}
        className="flex items-center gap-1 text-xs text-slate-500 hover:text-slate-400 mb-3"
      >
        <Settings className="w-3 h-3" />
        {showAdvanced ? 'Скрыть' : 'Показать'} расширенные
      </button>

      {showAdvanced && (
        <div className="grid grid-cols-2 gap-3 mb-4 p-3 bg-slate-800/50 rounded-lg">
          <div>
            <label className="block text-xs text-slate-500 mb-1">Аянамаса</label>
            <select
              value={params.ayanamsa}
              onChange={e => setParams(p => ({ ...p, ayanamsa: e.target.value }))}
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white"
            >
              {AYANAMSA_OPTIONS.map(opt => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs text-slate-500 mb-1">Система домов</label>
            <select
              value={params.house_system}
              onChange={e => setParams(p => ({ ...p, house_system: e.target.value }))}
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white"
            >
              {HOUSE_SYSTEMS.map(opt => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </div>

          <div className="col-span-2 flex gap-4">
            <label className="flex items-center gap-2 text-xs text-slate-400">
              <input
                type="checkbox"
                checked={params.compute_panchanga}
                onChange={e => setParams(p => ({ ...p, compute_panchanga: e.target.checked }))}
                className="rounded"
              />
              Panchanga
            </label>
            <label className="flex items-center gap-2 text-xs text-slate-400">
              <input
                type="checkbox"
                checked={params.compute_choghadiya}
                onChange={e => setParams(p => ({ ...p, compute_choghadiya: e.target.checked }))}
                className="rounded"
              />
              Choghadiya
            </label>
            <label className="flex items-center gap-2 text-xs text-slate-400">
              <input
                type="checkbox"
                checked={params.compute_ashtakavarga}
                onChange={e => setParams(p => ({ ...p, compute_ashtakavarga: e.target.checked }))}
                className="rounded"
              />
              Ashtakavarga
            </label>
          </div>
        </div>
      )}

      <button
        type="submit"
        disabled={isLoading}
        className="w-full bg-cyan-600 hover:bg-cyan-500 disabled:bg-slate-700 text-white rounded-lg px-4 py-2 text-sm font-medium flex items-center justify-center gap-2"
      >
        {isLoading ? (
          <>
            <span className="animate-spin">⟳</span>
            Расчёт...
          </>
        ) : (
          <>
            <Calculator className="w-4 h-4" />
            Рассчитать карту
          </>
        )}
      </button>
    </form>
  );
}
