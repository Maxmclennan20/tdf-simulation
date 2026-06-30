import { useState, useEffect, useCallback } from 'react';
import { api } from '../api/client';
import type { Rider, RiderUpdate } from '../api/types';

export function useRiders() {
  const [riders, setRiders] = useState<Rider[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getRiders().then(r => { setRiders(r); setLoading(false); });
  }, []);

  const updateRider = useCallback(async (id: number, update: RiderUpdate) => {
    const updated = await api.updateRider(id, update);
    setRiders(prev => prev.map(r => r.rider_id === id ? updated : r));
  }, []);

  return { riders, loading, updateRider };
}
