from __future__ import annotations
from collections import defaultdict
from engine.models import RiderState, Stage, IterationResult, RiderOdds, AggregatedResults
from engine.odds_converter import probability_to_decimal, decimal_to_fractional


def aggregate_results(
    riders: dict[int, RiderState],
    stages: dict[int, Stage],
    iterations: list[IterationResult],
) -> AggregatedResults:
    n = len(iterations)
    active = {rid: rs for rid, rs in riders.items() if rs.is_active()}

    # --- GC win and podium counts ---
    gc_wins: dict[int, int] = defaultdict(int)
    gc_podium: dict[int, int] = defaultdict(int)
    for it in iterations:
        ranked = sorted(it.gc_times.items(), key=lambda x: x[1])
        if ranked:
            gc_wins[ranked[0][0]] += 1
        for rid, _ in ranked[:3]:
            gc_podium[rid] += 1

    # --- Stage win counts ---
    stage_wins: dict[int, dict[int, int]] = {s: defaultdict(int) for s in stages}
    for it in iterations:
        for sr in it.stage_results:
            stage_wins[sr.stage][sr.winner_id] += 1

    # --- Points jersey ---
    points_wins: dict[int, int] = defaultdict(int)
    for it in iterations:
        if it.points_scores:
            winner = max(it.points_scores, key=lambda k: it.points_scores[k])
            points_wins[winner] += 1

    # --- KOM ---
    kom_wins: dict[int, int] = defaultdict(int)
    for it in iterations:
        if it.kom_scores:
            winner = max(it.kom_scores, key=lambda k: it.kom_scores[k])
            kom_wins[winner] += 1

    def to_odds(counts: dict[int, int]) -> list[RiderOdds]:
        results = []
        for rid, rs in active.items():
            win_count = counts.get(rid, 0)
            p = win_count / n if n > 0 else 0.0
            dec = probability_to_decimal(p)
            results.append(RiderOdds(
                rider_id=rid,
                name=rs.rider.name,
                team=rs.rider.team,
                win_pct=round(p, 4),
                podium_pct=None,
                decimal_odds=dec,
                fractional_odds=decimal_to_fractional(dec),
            ))
        return sorted(results, key=lambda x: -x.win_pct)

    gc_odds = to_odds(gc_wins)

    # GC podium odds (with both win_pct and podium_pct)
    gc_podium_odds = []
    for r in gc_odds:
        pod_count = gc_podium.get(r.rider_id, 0)
        pod_pct = round(pod_count / n, 4) if n > 0 else 0.0
        gc_podium_odds.append(RiderOdds(
            rider_id=r.rider_id, name=r.name, team=r.team,
            win_pct=r.win_pct, podium_pct=pod_pct,
            decimal_odds=r.decimal_odds, fractional_odds=r.fractional_odds,
        ))

    stages_odds = {s: to_odds(stage_wins[s]) for s in stages}

    # Aggregated stage wins across all stages
    all_stage_wins: dict[int, int] = defaultdict(int)
    for s_counts in stage_wins.values():
        for rid, cnt in s_counts.items():
            all_stage_wins[rid] += cnt

    # Normalise: total draws = n * num_stages
    stages_all_total = n * len(stages)
    stages_all_odds = []
    for rid, rs in active.items():
        p = all_stage_wins.get(rid, 0) / stages_all_total if stages_all_total > 0 else 0.0
        dec = probability_to_decimal(p)
        stages_all_odds.append(RiderOdds(
            rider_id=rid, name=rs.rider.name, team=rs.rider.team,
            win_pct=round(p, 4), podium_pct=None,
            decimal_odds=dec, fractional_odds=decimal_to_fractional(dec),
        ))
    stages_all_odds.sort(key=lambda x: -x.win_pct)

    # Young rider jersey: per iteration, find eligible rider with lowest GC time
    eligible_ids = {rid for rid, rs in active.items() if rs.rider.young_rider_eligible}
    young_jersey_wins: dict[int, int] = defaultdict(int)
    for it in iterations:
        eligible_times = {rid: t for rid, t in it.gc_times.items() if rid in eligible_ids}
        if eligible_times:
            young_winner = min(eligible_times, key=lambda k: eligible_times[k])
            young_jersey_wins[young_winner] += 1

    young_total = sum(young_jersey_wins.values())
    young_odds = []
    for rid in eligible_ids:
        cnt = young_jersey_wins.get(rid, 0)
        p = cnt / young_total if young_total > 0 else 0.0
        dec = probability_to_decimal(p)
        rs = active[rid]
        young_odds.append(RiderOdds(
            rider_id=rid, name=rs.rider.name, team=rs.rider.team,
            win_pct=round(p, 4), podium_pct=None,
            decimal_odds=dec, fractional_odds=decimal_to_fractional(dec),
        ))
    young_odds.sort(key=lambda x: -x.win_pct)

    # Head-to-head (GC win probability)
    h2h: dict[tuple[int, int], tuple[float, float]] = {}
    rider_ids = list(active.keys())
    for i, r1 in enumerate(rider_ids):
        for r2 in rider_ids[i+1:]:
            p1 = gc_wins.get(r1, 0) / n if n > 0 else 0.5
            p2 = gc_wins.get(r2, 0) / n if n > 0 else 0.5
            total = p1 + p2
            if total > 0:
                h2h[(r1, r2)] = (round(p1 / total, 4), round(p2 / total, 4))
            else:
                h2h[(r1, r2)] = (0.5, 0.5)

    return AggregatedResults(
        gc=gc_odds,
        gc_podium=gc_podium_odds,
        stages=stages_odds,
        stages_all=stages_all_odds,
        points_jersey=to_odds(points_wins),
        kom=to_odds(kom_wins),
        young_rider=young_odds,
        head_to_head=h2h,
    )
