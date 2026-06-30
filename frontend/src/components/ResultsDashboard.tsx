import { useState, useEffect } from 'react';
import type { OddsRow, StageSummaryEntry } from '../api/types';
import { OddsTable } from './OddsTable';
import { StageSummaryView } from './StageSummaryView';
import { DownloadButton } from './DownloadButton';
import { api } from '../api/client';

type Tab = 'gc' | 'gc_podium' | 'stage_summary' | 'stages' | 'points_jersey' | 'kom' | 'young_rider' | 'head_to_head';

const TABS: { key: Tab; label: string }[] = [
  { key: 'gc', label: 'GC' },
  { key: 'gc_podium', label: 'Podium' },
  { key: 'stage_summary', label: 'Stage Summary' },
  { key: 'stages', label: 'Stage Win Odds' },
  { key: 'points_jersey', label: 'Points' },
  { key: 'kom', label: 'KOM' },
  { key: 'young_rider', label: 'Young Rider' },
  { key: 'head_to_head', label: 'H2H' },
];

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
  const [stageSummary, setStageSummary] = useState<StageSummaryEntry[]>([]);
  const [selectedStage, setSelectedStage] = useState<number | undefined>(undefined);
  const [loading, setLoading] = useState(false);

  // Extract job ID from the export URL (reuses existing hook without needing a new prop)
  const jobId = simComplete ? getExportUrl('gc').split('/export/')[1]?.split('/')[0] : null;

  useEffect(() => {
    if (!simComplete || !jobId) return;
    if (activeTab === 'stage_summary') {
      setLoading(true);
      api.getStageSummary(jobId)
        .then(setStageSummary)
        .catch(() => setStageSummary([]))
        .finally(() => setLoading(false));
      return;
    }
    setLoading(true);
    if (activeTab === 'head_to_head') {
      getResults('head_to_head')
        .then(r => setH2hRows(r as unknown as H2HRow[]))
        .catch(() => setH2hRows([]))
        .finally(() => setLoading(false));
    } else {
      const stage = activeTab === 'stages' ? selectedStage : undefined;
      getResults(activeTab, stage)
        .then(setRows)
        .catch(() => setRows([]))
        .finally(() => setLoading(false));
    }
  }, [simComplete, activeTab, selectedStage, getResults, jobId]);

  if (!simComplete) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center gap-4 bg-surface">
        <div className="w-16 h-16 rounded-full border-2 border-border flex items-center justify-center">
          <svg className="w-7 h-7 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
              d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
        </div>
        <div className="text-center">
          <p className="text-gray-400 text-sm font-medium">No results yet</p>
          <p className="text-gray-600 text-xs mt-1">Run a simulation to generate betting odds</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-1 flex-col overflow-hidden bg-surface">
      {/* Tabs */}
      <div className="flex items-center gap-1 px-4 pt-3 pb-0 border-b border-border shrink-0">
        {TABS.map(t => (
          <button
            key={t.key}
            onClick={() => setActiveTab(t.key)}
            className={`px-4 py-2 text-xs font-medium rounded-t transition-colors ${
              activeTab === t.key
                ? 'text-white bg-card border border-border border-b-card -mb-px'
                : 'text-gray-500 hover:text-gray-300'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Toolbar */}
      <div className="flex items-center justify-between px-4 py-2.5 bg-card/30 border-b border-border shrink-0">
        <div className="flex items-center gap-3">
          {activeTab === 'stages' && (
            <div className="flex items-center gap-2">
              <label className="text-xs text-gray-500">Stage</label>
              <select
                value={selectedStage ?? ''}
                onChange={e => setSelectedStage(e.target.value ? Number(e.target.value) : undefined)}
                className="text-xs bg-card border border-border rounded px-2 py-1 text-gray-300 focus:outline-none focus:border-amber-400/50"
              >
                <option value="">All Stages</option>
                {Array.from({ length: 21 }, (_, i) => i + 1).map(n => (
                  <option key={n} value={n}>Stage {n}</option>
                ))}
              </select>
            </div>
          )}
          {loading && <span className="text-xs text-gray-500 animate-pulse">Loading…</span>}
        </div>
        {activeTab !== 'head_to_head' && activeTab !== 'stage_summary' && (
          <DownloadButton
            url={getExportUrl(activeTab, activeTab === 'stages' ? selectedStage : undefined)}
            label={`Export ${TABS.find(t => t.key === activeTab)?.label} CSV`}
          />
        )}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4">
        {activeTab === 'head_to_head' ? (
          <HeadToHeadView rows={h2hRows} />
        ) : activeTab === 'stage_summary' ? (
          <StageSummaryView stages={stageSummary} />
        ) : (
          <OddsTable
            rows={rows}
            extraColumns={
              activeTab === 'gc'
                ? [
                    { key: 'podium_pct', label: 'Top 3 %' },
                    { key: 'top6_pct', label: 'Top 6 %' },
                    { key: 'top10_pct', label: 'Top 10 %' },
                    { key: 'top20_pct', label: 'Top 20 %' },
                    { key: 'top40_pct', label: 'Top 40 %' },
                  ]
                : activeTab === 'gc_podium'
                ? [{ key: 'podium_pct', label: 'Top 3 %' }]
                : activeTab === 'stages' && selectedStage != null
                ? [{ key: 'stage', label: 'Stage' }]
                : []
            }
          />
        )}
      </div>
    </div>
  );
}

function HeadToHeadView({ rows }: { rows: H2HRow[] }) {
  const [r1, setR1] = useState('');
  const [r2, setR2] = useState('');

  const ids = [...new Set(rows.map(r => r.rider1_id))];
  const match = rows.find(r =>
    (r.rider1_id === Number(r1) && r.rider2_id === Number(r2)) ||
    (r.rider1_id === Number(r2) && r.rider2_id === Number(r1))
  );

  const p1 = match ? (match.rider1_id === Number(r1) ? match.p1 : match.p2) : 0;
  const p2 = match ? (match.rider1_id === Number(r2) ? match.p1 : match.p2) : 0;

  const selectClass = "text-sm bg-card border border-border rounded px-3 py-1.5 text-gray-300 focus:outline-none focus:border-amber-400/50 min-w-[140px]";

  return (
    <div className="max-w-md">
      <p className="text-xs text-gray-500 mb-4">GC head-to-head win probability based on simulation results.</p>
      <div className="flex items-center gap-3 mb-6">
        <select value={r1} onChange={e => setR1(e.target.value)} className={selectClass}>
          <option value="">Select Rider 1</option>
          {ids.map(id => <option key={id} value={id}>{id}</option>)}
        </select>
        <span className="text-gray-600 text-sm font-medium">vs</span>
        <select value={r2} onChange={e => setR2(e.target.value)} className={selectClass}>
          <option value="">Select Rider 2</option>
          {ids.map(id => <option key={id} value={id}>{id}</option>)}
        </select>
      </div>

      {match && r1 && r2 && (
        <div className="bg-card border border-border rounded-lg p-4 space-y-3">
          {[{ id: r1, prob: p1 }, { id: r2, prob: p2 }].map(({ id, prob }) => (
            <div key={id}>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-gray-300">Rider {id}</span>
                <span className={`font-mono font-semibold ${prob > 0.5 ? 'text-amber-400' : 'text-gray-400'}`}>
                  {(prob * 100).toFixed(1)}%
                </span>
              </div>
              <div className="h-2 bg-gray-800 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all ${prob > 0.5 ? 'bg-amber-400' : 'bg-gray-500'}`}
                  style={{ width: `${prob * 100}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
