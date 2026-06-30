from math import gcd


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
