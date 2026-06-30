import { useState } from 'react';
import type { OddsRow } from '../api/types';

interface Props {
  rows: OddsRow[];
  extraColumns?: { key: string; label: string }[];
}

type SortDir = 'asc' | 'desc';

const COL_LABELS: Record<string, string> = {
  name: 'Rider',
  team: 'Team',
  win_pct: 'Win %',
  decimal_odds: 'Decimal',
  fractional_odds: 'Fractional',
  podium_pct: 'Podium %',
  stage: 'Stage',
};

function ProbBar({ pct }: { pct: number }) {
  const color = pct > 0.2 ? 'bg-amber-400' : pct > 0.08 ? 'bg-blue-500' : 'bg-gray-600';
  return (
    <div className="flex items-center gap-2">
      <div className="w-20 h-1.5 bg-gray-700 rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${Math.min(pct * 100, 100)}%` }} />
      </div>
      <span className="text-xs font-mono text-gray-300 w-10 text-right">{(pct * 100).toFixed(1)}%</span>
    </div>
  );
}

export function OddsTable({ rows, extraColumns = [] }: Props) {
  const [sortKey, setSortKey] = useState<keyof OddsRow>('win_pct');
  const [dir, setDir] = useState<SortDir>('desc');

  const sorted = [...rows].sort((a, b) => {
    const av = a[sortKey] ?? 0, bv = b[sortKey] ?? 0;
    return dir === 'desc' ? (av < bv ? 1 : -1) : (av > bv ? 1 : -1);
  });

  const toggleSort = (key: keyof OddsRow) => {
    if (sortKey === key) setDir(d => d === 'desc' ? 'asc' : 'desc');
    else { setSortKey(key); setDir('desc'); }
  };

  const allCols = ['name', 'team', 'win_pct', 'decimal_odds', 'fractional_odds',
    ...extraColumns.map(c => c.key)];

  const SortIcon = ({ col }: { col: string }) => {
    if (sortKey !== col) return <span className="text-gray-700 ml-1">↕</span>;
    return <span className="text-amber-400 ml-1">{dir === 'desc' ? '↓' : '↑'}</span>;
  };

  if (rows.length === 0) {
    return <p className="text-gray-500 text-sm py-8 text-center">No data for this market.</p>;
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm border-collapse">
        <thead>
          <tr className="border-b border-border">
            <th className="w-8 px-3 py-2 text-left text-[10px] font-medium text-gray-500 uppercase">#</th>
            {allCols.map(col => (
              <th
                key={col}
                onClick={() => toggleSort(col as keyof OddsRow)}
                className="px-3 py-2 text-left text-[10px] font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:text-gray-300 transition-colors select-none"
              >
                {COL_LABELS[col] ?? col}
                <SortIcon col={col} />
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {sorted.map((row, i) => {
            const isPodium = i < 3;
            return (
              <tr
                key={row.rider_id + String(row.stage ?? '')}
                className={`border-b border-border/40 transition-colors hover:bg-card/60 ${
                  i === 0 ? 'bg-amber-950/20' : isPodium ? 'bg-card/20' : ''
                }`}
              >
                <td className="px-3 py-2 text-center">
                  {i === 0 ? (
                    <span className="inline-block w-5 h-5 rounded-full bg-amber-400 text-black text-[10px] font-bold flex items-center justify-center">1</span>
                  ) : i === 1 ? (
                    <span className="text-gray-400 text-xs font-mono">2</span>
                  ) : i === 2 ? (
                    <span className="text-orange-600 text-xs font-mono">3</span>
                  ) : (
                    <span className="text-gray-600 text-xs font-mono">{i + 1}</span>
                  )}
                </td>
                <td className={`px-3 py-2 font-medium ${i === 0 ? 'text-white' : 'text-gray-200'}`}>{row.name}</td>
                <td className="px-3 py-2 text-gray-400 text-xs">{row.team}</td>
                <td className="px-3 py-2">
                  <ProbBar pct={row.win_pct} />
                </td>
                <td className="px-3 py-2 font-mono text-sm text-gray-200">{row.decimal_odds}</td>
                <td className="px-3 py-2 font-mono text-xs text-amber-400/80">{row.fractional_odds}</td>
                {extraColumns.map(c => (
                  <td key={c.key} className="px-3 py-2 text-gray-300 text-xs">
                    {c.key.includes('pct')
                      ? `${((Number((row as unknown as Record<string, unknown>)[c.key]) || 0) * 100).toFixed(1)}%`
                      : String((row as unknown as Record<string, unknown>)[c.key] ?? '')}
                  </td>
                ))}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
