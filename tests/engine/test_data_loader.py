import pytest
from pathlib import Path
from engine.data_loader import load_all_data, DataLoadError
from engine.models import StageType

DATA_DIR = Path(__file__).parent.parent.parent / "data"


def test_load_riders():
    riders, _, _, _, _ = load_all_data(DATA_DIR)
    assert len(riders) == 15
    r = riders[1]
    assert r.rider.name == "Tadej Pogacar"
    assert r.sprint == 55
    assert r.climbing == 98


def test_load_stages():
    _, stages, _, _, _ = load_all_data(DATA_DIR)
    assert len(stages) == 21
    assert stages[9].type == StageType.TT
    assert stages[1].type == StageType.FLAT


def test_load_odds():
    _, _, odds, _, _ = load_all_data(DATA_DIR)
    assert 1 in odds
    assert odds[1]["gc_win"] == pytest.approx(1.80)


def test_missing_data_dir_raises():
    with pytest.raises(DataLoadError):
        load_all_data(Path("/nonexistent/path"))


def test_young_rider_eligible():
    riders, _, _, _, _ = load_all_data(DATA_DIR)
    assert all(not rs.rider.young_rider_eligible for rs in riders.values())


def test_young_rider_flag_consistent_with_birth_year():
    riders, _, _, _, _ = load_all_data(DATA_DIR)
    for rs in riders.values():
        if rs.rider.young_rider_eligible:
            assert rs.rider.birth_year >= 2003, (
                f"{rs.rider.name} is flagged young_rider_eligible "
                f"but birth_year={rs.rider.birth_year} < 2003"
            )
