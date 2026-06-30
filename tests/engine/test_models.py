import pytest
from engine.models import (
    Rider, Stage, RiderState, StageType,
    StageResult, IterationResult, RiderOdds, AggregatedResults,
)


def test_rider_model():
    r = Rider(rider_id=1, name="Test Rider", team="Team A",
              nationality="GBR", birth_year=2000, uci_ranking=5,
              young_rider_eligible=False)
    assert r.rider_id == 1
    assert r.name == "Test Rider"
    assert r.team == "Team A"
    assert r.nationality == "GBR"
    assert r.birth_year == 2000
    assert r.uci_ranking == 5
    assert r.young_rider_eligible is False


def test_stage_type_enum():
    assert StageType.FLAT.value == "flat"
    assert StageType.MOUNTAIN.value == "mountain"
    assert StageType.TT.value == "tt"
    assert StageType.HILLY.value == "hilly"


def test_rider_state_defaults():
    r = Rider(rider_id=1, name="X", team="Y", nationality="Z",
              birth_year=1998, uci_ranking=10, young_rider_eligible=False)
    state = RiderState(rider=r, sprint=70, climbing=80, tt=65, gc=75)
    assert state.form == 1.0
    assert state.dns is False
    assert state.dnf is False


def test_rider_state_active():
    r = Rider(rider_id=1, name="X", team="Y", nationality="Z",
              birth_year=1998, uci_ranking=10, young_rider_eligible=False)
    state = RiderState(rider=r, sprint=70, climbing=80, tt=65, gc=75)
    assert state.is_active() is True
    state.dns = True
    assert state.is_active() is False
    state.dns = False
    state.dnf = True
    assert state.is_active() is False


def test_stage_construction():
    s = Stage(stage=1, start="Lille", finish="Paris", distance=180.5, type=StageType.FLAT)
    assert s.stage == 1
    assert s.type == StageType.FLAT
    assert s.key_climbs == []


def test_stage_result_construction():
    sr = StageResult(stage=1, winner_id=42, top3_ids=[42, 7, 3], time_gaps={42: 0.0, 7: 4.5})
    assert sr.winner_id == 42
    assert sr.top3_ids[0] == 42


def test_iteration_result_construction():
    ir = IterationResult(
        stage_results=[],
        gc_times={1: 0.0},
        points_scores={1: 10},
        kom_scores={1: 5},
        dnf_ids=set(),
    )
    assert ir.gc_times == {1: 0.0}
    assert ir.dnf_ids == set()


def test_rider_odds_construction():
    odds = RiderOdds(
        rider_id=1, name="Test Rider", team="Team A",
        win_pct=0.15, decimal_odds=6.5, fractional_odds="11/2",
    )
    assert odds.win_pct == 0.15
    assert odds.podium_pct is None


def test_aggregated_results_construction():
    ar = AggregatedResults(
        gc=[], gc_podium=[], stages={}, stages_all=[],
        points_jersey=[], kom=[], young_rider=[], head_to_head={},
    )
    assert ar.gc == []
    assert ar.head_to_head == {}
