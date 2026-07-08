import type { StageSummaryEntry } from '../api/types';

interface Props {
  stages: StageSummaryEntry[];
}

const TYPE_BADGE: Record<string, { label: string; color: string }> = {
  mountain: { label: 'MTN', color: 'text-blue-700 bg-blue-100' },
  flat:     { label: 'FLT', color: 'text-emerald-700 bg-emerald-100' },
  hilly:    { label: 'HLY', color: 'text-amber-700 bg-amber-100' },
  tt:       { label: 'TT',  color: 'text-purple-700 bg-purple-100' },
};

export function StageSummaryView({ stages }: Props) {
  if (stages.length === 0) {
    return <p className="text-gray-500 text-sm py-8 text-center">No stage data available.</p>;
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse text-xs">
        <thead>
          <tr className="border-b border-border">
            <th className="text-left py-2 px-3 text-[10px] font-semibold text-gray-500 uppercase tracking-wider w-12">Stage</th>
            <th className="text-left py-2 px-2 text-[10px] font-semibold text-gray-500 uppercase tracking-wider w-12">Type</th>
            <th className="text-left py-2 px-2 text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Finish</th>
            <th className="text-right py-2 px-2 text-[10px] font-semibold text-gray-500 uppercase tracking-wider w-14">Km</th>
            <th className="text-left py-2 px-3 text-[10px] font-semibold text-amber-600/80 uppercase tracking-wider">Favourite</th>
            <th className="text-left py-2 px-3 text-[10px] font-semibold text-gray-500 uppercase tracking-wider">2nd</th>
            <th className="text-left py-2 px-3 text-[10px] font-semibold text-gray-500 uppercase tracking-wider">3rd</th>
            <th className="text-left py-2 px-3 text-[10px] font-semibold text-gray-500 uppercase tracking-wider">4th</th>
            <th className="text-left py-2 px-3 text-[10px] font-semibold text-gray-500 uppercase tracking-wider">5th</th>
          </tr>
        </thead>
        <tbody>
          {stages.map((s) => {
            const badge = TYPE_BADGE[s.type] ?? { label: s.type.toUpperCase(), color: 'text-gray-600 bg-gray-200' };
            return (
              <tr
                key={s.stage}
                className="border-b border-border/40 hover:bg-card/50 transition-colors"
              >
                <td className="py-1.5 px-3 font-mono text-gray-600 font-semibold">{s.stage}</td>
                <td className="py-1.5 px-2">
                  <span className={`inline-block px-1.5 py-0.5 rounded text-[9px] font-bold tracking-wider ${badge.color}`}>
                    {badge.label}
                  </span>
                </td>
                <td className="py-1.5 px-2">
                  <div className="text-gray-800 font-medium">{s.finish}</div>
                  {s.key_climbs.length > 0 && (
                    <div className="text-[9px] text-gray-400 truncate max-w-[160px]" title={s.key_climbs.join(', ')}>
                      {s.key_climbs.join(' · ')}
                    </div>
                  )}
                </td>
                <td className="py-1.5 px-2 text-right font-mono text-gray-500">{s.distance}</td>
                {[0, 1, 2, 3, 4].map((rank) => {
                  const rider = s.top5[rank];
                  if (!rider) return <td key={rank} className="py-1.5 px-3 text-gray-300">—</td>;
                  return (
                    <td key={rank} className="py-1.5 px-3">
                      <div className={rank === 0 ? 'text-gray-900 font-semibold' : 'text-gray-600'}>
                        {rider.name.split(' ').pop()}
                      </div>
                      <div className={`font-mono text-[9px] ${rank === 0 ? 'text-amber-600' : 'text-gray-400'}`}>
                        {(rider.win_pct * 100).toFixed(1)}%
                      </div>
                    </td>
                  );
                })}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
