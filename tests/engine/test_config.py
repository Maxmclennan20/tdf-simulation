from engine.config import STAGE_FACTORS, TDF_POINTS_SCALE, KOM_POINTS
from engine.models import StageType


def test_stage_factors_sum_to_one():
    for stage_type, factors in STAGE_FACTORS.items():
        total = factors["primary"] + factors["secondary"]
        assert abs(total - 1.0) < 1e-9, f"{stage_type} factors don't sum to 1.0"


def test_all_stage_types_covered():
    for st in StageType:
        assert st in STAGE_FACTORS, f"{st} missing from STAGE_FACTORS"


def test_points_scale_winner():
    assert TDF_POINTS_SCALE[1] == 50


def test_kom_points_hc():
    assert KOM_POINTS["HC"][1] == 20
