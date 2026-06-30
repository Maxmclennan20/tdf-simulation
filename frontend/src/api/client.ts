import type { Rider, RiderUpdate, Stage, OddsRow, JobStatus, H2HResult } from './types';

const BASE = 'http://localhost:8000';

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, options);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail ?? res.statusText);
  }
  return res.json();
}

export const api = {
  getRiders: () => apiFetch<Rider[]>('/riders'),
  updateRider: (id: number, update: RiderUpdate) =>
    apiFetch<Rider>(`/riders/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(update),
    }),
  getStages: () => apiFetch<Stage[]>('/stages'),
  simulate: (seed?: number) =>
    apiFetch<JobStatus>('/simulate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ seed: seed ?? null }),
    }),
  getJobStatus: (jobId: string) => apiFetch<JobStatus>(`/jobs/${jobId}/status`),
  getResults: (jobId: string, market: string, stage?: number) => {
    const params = stage != null ? `?stage=${stage}` : '';
    return apiFetch<OddsRow[] | H2HResult[]>(`/results/${jobId}/${market}${params}`);
  },
  getExportUrl: (jobId: string, market: string, stage?: number) => {
    const params = stage != null ? `?stage=${stage}` : '';
    return `${BASE}/export/${jobId}/${market}${params}`;
  },
  importOdds: (file: File) => {
    const form = new FormData();
    form.append('file', file);
    return apiFetch<{ message: string }>('/odds/import', { method: 'POST', body: form });
  },
};
