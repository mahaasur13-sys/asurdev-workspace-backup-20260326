import { useState, useCallback } from 'react';

interface PerformanceData {
  agent: string;
  accuracy: number;
  predictions: number;
}

export function useFeedback() {
  const [performance, setPerformance] = useState<PerformanceData[]>([]);

  const fetchPerformance = useCallback(async () => {
    try {
      const response = await fetch('/api/performance');
      const data = await response.json();
      setPerformance(data);
    } catch (e) {
      console.error('Failed to fetch performance:', e);
    }
  }, []);

  const submitFeedback = useCallback(async (
    agentId: string,
    rating: number,
    comment: string
  ) => {
    try {
      await fetch('/api/feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ agent_id: agentId, rating, comment })
      });
      await fetchPerformance();
    } catch (e) {
      console.error('Failed to submit feedback:', e);
    }
  }, [fetchPerformance]);

  return { performance, submitFeedback, fetchPerformance };
}
