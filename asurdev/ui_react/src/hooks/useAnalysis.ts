import { useState, useCallback } from 'react';

interface Agent {
  name: string;
  signal: string;
  confidence: number;
  weight: number;
  icon: string;
  color: string;
}

interface Analysis {
  final_signal: string;
  confidence: number;
  summary: string;
  action: string;
  agents: Agent[];
}

export function useAnalysis() {
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const runAnalysis = useCallback(async (symbol: string, action: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await fetch('/api/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ symbol, action })
      });
      const data = await response.json();
      setAnalysis(data);
      setAgents(data.agents || []);
    } catch (e: any) {
      setError(e.message || 'Analysis failed');
    } finally {
      setIsLoading(false);
    }
  }, []);

  return { analysis, agents, isLoading, error, runAnalysis };
}
