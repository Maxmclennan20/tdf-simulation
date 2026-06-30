import type { Rider, RiderUpdate } from '../api/types';

interface Props {
  rider: Rider;
  onUpdate: (id: number, update: RiderUpdate) => void;
}

const RATINGS: (keyof Pick<Rider, 'sprint' | 'climbing' | 'tt' | 'gc'>)[] =
  ['sprint', 'climbing', 'tt', 'gc'];

function ratingColor(value: number): string {
  if (value >= 85) return '#fbbf24';
  if (value >= 70) return '#34d399';
  if (value >= 55) return '#60a5fa';
  return '#6b7280';
}

export function RiderRow({ rider, onUpdate }: Props) {
  const inactive = rider.dns || rider.dnf;

  return (
    <tr className={`border-b border-border/40 hover:bg-card/50 transition-colors ${inactive ? 'opacity-40' : ''}`}>
      <td className="py-1 pl-3 pr-1 max-w-0 w-36">
        <span className="block truncate text-white font-medium text-xs" title={rider.name}>{rider.name}</span>
      </td>
      <td className="py-1 px-1 max-w-0 w-32">
        <span className="block truncate text-gray-400 text-xs" title={rider.team}>{rider.team}</span>
      </td>
      {RATINGS.map(attr => (
        <td key={attr} className="py-1 px-0.5 text-center">
          <input
            type="number" min={0} max={100} step={1}
            value={rider[attr]}
            className="w-10 text-center text-[10px] font-mono font-semibold bg-card border border-border rounded focus:outline-none focus:border-amber-400/60 px-0.5 py-0.5"
            style={{ color: ratingColor(rider[attr]) }}
            onChange={e => onUpdate(rider.rider_id, { [attr]: Number(e.target.value) })}
          />
        </td>
      ))}
      <td className="py-1 px-1 text-center">
        <input
          type="number" min={0.5} max={1.5} step={0.05}
          value={rider.form}
          className="w-12 text-center text-[10px] font-mono font-semibold bg-card border border-border rounded focus:outline-none focus:border-amber-400/60 px-0.5 py-0.5"
          style={{ color: rider.form > 1.1 ? '#34d399' : rider.form < 0.9 ? '#f87171' : '#9ca3af' }}
          onChange={e => onUpdate(rider.rider_id, { form: Number(e.target.value) })}
        />
      </td>
      <td className="py-1 px-1 text-center">
        <input
          type="checkbox" checked={rider.dns}
          className="w-3.5 h-3.5 cursor-pointer accent-red-500"
          onChange={e => onUpdate(rider.rider_id, { dns: e.target.checked })}
        />
      </td>
      <td className="py-1 px-1 text-center">
        <input
          type="checkbox" checked={rider.dnf}
          className="w-3.5 h-3.5 cursor-pointer accent-orange-500"
          onChange={e => onUpdate(rider.rider_id, { dnf: e.target.checked })}
        />
      </td>
    </tr>
  );
}
