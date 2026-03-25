import React from 'react';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface AgentProps {
  agent: {
    name: string;
    signal: string;
    confidence: number;
    weight: number;
    icon: string;
    color: string;
  };
}

export function AgentCard({ agent }: AgentProps) {
  const isBullish = agent.signal === 'BULLISH' || agent.signal === 'BUY';
  const isBearish = agent.signal === 'BEARISH' || agent.signal === 'SELL';
  
  const bgColor = isBullish ? 'bg-green-900/30 border-green-800' :
                   isBearish ? 'bg-red-900/30 border-red-800' :
                   'bg-yellow-900/30 border-yellow-800';
  
  const Icon = isBullish ? TrendingUp : isBearish ? TrendingDown : Minus;

  return (
    <div className={`rounded-xl p-4 border ${bgColor}`}>
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="text-lg">{agent.icon}</span>
          <span className="font-medium">{agent.name}</span>
        </div>
        <Icon className={`w-5 h-5 ${isBullish ? 'text-green-400' : isBearish ? 'text-red-400' : 'text-yellow-400'}`} />
      </div>
      <div className="flex items-center justify-between">
        <span className={`text-lg font-bold ${
          isBullish ? 'text-green-400' : isBearish ? 'text-red-400' : 'text-yellow-400'
        }`}>
          {agent.signal}
        </span>
        <div className="text-right">
          <div className="text-xl font-bold">{agent.confidence}%</div>
          <div className="text-xs text-slate-400">confidence</div>
        </div>
      </div>
      <div className="mt-2 pt-2 border-t border-slate-700/50 flex justify-between text-xs text-slate-400">
        <span>Weight: {(agent.weight * 100).toFixed(0)}%</span>
        {agent.accuracy !== undefined && (
          <span>Accuracy: {(agent.accuracy * 100).toFixed(0)}%</span>
        )}
      </div>
    </div>
  );
}
