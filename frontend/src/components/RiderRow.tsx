import type { Rider, RiderUpdate } from '../api/types';

interface Props {
  rider: Rider;
  onUpdate: (id: number, update: RiderUpdate) => void;
}

const RATINGS: (keyof Pick<Rider, 'sprint' | 'climbing' | 'tt' | 'gc'>)[] =
  ['sprint', 'climbing', 'tt', 'gc'];

function RatingBadge({ value }: { value: number }) {
  const color =
    value >= 85 ? 'text-amber-400' :
    value >= 70 ? 'text-emerald-400' :
    value >= 55 ? 'text-blue-400' :
    'text-gray-500';
  return <span className={`text-xs font-mono font-semibold ${color}`}>{value}</span>;
}

export function RiderRow({ rider, onUpdate }: Props) {
  const inactive = rider.dns || rider.dnf;

  return (
    <div
      className={`grid items-center px-2 py-1.5 hover:bg-card/50 transition-colors text-xs ${inactive ? 'opacity-40' : ''}`}
      style={{ gridTemplateColumns: '1fr 1fr 2.5rem 2.5rem 2.5rem 2.5rem 7rem 3rem 3rem' }}
    >
      {/* Name */}
      <span className="text-white font-medium truncate pr-1" title={rider.name}>{rider.name}</span>

      {/* Team */}
      <span className="text-gray-400 truncate pr-1" title={rider.team}>{rider.team}</span>

      {/* Ratings */}
      {RATINGS.map(attr => (
        <div key={attr} className="flex flex-col items-center gap-0.5">
          <RatingBadge value={rider[attr]} />
          <input
            type="number" min={0} max={100} step={1}
            value={rider[attr]}
            className="w-9 text-center text-[10px] bg-card border border-border rounded text-gray-300 focus:outline-none focus:border-amber-400/60 px-0.5"
            onChange={e => onUpdate(rider.rider_id, { [attr]: Number(e.target.value) })}
          />
        </div>
      ))}

      {/* Form slider */}
      <div className="flex flex-col items-center gap-0.5 px-1">
        <span className={`text-[10px] font-mono font-semibold ${
          rider.form > 1.1 ? 'text-emerald-400' :
          rider.form < 0.9 ? 'text-red-400' :
          'text-gray-400'
        }`}>{rider.form.toFixed(2)}</span>
        <input
          type="range" min={0.5} max={1.5} step={0.05}
          value={rider.form}
          className="w-full h-1 cursor-pointer"
          style={{ accentColor: rider.form < 0.85 ? '#f87171' : rider.form > 1.1 ? '#34d399' : '#f59e0b' }}
          onChange={e => onUpdate(rider.rider_id, { form: Number(e.target.value) })}
        />
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
