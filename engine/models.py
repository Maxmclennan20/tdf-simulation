from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class StageType(str, Enum):
    FLAT = "flat"
    HILLY = "hilly"
    MOUNTAIN = "mountain"
    TT = "tt"


@dataclass
class Rider:
    rider_id: int
    name: str
    team: str
    nationality: str
    birth_year: int
    uci_ranking: int
    young_rider_eligible: bool


@dataclass
class Stage:
    stage: int
    start: str
    finish: str
    distance: float
    type: StageType
    key_climbs: list[str] = field(default_factory=list)


@dataclass
class RiderState:
    rider: Rider
    sprint: float
    climbing: float
    tt: float
    gc: float
    form: float = 1.0
    dns: bool = False
    dnf: bool = False
    calibration_factor: float = 1.0

    def is_active(self) -> bool:
        return not self.dns and not self.dnf


@dataclass
class StageResult:
    stage: int
    winner_id: int
    top3_ids: list[int]
    time_gaps: dict[int, float]  # rider_id -> seconds behind winner


@dataclass
class IterationResult:
    stage_results: list[StageResult]
    gc_times: dict[int, float]      # rider_id -> total seconds
    points_scores: dict[int, int]   # rider_id -> total points jersey points
    kom_scores: dict[int, int]      # rider_id -> total KOM points
    dnf_ids: set[int]


@dataclass
class RiderOdds:
    rider_id: int
    name: str
    team: str
    win_pct: float
    podium_pct: Optional[float]
    decimal_odds: float
    fractional_odds: str


@dataclass
class AggregatedResults:
    gc: list[RiderOdds]
    gc_podium: list[RiderOdds]
    stages: dict[int, list[RiderOdds]]   # stage_number -> odds list
    stages_all: list[RiderOdds]          # aggregated across all stages
    points_jersey: list[RiderOdds]
    kom: list[RiderOdds]
    young_rider: list[RiderOdds]
    head_to_head: dict[tuple[int, int], tuple[float, float]]  # (id1,id2) -> (p1,p2)
