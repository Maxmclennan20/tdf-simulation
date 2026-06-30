import { useState, useEffect } from 'react';
import type { OddsRow } from '../api/types';
import { OddsTable } from './OddsTable';
import { DownloadButton } from './DownloadButton';

type Tab = 'gc' | 'gc_podium' | 'stages' | 'points_jersey' | 'kom' | 'young_rider' | 'head_to_head';
const TABS: Tab[] = ['gc', 'gc_podium', 'stages', 'points_jersey', 'kom', 'young_rider', 'head_to_head'];

interface Props {
  simComplete: boolean;
  getResults: (market: string, stage?: number) => Promise<OddsRow[]>;
  getExportUrl: (market: string, stage?: number) => string;
}

interface H2HRow {
  rider1_id: number;
  rider2_id: number;
  p1: number;
  p2: number;
}

export function ResultsDashboard({ simComplete, getResults, getExportUrl }: Props) {
  const [activeTab, setActiveTab] = useState<Tab>('gc');
  const [rows, setRows] = useState<OddsRow[]>([]);
  const [h2hRows, setH2hRows] = useState<H2HRow[]>([]);
  const [selectedStage, setSelectedStage] = useState<number | undefined>(undefined);

  useEffect(() => {
    if (!simComplete) return;
    if (activeTab === 'head_to_head') {
      getResults('head_to_head').then(r => setH2hRows(r as unknown as H2HRow[])).catch(() => setH2hRows([]));
    } else {
      const stage = activeTab === 'stages' ? selectedStage : undefined;
      getResults(activeTab, stage).then(setRows).catch(() => setRows([]));
    }
  }, [simComplete, activeTab, selectedStage, getResults]);

  if (!simComplete) {
    return (
      <div style={{ flex: 1, padding: 24, color: '#888' }}>
        Run a simulation to see results.
      </div>
    );
  }

  return (
    <div style={{ flex: 1, padding: 16, overflowY: 'auto' }}>
      <div style={{ display: 'flex', gap: 6, marginBottom: 12 }}>
        {TABS.map(t => (
          <button key={t} onClick={() => setActiveTab(t)}
                  style={{ fontWeight: activeTab === t ? 'bold' : 'normal' }}>
            {t.replace('_', ' ').toUpperCase()}
          </button>
        ))}
      </div>

      {activeTab === 'stages' && (
        <div style={{ marginBottom: 8 }}>
          <label>Stage: </label>
          <select value={selectedStage ?? ''} onChange={e =>
            setSelectedStage(e.target.value ? Number(e.target.value) : undefined)}>
            <option value="">All Stages</option>
            {Array.from({ length: 21 }, (_, i) => i + 1).map(n => (
              <option key={n} value={n}>Stage {n}</option>
            ))}
          </select>
        </div>
      )}

      <div style={{ marginBottom: 8 }}>
        <DownloadButton
          url={getExportUrl(activeTab, activeTab === 'stages' ? selectedStage : undefined)}
          label={`Download ${activeTab} CSV`}
        />
      </div>

      {activeTab === 'head_to_head' ? (
        <HeadToHeadView rows={h2hRows} />
      ) : (
        <OddsTable
          rows={rows}
          extraColumns={activeTab === 'gc_podium'
            ? [{ key: 'podium_pct', label: 'Podium %' }]
            : activeTab === 'stages' && selectedStage != null
            ? [{ key: 'stage', label: 'Stage' }]
            : []}
        />
      )}
    </div>
  );
}

function HeadToHeadView({ rows }: { rows: H2HRow[] }) {
  const [r1, setR1] = useState('');
  const [r2, setR2] = useState('');

  const ids1 = [...new Set(rows.map(r => r.rider1_id))];
  const match = rows.find(r =>
    (r.rider1_id === Number(r1) && r.rider2_id === Number(r2)) ||
    (r.rider1_id === Number(r2) && r.rider2_id === Number(r1))
  );

  return (
    <div>
      <p style={{ color: '#666', fontSize: 12 }}>GC head-to-head only.</p>
      <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
        <select value={r1} onChange={e => setR1(e.target.value)}>
          <option value="">Rider 1</option>
          {ids1.map(id => <option key={id} value={id}>{id}</option>)}
        </select>
        <select value={r2} onChange={e => setR2(e.target.value)}>
          <option value="">Rider 2</option>
          {ids1.map(id => <option key={id} value={id}>{id}</option>)}
        </select>
      </div>
      {match && (
        <table style={{ borderCollapse: 'collapse' }}>
          <thead><tr><th>Rider ID</th><th>Win Probability</th></tr></thead>
          <tbody>
            <tr>
              <td style={{ padding: '4px 12px' }}>{r1}</td>
              <td style={{ padding: '4px 12px' }}>
                {((match.rider1_id === Number(r1) ? match.p1 : match.p2) * 100).toFixed(1)}%
              </td>
            </tr>
            <tr>
              <td style={{ padding: '4px 12px' }}>{r2}</td>
              <td style={{ padding: '4px 12px' }}>
                {((match.rider1_id === Number(r2) ? match.p1 : match.p2) * 100).toFixed(1)}%
              </td>
            </tr>
          </tbody>
        </table>
      )}
    </div>
  );
}
