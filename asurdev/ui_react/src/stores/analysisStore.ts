import { create } from 'zustand';

interface AnalysisState {
  symbol: string;
  action: string;
  analysis: any | null;
  agents: any[];
  isLoading: boolean;
  error: string | null;
  
  setSymbol: (s: string) => void;
  setAction: (a: string) => void;
  setAnalysis: (a: any) => void;
  setLoading: (l: boolean) => void;
  setError: (e: string | null) => void;
}

export const useAnalysisStore = create<AnalysisState>((set) => ({
  symbol: 'BTC',
  action: 'hold',
  analysis: null,
  agents: [],
  isLoading: false,
  error: null,
  
  setSymbol: (symbol) => set({ symbol }),
  setAction: (action) => set({ action }),
  setAnalysis: (analysis) => set({ analysis }),
  setLoading: (isLoading) => set({ isLoading }),
  setError: (error) => set({ error })
}));
