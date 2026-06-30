import { useRiders } from './hooks/useRiders';
import { useSimulation } from './hooks/useSimulation';
import { ControlsPanel } from './components/ControlsPanel';
import { ResultsDashboard } from './components/ResultsDashboard';
import type { OddsRow } from './api/types';

function App() {
  const { riders, loading, updateRider } = useRiders();
  const { state, run, getResults, getExportUrl } = useSimulation();

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full bg-surface">
        <div className="text-gray-400 text-sm animate-pulse">Loading riders…</div>
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
            <h1 className="text-white font-semibold text-sm leading-tight">Tour de France 2026</h1>
            <p className="text-gray-500 text-xs">Monte Carlo Simulation · 20,000 iterations</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {state === 'running' && (
            <span className="flex items-center gap-2 text-amber-400 text-xs">
              <span className="inline-block w-2 h-2 rounded-full bg-amber-400 animate-ping" />
              Simulating…
            </span>
          )}
          {state === 'complete' && (
            <span className="flex items-center gap-2 text-emerald-400 text-xs">
              <span className="inline-block w-2 h-2 rounded-full bg-emerald-400" />
              Results ready
            </span>
          )}
          {state === 'error' && (
            <span className="text-red-400 text-xs">Simulation failed</span>
          )}
        </div>
      </header>

      {/* Body */}
      <div className="flex flex-1 overflow-hidden">
        <ControlsPanel
          riders={riders}
          onUpdate={updateRider}
          onRun={() => run()}
          simState={state}
        />
        <ResultsDashboard
          simComplete={state === 'complete'}
          getResults={getResults as (market: string, stage?: number) => Promise<OddsRow[]>}
          getExportUrl={getExportUrl}
        />
      </div>
    </div>
  );
}

export default App;
