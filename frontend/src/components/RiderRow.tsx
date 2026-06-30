import type { Rider, RiderUpdate } from '../api/types';

interface Props {
  rider: Rider;
  onUpdate: (id: number, update: RiderUpdate) => void;
}

const RATINGS: (keyof Pick<Rider, 'sprint' | 'climbing' | 'tt' | 'gc'>)[] =
  ['sprint', 'climbing', 'tt', 'gc'];

function ratingColor(value: number): string {
  if (value >= 85) return '#fbbf24'; // amber-400
  if (value >= 70) return '#34d399'; // emerald-400
  if (value >= 55) return '#60a5fa'; // blue-400
  return '#6b7280'; // gray-500
}

export function RiderRow({ rider, onUpdate }: Props) {
  const inactive = rider.dns || rider.dnf;

  return (
    <div
      className={`grid items-center px-2 py-0.5 hover:bg-card/50 transition-colors text-xs ${inactive ? 'opacity-40' : ''}`}
      style={{ gridTemplateColumns: '1fr 1fr 2.5rem 2.5rem 2.5rem 2.5rem 7rem 3rem 3rem' }}
    >
      {/* Name */}
      <span className="text-white font-medium truncate pr-1" title={rider.name}>{rider.name}</span>

      {/* Team */}
      <span className="text-gray-400 truncate pr-1" title={rider.team}>{rider.team}</span>

      {/* Ratings — single compact colored input per column */}
      {RATINGS.map(attr => (
        <input
          key={attr}
          type="number" min={0} max={100} step={1}
          value={rider[attr]}
          className="w-9 text-center text-[10px] font-mono font-semibold bg-card border border-border rounded focus:outline-none focus:border-amber-400/60 px-0.5"
          style={{ color: ratingColor(rider[attr]) }}
          onChange={e => onUpdate(rider.rider_id, { [attr]: Number(e.target.value) })}
        />
      ))}

      {/* Form slider */}
      <div className="flex items-center gap-1 px-1">
        <input
          type="range" min={0.5} max={1.5} step={0.05}
          value={rider.form}
          className="w-full h-1 cursor-pointer"
          style={{ accentColor: rider.form < 0.85 ? '#f87171' : rider.form > 1.1 ? '#34d399' : '#f59e0b' }}
          onChange={e => onUpdate(rider.rider_id, { form: Number(e.target.value) })}
        />
        <span className="text-[9px] font-mono w-6 text-right" style={{
          color: rider.form > 1.1 ? '#34d399' : rider.form < 0.9 ? '#f87171' : '#9ca3af'
        }}>{rider.form.toFixed(2)}</span>
      </div>

      {/* DNS */}
      <div className="flex justify-center">
        <input
          type="checkbox" checked={rider.dns}
          className="w-3.5 h-3.5 cursor-pointer accent-red-500"
          onChange={e => onUpdate(rider.rider_id, { dns: e.target.checked })}
        />
      </div>

      {/* DNF */}
      <div className="flex justify-center">
        <input
          type="checkbox" checked={rider.dnf}
          className="w-3.5 h-3.5 cursor-pointer accent-orange-500"
          onChange={e => onUpdate(rider.rider_id, { dnf: e.target.checked })}
        />
      </div>
    </div>
  );
}
