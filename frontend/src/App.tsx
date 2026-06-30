import { useRiders } from './hooks/useRiders';
import { useSimulation } from './hooks/useSimulation';
import { ControlsPanel } from './components/ControlsPanel';
import { ResultsDashboard } from './components/ResultsDashboard';
import type { OddsRow } from './api/types';

function App() {
  const { riders, loading, updateRider } = useRiders();
  const { state, run, getResults, getExportUrl } = useSimulation();

  if (loading) return <div style={{ padding: 24 }}>Loading riders…</div>;

  return (
    <div style={{ display: 'flex', height: '100vh', fontFamily: 'sans-serif' }}>
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
  );
}

export default App;
