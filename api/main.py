from __future__ import annotations
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from api.state import app_state
from api.routes import riders, stages, simulate, results, export, odds
from engine.data_loader import load_all_data
from engine.models import StageType
from engine.performance_model import apply_odds_calibration

DATA_DIR = Path(__file__).parent.parent / "data"


@asynccontextmanager
async def lifespan(app: FastAPI):
    r, s, o, _, _ = load_all_data(DATA_DIR)
    app_state.riders = r
    app_state.stages = s
    app_state.odds = o
    # GC win odds → calibration_factor used on mountain/TT stages
    apply_odds_calibration(app_state.riders, app_state.odds,
                           "gc_win", StageType.MOUNTAIN,
                           target_field="calibration_factor")
    # Stage win odds → stage_calibration_factor used on flat/hilly stages
    apply_odds_calibration(app_state.riders, app_state.odds,
                           "stage_win", StageType.FLAT,
                           target_field="stage_calibration_factor")
    yield


app = FastAPI(title="TdF 2026 Simulation", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    detail = exc.detail
    if isinstance(detail, dict) and "error" in detail:
        return JSONResponse(status_code=exc.status_code, content=detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": "http_error", "detail": str(detail)},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"error": "validation_error", "detail": str(exc)},
    )


app.include_router(riders.router)
app.include_router(stages.router)
app.include_router(simulate.router)
app.include_router(results.router)
app.include_router(export.router)
app.include_router(odds.router)
