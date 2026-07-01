from engine.models import StageType

# Stage blending factors: primary and secondary rating weights per stage type
STAGE_FACTORS: dict[StageType, dict[str, float]] = {
    StageType.FLAT:     {"primary": 1.00, "secondary": 0.00},  # pure sprint — no gc boost
    StageType.HILLY:    {"primary": 0.60, "secondary": 0.40},  # sprint + climbing (puncheurs)
    StageType.MOUNTAIN: {"primary": 0.75, "secondary": 0.25},
    StageType.TT:       {"primary": 0.80, "secondary": 0.20},
}

# Which ratings are primary/secondary per stage type
STAGE_RATING_MAP: dict[StageType, tuple[str, str]] = {
    StageType.FLAT:     ("sprint",   "sprint"),    # secondary unused (weight 0)
    StageType.HILLY:    ("sprint",   "climbing"),  # puncheur stages
    StageType.MOUNTAIN: ("climbing", "gc"),
    StageType.TT:       ("tt",       "gc"),
}

# Per-stage points scales for the 2026 Tour de France (official ASO classification).
# Stages are grouped by difficulty coefficient, not by our internal StageType.
_COEFF1  = {  # Flat (coefficient 1): stages 5, 7, 8, 11, 12 — top 18 finishers
    1: 70, 2: 50, 3: 40, 4: 35, 5: 30, 6: 26, 7: 24, 8: 22, 9: 20, 10: 18,
    11: 16, 12: 14, 13: 12, 14: 10, 15: 8, 16: 6, 17: 4, 18: 2,
}
_COEFF2  = {  # Slightly undulating (coefficient 2): stages 4, 13, 17, 21
    1: 50, 2: 30, 3: 20, 4: 18, 5: 16, 6: 14, 7: 12, 8: 10, 9: 8, 10: 7,
    11: 6, 12: 5, 13: 4, 14: 3, 15: 2,
}
_COEFF3P = {  # Hilly/mountain (coefficient 3, 4, 5): stages 2,3,6,9,10,14,15,18,19,20
    1: 30, 2: 25, 3: 22, 4: 19, 5: 17, 6: 15, 7: 13, 8: 11, 9: 9, 10: 7,
    11: 6, 12: 5, 13: 4, 14: 3, 15: 2,
}
_TT      = {  # Time trial: stages 1, 16
    1: 20, 2: 17, 3: 15, 4: 13, 5: 11, 6: 9, 7: 7, 8: 6, 9: 5, 10: 4,
    11: 3, 12: 2, 13: 1,
}

STAGE_POINTS_SCALE: dict[int, dict[int, int]] = {
    1:  _TT,     2:  _COEFF3P, 3:  _COEFF3P, 4:  _COEFF2,  5:  _COEFF1,
    6:  _COEFF3P, 7:  _COEFF1,  8:  _COEFF1,  9:  _COEFF3P, 10: _COEFF3P,
    11: _COEFF1,  12: _COEFF1,  13: _COEFF2,  14: _COEFF3P, 15: _COEFF3P,
    16: _TT,      17: _COEFF2,  18: _COEFF3P, 19: _COEFF3P, 20: _COEFF3P, 21: _COEFF2,
}

# Stages with a bunch sprint finish — finish ORDER is determined by sprint weights,
# not time gaps. Coefficient 1 (flat) and 2 (slightly undulating) only.
BUNCH_FINISH_STAGES: frozenset[int] = frozenset({4, 5, 7, 8, 11, 12, 13, 17, 21})

# Intermediate sprint bonus points (green jersey) — only on bunch-finish stages.
# Drawn separately using sprint-weighted probabilities.
INTERMEDIATE_SPRINT_STAGES: frozenset[int] = BUNCH_FINISH_STAGES
INTERMEDIATE_SPRINT_POINTS: dict[int, int] = {1: 20, 2: 13, 3: 8}

# KOM points: category -> {position: points}
KOM_POINTS: dict[str, dict[int, int]] = {
    "HC": {1: 20, 2: 14, 3: 10, 4: 6, 5: 4, 6: 2},
    "1":  {1: 10, 2:  8, 3:  6, 4: 4, 5: 2},
    "2":  {1:  5, 2:  3, 3:  2, 4: 1},
    "3":  {1:  2, 2:  1},
    "4":  {1:  1},
}

# Log-normal time gap parameters per stage type
# (mu, sigma) of the underlying normal distribution
# Applied per rider tier (higher-rated riders get lower mu)
TIME_GAP_PARAMS: dict[str, dict[str, tuple[float, float]]] = {
    "mountain": {
        "tier_high":   (2.5, 0.8),   # riders with climbing > 80
        "tier_mid":    (3.5, 0.9),   # riders with climbing 60-80
        "tier_low":    (4.5, 1.0),   # riders with climbing < 60
    },
    "tt": {
        "tier_high":   (1.5, 0.6),
        "tier_mid":    (2.5, 0.7),
        "tier_low":    (3.5, 0.8),
    },
}

# Rider tier thresholds for time gap generation (based on relevant rating)
TIER_HIGH_THRESHOLD: int = 80   # rating above this → tier_high
TIER_MID_THRESHOLD: int = 60    # rating above this → tier_mid (else tier_low)

SIMULATION_ITERATIONS: int = 20_000
