import pytest
from engine.models import Rider, Stage, RiderState, StageType


def test_rider_model():
    r = Rider(rider_id=1, name="Test Rider", team="Team A",
              nationality="GBR", birth_year=2000, uci_ranking=5,
              young_rider_eligible=False)
    assert r.rider_id == 1
    assert r.name == "Test Rider"


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
