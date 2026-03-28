import React from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

interface Props {
  data: Array<{ agent: string; accuracy: number; predictions: number }>;
}

export function PerformanceChart({ data }: Props) {
  if (!data || data.length === 0) return null;

  return (
    <div className="bg-slate-900 rounded-xl p-4 border border-slate-800">
      <ResponsiveContainer width="100%" height={200}>
        <BarChart data={data}>
          <XAxis dataKey="agent" tick={{ fontSize: 10, fill: '#94a3b8' }} />
          <YAxis tick={{ fontSize: 10, fill: '#94a3b8' }} domain={[0, 1]} tickFormatter={v => `${(v*100).toFixed(0)}%`} />
          <Tooltip
            formatter={(v: number) => [`${(v*100).toFixed(1)}%`, 'Accuracy']}
            contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155' }}
          />
          <Bar dataKey="accuracy" fill="#a855f7" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
