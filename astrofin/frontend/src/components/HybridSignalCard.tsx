// frontend/src/components/HybridSignalCard.tsx

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

interface HybridSignalProps {
  signal: {
    signal: string;
    confidence: number;
    summary: string;
    details: any;
  };
  symbol: string;
}

const HybridSignalCard: React.FC<HybridSignalProps> = ({ signal, symbol }) => {
  const getSignalColor = (sig: string) => {
    if (sig.includes('STRONG_BUY')) return 'bg-green-600';
    if (sig.includes('BUY')) return 'bg-green-500';
    if (sig.includes('SELL')) return 'bg-red-500';
    if (sig.includes('STRONG_SELL')) return 'bg-red-600';
    return 'bg-yellow-500';
  };

  return (
    <Card className="w-full max-w-md">
      <CardHeader>
        <CardTitle className="flex justify-between items-center">
          <span>{symbol}</span>
          <Badge className={`${getSignalColor(signal.signal)} text-white px-4 py-1`}>
            {signal.signal}
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-center text-2xl font-bold mb-2">
          {signal.confidence}%
        </p>
        <p className="text-center text-lg text-muted-foreground">
          {signal.summary}
        </p>

        <div className="grid grid-cols-2 gap-4 text-sm mt-4">
          <div>
            <strong>Астрология</strong>
            <p>{signal.details?.ephemeris_summary?.yoga || '-'}</p>
          </div>
          <div>
            <strong>Quant/ML</strong>
            <p>{signal.details?.sub_agents?.find((a: any) => a.agent_name === 'Quant')?.confidence || '-'}%</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default HybridSignalCard;
