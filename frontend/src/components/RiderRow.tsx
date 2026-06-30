import type { Rider, RiderUpdate } from '../api/types';

interface Props {
  rider: Rider;
  onUpdate: (id: number, update: RiderUpdate) => void;
}

const RATINGS: (keyof Pick<Rider, 'sprint' | 'climbing' | 'tt' | 'gc'>)[] =
  ['sprint', 'climbing', 'tt', 'gc'];

export function RiderRow({ rider, onUpdate }: Props) {
  const inactive = rider.dns || rider.dnf;

  return (
    <tr style={{ opacity: inactive ? 0.4 : 1 }}>
      <td>{rider.name}</td>
      <td>{rider.team}</td>
      {RATINGS.map(attr => (
        <td key={attr}>
          <input
            type="number" min={0} max={100} step={1}
            value={rider[attr]}
            style={{ width: 50 }}
            onChange={e => onUpdate(rider.rider_id, { [attr]: Number(e.target.value) })}
          />
        </td>
      ))}
      <td>
        <input
          type="range" min={0.5} max={1.5} step={0.05}
          value={rider.form}
          style={{ accentColor: rider.form < 0.85 ? 'orange' : undefined }}
          onChange={e => onUpdate(rider.rider_id, { form: Number(e.target.value) })}
        />
        <span style={{ marginLeft: 4 }}>{rider.form.toFixed(2)}</span>
      </td>
      <td>
        <input type="checkbox" checked={rider.dns}
          onChange={e => onUpdate(rider.rider_id, { dns: e.target.checked })} />
        DNS
      </td>
      <td>
        <input type="checkbox" checked={rider.dnf}
          onChange={e => onUpdate(rider.rider_id, { dnf: e.target.checked })} />
        DNF
      </td>
    </tr>
  );
}
