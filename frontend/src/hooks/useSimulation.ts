import { useState, useCallback, useRef } from 'react';
import { api } from '../api/client';

type SimState = 'idle' | 'running' | 'complete' | 'error';

export function useSimulation() {
  const [state, setState] = useState<SimState>('idle');
  const [jobId, setJobId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const stopPolling = () => {
    if (pollRef.current) clearInterval(pollRef.current);
    pollRef.current = null;
  };

  const run = useCallback(async (seed?: number) => {
    setState('running');
    setError(null);
    try {
      const job = await api.simulate(seed);
      setJobId(job.job_id);

      pollRef.current = setInterval(async () => {
        const status = await api.getJobStatus(job.job_id);
        if (status.status === 'complete') {
          stopPolling();
          setState('complete');
        } else if (status.status === 'failed') {
          stopPolling();
          setState('error');
          setError('Simulation failed');
        }
      }, 1000);
    } catch (e: unknown) {
      setState('error');
      setError(e instanceof Error ? e.message : 'Unknown error');
    }
  }, []);

  const getResults = useCallback(
    (market: string, stage?: number) =>
      jobId ? api.getResults(jobId, market, stage) : Promise.resolve([]),
    [jobId]
  );

  const getExportUrl = useCallback(
    (market: string, stage?: number) =>
      jobId ? api.getExportUrl(jobId, market, stage) : '',
    [jobId]
  );

  return { state, jobId, error, run, getResults, getExportUrl };
}
