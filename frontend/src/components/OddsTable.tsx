import { useState } from 'react';
import type { OddsRow } from '../api/types';

interface Props {
  rows: OddsRow[];
  extraColumns?: { key: string; label: string }[];
}

export function OddsTable({ rows, extraColumns = [] }: Props) {
  const [sortKey, setSortKey] = useState<keyof OddsRow>('win_pct');
  const [asc, setAsc] = useState(false);

  const sorted = [...rows].sort((a, b) => {
    const av = a[sortKey] ?? 0, bv = b[sortKey] ?? 0;
    return asc ? (av > bv ? 1 : -1) : (av < bv ? 1 : -1);
  });

  const toggleSort = (key: keyof OddsRow) => {
    if (sortKey === key) setAsc(a => !a);
    else { setSortKey(key); setAsc(false); }
  };

  return (
    <table style={{ borderCollapse: 'collapse', width: '100%', fontSize: 13 }}>
      <thead>
        <tr style={{ background: '#f0f0f0' }}>
          {['name', 'team', 'win_pct', 'decimal_odds', 'fractional_odds',
            ...extraColumns.map(c => c.key)].map(col => (
            <th key={col} onClick={() => toggleSort(col as keyof OddsRow)}
                style={{ cursor: 'pointer', padding: '4px 8px', textAlign: 'left' }}>
              {col.replace('_', ' ')}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {sorted.map((row, i) => (
          <tr key={row.rider_id + String(row.stage)}
              style={{ background: i < 3 ? '#fffbe6' : 'white' }}>
            <td style={{ padding: '3px 8px' }}>{row.name}</td>
            <td style={{ padding: '3px 8px' }}>{row.team}</td>
            <td style={{ padding: '3px 8px' }}>{(row.win_pct * 100).toFixed(1)}%</td>
            <td style={{ padding: '3px 8px' }}>{row.decimal_odds}</td>
            <td style={{ padding: '3px 8px' }}>{row.fractional_odds}</td>
            {extraColumns.map(c => (
              <td key={c.key} style={{ padding: '3px 8px' }}>
                {String((row as unknown as Record<string, unknown>)[c.key] ?? '')}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}
