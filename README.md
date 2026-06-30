# TdF 2026 Simulation

A Monte Carlo race simulation for the 2026 Tour de France. Runs 20,000 iterations of the full 21-stage race and generates betting odds for GC, stage wins, points jersey, KOM, young rider, and head-to-head markets.

## Features

- **20,000-iteration Monte Carlo simulation** of the full 2026 TdF route
- Real 2026 startlist — 173 riders across 23 teams
- Bookmaker odds calibration — GC win probabilities anchored to real market odds
- Stage-type modelling — separate weight functions for mountain, flat, hilly, and TT stages
- Log-normal time gaps on mountain and TT stages, tiered by rider rating
- Live rider editor — adjust ratings and form before running
- Markets: GC win, GC podium, stage wins (per stage + aggregate), points jersey, KOM, best young rider, head-to-head

## Stack

- **Backend**: Python 3.14, FastAPI, NumPy, pandas
- **Frontend**: React, TypeScript, Vite, Tailwind CSS v3

## Getting Started

**Prerequisites**: Python 3.14+, Node.js 18+

```bash
# Clone and set up Python environment
git clone https://github.com/Maxmclennan20/tdf-simulation.git
cd tdf-simulation
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Install frontend dependencies
cd frontend && npm install && cd ..

# Start both servers
./start.sh
```

Then open http://localhost:5173.

## Project Structure

```
engine/          Monte Carlo simulation core
  config.py      Stage factors, time gap parameters, points scales
  models.py      Pydantic data models
  performance_model.py  Stage weight calculation and odds calibration
  time_gaps.py   Log-normal time gap generation per stage type
  monte_carlo.py Full race simulation runner
  aggregator.py  Result aggregation and odds conversion

api/             FastAPI backend
  main.py        App setup and lifespan data loading
  routes/        Endpoints: /riders, /stages, /simulate, /results, /odds, /export
  state.py       In-memory app state and job tracking
  job_runner.py  Background simulation job execution

frontend/        React + Tailwind UI
  src/components/
    ControlsPanel.tsx   Rider editor with ratings, form, DNS/DNF
    ResultsDashboard.tsx  Tabbed odds tables by market

data/            CSV source files
  riders.csv           173 riders with team, nationality, birth year
  rider_ratings.csv    sprint/climbing/tt/gc ratings (0-100)
  stages.csv           21-stage 2026 route with stage types
  odds.csv             Real bookmaker GC and stage win odds
  historical_results.csv  Grand tour results for context
```

## How the Simulation Works

Each iteration simulates all 21 stages in order:

1. **Stage winner** is sampled from active riders weighted by their ratings for that stage type, form, and a calibration factor derived from bookmaker odds
2. **Time gaps** are generated from a log-normal distribution — mountain and TT stages only; flat and hilly stages produce bunch finishes (0 gap)
3. **GC time** accumulates across all stages; the rider with the lowest total time wins
4. Points, KOM, and young rider jerseys are tracked separately

After 20,000 iterations, win counts are converted to decimal and fractional odds.

## API

```
POST /simulate          Start a simulation job (returns job_id)
GET  /jobs/{id}/status  Poll job status (running / complete)
GET  /results/{id}/gc               GC win odds
GET  /results/{id}/gc_podium        GC podium odds
GET  /results/{id}/stages_all       Aggregate stage win odds
GET  /results/{id}/stages?stage=N   Per-stage odds
GET  /results/{id}/points_jersey
GET  /results/{id}/kom
GET  /results/{id}/young_rider
GET  /results/{id}/head_to_head
GET  /export/{id}       Download results as CSV
```
