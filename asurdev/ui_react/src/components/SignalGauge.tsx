import React from 'react';

interface Props {
  signal: string;
  confidence: number;
}

export function SignalGauge({ signal, confidence }: Props) {
  const isBullish = signal === 'BULLISH' || signal === 'BUY';
  const isBearish = signal === 'BEARISH' || signal === 'SELL';
  
  const color = isBullish ? '#22c55e' : isBearish ? '#ef4444' : '#eab308';
  const rotation = isBullish ? 45 : isBearish ? -45 : 0;

  return (
    <div className="flex flex-col items-center">
      <div className="relative w-32 h-32">
        <svg viewBox="0 0 100 100" className="w-full h-full">
          <circle cx="50" cy="50" r="45" fill="none" stroke="#334155" strokeWidth="8" />
          <circle
            cx="50" cy="50" r="45" fill="none" stroke={color} strokeWidth="8"
            strokeDasharray={`${(confidence / 100) * 283} 283`}
            strokeLinecap="round"
            transform={`rotate(${rotation - 90} 50 50)`}
            style={{ transition: 'stroke-dasharray 0.5s ease' }}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-3xl font-bold" style={{ color }}>{confidence}%</span>
          <span className="text-xs text-slate-400">{signal}</span>
        </div>
      </div>
    </div>
  );
}
