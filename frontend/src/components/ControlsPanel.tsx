import { useRef } from 'react';
import type { Rider, RiderUpdate } from '../api/types';
import { RiderRow } from './RiderRow';
import { api } from '../api/client';

interface Props {
  riders: Rider[];
  onUpdate: (id: number, update: RiderUpdate) => void;
}

export function ControlsPanel({ riders, onUpdate }: Props) {
  const fileRef = useRef<HTMLInputElement>(null);

  const handleImport = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      await api.importOdds(file);
      alert('Odds imported and calibration updated');
    } catch (err: unknown) {
      alert(`Import failed: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
    e.target.value = '';
  };

  const activeCount = riders.filter(r => !r.dns && !r.dnf).length;

  return (
    <div className="flex flex-col h-full bg-panel overflow-hidden">
      {/* Panel header */}
      <div className="px-4 py-3 border-b border-border shrink-0">
        <div className="flex items-center justify-between">
          <p className="text-gray-500 text-xs">{activeCount} of {riders.length} active</p>
          <div className="flex gap-2">
            <button
              onClick={() => fileRef.current?.click()}
              className="px-3 py-1.5 text-xs rounded bg-card border border-border text-gray-300 hover:text-white hover:border-gray-500 transition-colors"
            >
              Import Odds CSV
            </button>
            <input ref={fileRef} type="file" accept=".csv" className="hidden" onChange={handleImport} />
          </div>
        </div>
      </div>

      {/* Rider table */}
      <div className="flex-1 overflow-y-auto">
        <table className="w-full table-fixed border-collapse text-xs">
          <thead className="sticky top-0 z-10 bg-panel">
            <tr className="border-b border-border">
              <th className="text-left py-2 pl-3 pr-1 text-[10px] font-semibold text-gray-500 uppercase tracking-wider w-48">Name</th>
              <th className="text-left py-2 px-1 text-[10px] font-semibold text-gray-500 uppercase tracking-wider w-56">Team</th>
              <th className="text-center py-2 px-0.5 text-[10px] font-semibold text-gray-500 uppercase tracking-wider w-16">SPR</th>
              <th className="text-center py-2 px-0.5 text-[10px] font-semibold text-gray-500 uppercase tracking-wider w-16">CLB</th>
              <th className="text-center py-2 px-0.5 text-[10px] font-semibold text-gray-500 uppercase tracking-wider w-16">TT</th>
              <th className="text-center py-2 px-0.5 text-[10px] font-semibold text-gray-500 uppercase tracking-wider w-16">GC</th>
              <th className="text-center py-2 px-1 text-[10px] font-semibold text-gray-500 uppercase tracking-wider w-16">Form</th>
              <th className="text-center py-2 px-1 text-[10px] font-semibold text-red-500/70 uppercase tracking-wider w-12">DNS</th>
              <th className="text-center py-2 px-1 text-[10px] font-semibold text-orange-500/70 uppercase tracking-wider w-12">DNF</th>
            </tr>
          </thead>
          <tbody>
            {riders.map(r => (
              <RiderRow key={r.rider_id} rider={r} onUpdate={onUpdate} />
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
