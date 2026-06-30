export interface Rider {
  rider_id: number;
  name: string;
  team: string;
  nationality: string;
  sprint: number;
  climbing: number;
  tt: number;
  gc: number;
  form: number;
  dns: boolean;
  dnf: boolean;
  young_rider_eligible: boolean;
}

export interface RiderUpdate {
  sprint?: number;
  climbing?: number;
  tt?: number;
  gc?: number;
  form?: number;
  dns?: boolean;
  dnf?: boolean;
}

export interface Stage {
  stage: number;
  start: string;
  finish: string;
  distance: number;
  type: 'flat' | 'hilly' | 'mountain' | 'tt';
  key_climbs: string[];
}

export interface OddsRow {
  rider_id: number;
  name: string;
  team: string;
  win_pct: number;
  podium_pct?: number;
  top6_pct?: number;
  top10_pct?: number;
  top20_pct?: number;
  top40_pct?: number;
  decimal_odds: number;
  fractional_odds: string;
  stage?: number;
}

export interface StageSummaryEntry {
  stage: number;
  type: 'flat' | 'hilly' | 'mountain' | 'tt';
  finish: string;
  distance: number;
  key_climbs: string[];
  top5: { rider_id: number; name: string; team: string; win_pct: number }[];
}

export interface JobStatus {
  job_id: string;
  status: 'pending' | 'running' | 'complete' | 'failed';
}

export type Market = 'gc' | 'gc_podium' | 'stages' | 'points_jersey' | 'kom' | 'young_rider' | 'head_to_head';

export interface H2HResult {
  rider1_id: number;
  rider2_id: number;
  p1: number;
  p2: number;
}
