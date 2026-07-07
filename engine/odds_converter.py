from math import gcd


def remove_overround_power(implied: dict) -> dict:
    """De-margin a book of implied probabilities using the power method.

    Finds k such that sum(p_i^k) = 1 and returns {key: p_i^k}.

    Proportional normalisation (p_i / total) spreads the bookmaker's margin
    evenly, which badly understates favourites on high-overround books —
    cycling outrights routinely run 150%+ because margin is concentrated in
    the longshots (favourite-longshot bias). The power method removes margin
    progressively: a 1.24 favourite keeps most of its implied probability
    while 200+ longshots are compressed hardest.

    Keys with p <= 0 map to 0.0. An overround book (total > 1) yields k > 1;
    an undercovered book (total < 1) yields k < 1, scaling probabilities up.
    """
    positive = {key: p for key, p in implied.items() if p > 0}
    if not positive:
        return {key: 0.0 for key in implied}
    if len(positive) == 1:
        # Single-outcome book: no finite k reaches sum=1; match proportional.
        (only_key,) = positive
        return {key: 1.0 if key == only_key else 0.0 for key in implied}

    probs = list(positive.values())
    # sum(p^k) is strictly decreasing in k; bracket the root then bisect.
    lo, hi = 1e-6, 1.0
    while sum(p**hi for p in probs) > 1.0:
        hi *= 2
        if hi > 1e6:
            break
    for _ in range(200):
        mid = (lo + hi) / 2
        if sum(p**mid for p in probs) > 1.0:
            lo = mid
        else:
            hi = mid
    k = (lo + hi) / 2

    result = {key: p**k for key, p in positive.items()}
    for key in implied:
        result.setdefault(key, 0.0)
    return result


def probability_to_decimal(p: float) -> float:
    if p <= 0:
        return 1000.0
    return round(1.0 / p, 2)


def decimal_to_fractional(decimal_odds: float) -> str:
    """Convert decimal odds to fractional string, e.g. 4.0 -> '3/1'."""
    profit = decimal_odds - 1.0
    denominator = 100
    numerator = round(profit * denominator)
    common = gcd(int(numerator), int(denominator))
    return f"{numerator // common}/{denominator // common}"
