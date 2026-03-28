import React, { useState } from 'react';
import { TrendingUp, Brain, Star, Activity, BarChart3, Moon, Sun, Send, Calculator, 
         LineChart, Settings, X } from 'lucide-react';
import { useAnalysis } from './hooks/useAnalysis';
import { useFeedback } from './hooks/useFeedback';
import { AgentCard } from './components/AgentCard';
import { SignalGauge } from './components/SignalGauge';
import { AstroWidget } from './components/AstroWidget';
import { FeedbackPanel } from './components/FeedbackPanel';
import { PerformanceChart } from './components/PerformanceChart';
import { ChartForm, type ChartParams } from './components/ChartForm';
import { PlanetPositionsTable } from './components/PlanetPositionsTable';
import { PanchangaCard } from './components/PanchangaCard';
import { ChoghadiyaTimeline } from './components/ChoghadiyaTimeline';
import { api, type ChartResult } from './services/api';

type TabType = 'trading' | 'astro';

export default function App() {
  const [activeTab, setActiveTab] = useState<TabType>('trading');
  const [chartResult, setChartResult] = useState<ChartResult | null>(null);
  const [isChartLoading, setIsChartLoading] = useState(false);
  const [chartError, setChartError] = useState<string | null>(null);

  const { analysis, isLoading, error, runAnalysis, agents } = useAnalysis();
  const { performance, submitFeedback } = useFeedback();

  const handleAnalyze = () => runAnalysis('BTC', 'hold');

  // Chart calculation
  const handleCalculateChart = async (params: ChartParams) => {
    setIsChartLoading(true);
    setChartError(null);
    try {
      const result = await api.computeChart(params);
      setChartResult(result);
    } catch (err) {
      setChartError(err instanceof Error ? err.message : 'Failed to calculate chart');
    } finally {
      setIsChartLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-white">
      {/* Header */}
      <header className="border-b border-slate-800 bg-slate-900/50 backdrop-blur sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
                <Brain className="w-6 h-6" />
              </div>
              <div>
                <h1 className="text-xl font-bold">AstroFin Sentinel</h1>
                <p className="text-xs text-slate-400">v2.1 — Self-Learning Multi-Agent</p>
              </div>
            </div>

            {/* Tab Switcher */}
            <div className="flex items-center gap-1 bg-slate-800/50 rounded-lg p-1">
              <button
                onClick={() => setActiveTab('trading')}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                  activeTab === 'trading'
                    ? 'bg-purple-600 text-white'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                <BarChart3 className="w-4 h-4 inline mr-2" />
                Trading
              </button>
              <button
                onClick={() => setActiveTab('astro')}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                  activeTab === 'astro'
                    ? 'bg-cyan-600 text-white'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                <Star className="w-4 h-4 inline mr-2" />
                Astrology
              </button>
            </div>

            <div className="flex items-center gap-2 text-xs text-slate-500">
              <span className="px-2 py-1 bg-green-900/50 text-green-400 rounded">Online</span>
              <span>{new Date().toLocaleTimeString()}</span>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-6">
        {activeTab === 'trading' ? (
          /* ==================== TRADING TAB ==================== */
          <TradingView
            symbol="BTC"
            action="hold"
            analysis={analysis}
            isLoading={isLoading}
            error={error}
            agents={agents}
            performance={performance}
            onAnalyze={handleAnalyze}
            onSubmitFeedback={submitFeedback}
          />
        ) : (
          /* ==================== ASTROLOGY TAB ==================== */
          <AstroView
            chartResult={chartResult}
            isLoading={isChartLoading}
            error={chartError}
            onCalculate={handleCalculateChart}
          />
        )}
      </main>

      <footer className="border-t border-slate-800 mt-12 py-4 text-center text-xs text-slate-500">
        AstroFin Sentinel v2.1 — Swiss Ephemeris + LangChain + AutoGen
      </footer>
    </div>
  );
}

// ============================================================================
// TRADING VIEW
// ============================================================================

interface TradingViewProps {
  symbol: string;
  action: string;
  analysis: any;
  isLoading: boolean;
  error: string | null;
  agents: any[];
  performance: any[];
  onAnalyze: () => void;
  onSubmitFeedback: (agentId: string, rating: number, comment: string) => void;
}

function TradingView({
  symbol, action, analysis, isLoading, error, agents, performance,
  onAnalyze, onSubmitFeedback
}: TradingViewProps) {
  return (
    <>
      {/* Action Bar */}
      <div className="mb-6 p-4 bg-slate-900/50 rounded-xl border border-slate-800 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <select 
            className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm"
            defaultValue={symbol}
          >
            {['BTC','ETH','SOL','BNB','XRP','ADA','DOGE'].map(s => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
          <select 
            className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm"
            defaultValue={action}
          >
            <option value="buy">Buy</option>
            <option value="sell">Sell</option>
            <option value="hold">Hold</option>
          </select>
        </div>
        <button
          onClick={onAnalyze}
          disabled={isLoading}
          className="bg-purple-600 hover:bg-purple-500 disabled:bg-slate-700 px-6 py-2 rounded-lg font-medium flex items-center gap-2"
        >
          {isLoading ? (
            <Activity className="w-4 h-4 animate-spin" />
          ) : (
            <Send className="w-4 h-4" />
          )}
          Run Analysis
        </button>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-900/30 border border-red-800 rounded-xl text-red-300">
          {error}
        </div>
      )}

      <div className="grid grid-cols-12 gap-6">
        {/* Left Column - Agents */}
        <div className="col-span-8 space-y-4">
          <h2 className="text-lg font-semibold flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-purple-400" />
            Agent Analysis
          </h2>
          <div className="grid grid-cols-2 gap-4">
            {agents.map((agent) => (
              <AgentCard key={agent.name} agent={agent} />
            ))}
          </div>
          {performance.length > 0 && (
            <div className="mt-6">
              <h3 className="text-sm font-medium text-slate-400 mb-3">Agent Performance</h3>
              <PerformanceChart data={performance} />
            </div>
          )}
        </div>

        {/* Right Column - Signal & Astro */}
        <div className="col-span-4 space-y-4">
          {analysis && (
            <div className="bg-slate-900 rounded-xl p-6 border border-slate-800">
              <h3 className="text-sm font-medium text-slate-400 mb-4">Final Signal</h3>
              <SignalGauge signal={analysis.final_signal} confidence={analysis.confidence} />
              <div className="mt-4 pt-4 border-t border-slate-800">
                <p className="text-sm text-slate-300">{analysis.summary}</p>
                <div className="mt-3 flex items-center gap-2">
                  <span className={`px-2 py-1 rounded text-xs font-medium ${
                    analysis.action === 'buy' ? 'bg-green-900 text-green-300' :
                    analysis.action === 'sell' ? 'bg-red-900 text-red-300' : 'bg-yellow-900 text-yellow-300'
                  }`}>
                    {analysis.action.toUpperCase()}
                  </span>
                  <span className="text-xs text-slate-500">Confidence: {analysis.confidence}%</span>
                </div>
              </div>
            </div>
          )}
          <AstroWidget />
          <FeedbackPanel onSubmit={onSubmitFeedback} />
        </div>
      </div>
    </>
  );
}

// ============================================================================
// ASTROLOGY VIEW
// ============================================================================

interface AstroViewProps {
  chartResult: ChartResult | null;
  isLoading: boolean;
  error: string | null;
  onCalculate: (params: ChartParams) => void;
}

function AstroView({ chartResult, isLoading, error, onCalculate }: AstroViewProps) {
  return (
    <div className="space-y-6">
      {/* Error display */}
      {error && (
        <div className="p-4 bg-red-900/30 border border-red-800 rounded-xl text-red-300">
          {error}
        </div>
      )}

      <div className="grid grid-cols-12 gap-6">
        {/* Left Column - Form */}
        <div className="col-span-4">
          <ChartForm onCalculate={onCalculate} isLoading={isLoading} />
        </div>

        {/* Right Column - Results */}
        <div className="col-span-8 space-y-4">
          {chartResult ? (
            <>
              {/* Planet Positions */}
              <PlanetPositionsTable 
                positions={chartResult.positions} 
                houses={chartResult.houses}
              />

              {/* Panchanga & Choghadiya */}
              <div className="grid grid-cols-2 gap-4">
                {chartResult.panchanga && (
                  <PanchangaCard panchanga={chartResult.panchanga} />
                )}
                {chartResult.choghadiya && (
                  <ChoghadiyaTimeline 
                    choghadiya={chartResult.choghadiya}
                    sunrise={chartResult.panchanga?.sunrise}
                    sunset={chartResult.panchanga?.sunset}
                  />
                )}
              </div>

              {/* Calculation info */}
              <div className="text-xs text-slate-500 text-right">
                Расчёт выполнен за {chartResult.calculation_time_ms}ms
                {' • '}
                {chartResult.input.ayanamsa} / {chartResult.input.zodiac} / {chartResult.input.house_system}
              </div>
            </>
          ) : (
            <div className="flex items-center justify-center h-96 bg-slate-900/30 rounded-xl border border-slate-800 border-dashed">
              <div className="text-center text-slate-500">
                <Calculator className="w-12 h-12 mx-auto mb-4 opacity-50" />
                <p>Заполните форму и нажмите "Рассчитать карту"</p>
                <p className="text-xs mt-2">Расчёт позиций планет, домов, панчанги и чохгадии</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
