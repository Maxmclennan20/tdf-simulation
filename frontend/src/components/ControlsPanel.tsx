import { useRef } from 'react';
import type { Rider, RiderUpdate } from '../api/types';
import { RiderRow } from './RiderRow';
import { api } from '../api/client';

interface Props {
  riders: Rider[];
  onUpdate: (id: number, update: RiderUpdate) => void;
  onRun: () => void;
  simState: 'idle' | 'running' | 'complete' | 'error';
}

export function ControlsPanel({ riders, onUpdate, onRun, simState }: Props) {
  const fileRef = useRef<HTMLInputElement>(null);

  const handleImport = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      await api.importOdds(file);
      alert('Odds imported successfully');
    } catch (err: unknown) {
      alert(`Import failed: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  };

  return (
    <div style={{ width: 420, overflowY: 'auto', borderRight: '1px solid #ccc', padding: 12 }}>
      <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
        <button onClick={onRun} disabled={simState === 'running'}>
          {simState === 'running' ? 'Simulating…' : 'Run Simulation'}
        </button>
        <button onClick={() => fileRef.current?.click()}>Import Odds CSV</button>
        <input ref={fileRef} type="file" accept=".csv" hidden onChange={handleImport} />
      </div>
      <table style={{ fontSize: 12, borderCollapse: 'collapse' }}>
        <thead>
          <tr>
            <th>Name</th><th>Team</th>
            <th>SPR</th><th>CLB</th><th>TT</th><th>GC</th>
            <th>Form</th><th colSpan={2}>Status</th>
          </tr>
        </thead>
        <tbody>
          {riders.map(r => (
            <RiderRow key={r.rider_id} rider={r} onUpdate={onUpdate} />
          ))}
        </tbody>
      </table>
    </div>
  );
}
