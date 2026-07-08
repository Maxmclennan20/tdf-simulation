import { useState, useEffect } from 'react';
import { useRiders } from './hooks/useRiders';
import { useSimulation } from './hooks/useSimulation';
import { ControlsPanel } from './components/ControlsPanel';
import { ResultsDashboard } from './components/ResultsDashboard';
import type { OddsRow } from './api/types';

type AppTab = 'riders' | 'results';

function App() {
  const { riders, loading, updateRider } = useRiders();
  const { state, run, getResults, getExportUrl } = useSimulation();
  const [activeTab, setActiveTab] = useState<AppTab>('riders');

  // Auto-switch to results when simulation completes
  useEffect(() => {
    if (state === 'complete') setActiveTab('results');
  }, [state]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full bg-surface">
        <div className="text-gray-600 text-sm animate-pulse">Loading riders…</div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-surface">
      {/* Header */}
      <header className="flex items-center justify-between px-6 py-3 bg-panel border-b border-border shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-7 h-7 rounded bg-amber-400 flex items-center justify-center text-black font-bold text-xs">TdF</div>
          <div>
            <h1 className="text-gray-900 font-semibold text-sm leading-tight">Tour de France 2026</h1>
            <p className="text-gray-500 text-xs">Monte Carlo Simulation · 20,000 iterations</p>
          </div>
        </div>

        {/* Top-level tab switcher */}
        <div className="flex items-center gap-1 bg-card rounded-lg p-1">
          <button
            onClick={() => setActiveTab('riders')}
            className={`px-4 py-1.5 text-xs font-medium rounded transition-colors ${
              activeTab === 'riders'
                ? 'bg-panel text-gray-900 shadow-sm'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            Riders
          </button>
          <button
            onClick={() => setActiveTab('results')}
            className={`px-4 py-1.5 text-xs font-medium rounded transition-colors flex items-center gap-1.5 ${
              activeTab === 'results'
                ? 'bg-panel text-gray-900 shadow-sm'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            Results
            {state === 'complete' && (
              <span className="inline-block w-1.5 h-1.5 rounded-full bg-emerald-500" />
            )}
            {state === 'running' && (
              <span className="inline-block w-1.5 h-1.5 rounded-full bg-amber-400 animate-ping" />
            )}
          </button>
        </div>

        {/* Status / run button */}
        <div className="flex items-center gap-3">
          {state === 'running' && (
            <span className="text-amber-600 text-xs animate-pulse">Simulating…</span>
          )}
          {state === 'error' && (
            <span className="text-red-600 text-xs">Simulation failed</span>
          )}
          <button
            onClick={() => { run(); setActiveTab('results'); }}
            disabled={state === 'running'}
            className={`px-4 py-1.5 text-xs rounded font-semibold transition-all ${
              state === 'running'
                ? 'bg-amber-200 text-amber-600 cursor-not-allowed'
                : 'bg-amber-400 text-black hover:bg-amber-300 active:scale-95'
            }`}
          >
            {state === 'running' ? 'Running…' : 'Run Simulation'}
          </button>
        </div>
      </header>

      {/* Body */}
      <div className="flex-1 overflow-hidden relative">
        {activeTab === 'riders' ? (
          <ControlsPanel
            riders={riders}
            onUpdate={updateRider}
          />
        ) : (
          <ResultsDashboard
            simComplete={state === 'complete'}
            getResults={getResults as (market: string, stage?: number) => Promise<OddsRow[]>}
            getExportUrl={getExportUrl}
          />
        )}
      </div>
    </div>
  );
}

export default App;
