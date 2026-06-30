import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from api.state import app_state
from engine.data_loader import load_all_data
from engine.models import StageType
from engine.performance_model import apply_odds_calibration

DATA_DIR = Path(__file__).parent.parent.parent / "data"


@pytest.fixture(autouse=True)
def load_test_state():
    r, s, o, _, _ = load_all_data(DATA_DIR)
    app_state.riders = r
    app_state.stages = s
    app_state.odds = o
    app_state.current_job = None
    apply_odds_calibration(app_state.riders, app_state.odds,
                           "gc_win", StageType.MOUNTAIN)


@pytest.fixture
def client():
    from api.main import app
    return TestClient(app)
