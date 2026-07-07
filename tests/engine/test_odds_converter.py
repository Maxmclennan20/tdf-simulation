import pytest
from engine.odds_converter import probability_to_decimal, decimal_to_fractional, remove_overround_power

def test_even_money():
    assert probability_to_decimal(0.5) == pytest.approx(2.0)

def test_high_probability():
    assert probability_to_decimal(0.9) == pytest.approx(1.111, rel=1e-3)

def test_zero_probability_returns_large_odds():
    assert probability_to_decimal(0.0) == pytest.approx(1000.0)

def test_fractional_evens():
    assert decimal_to_fractional(2.0) == "1/1"

def test_fractional_half():
    assert decimal_to_fractional(1.5) == "1/2"

def test_fractional_common():
    assert decimal_to_fractional(4.0) == "3/1"


def test_power_demargin_sums_to_one():
    implied = {1: 1/1.24, 2: 1/4.0, 3: 1/11.5, 4: 1/151.0, 5: 1/226.0}
    p = remove_overround_power(implied)
    assert sum(p.values()) == pytest.approx(1.0, abs=1e-9)


def test_power_demargin_favours_favourite_over_proportional():
    # On an overround book the favourite must keep more probability than
    # proportional normalisation would give it, longshots less.
    implied = {1: 0.8, 2: 0.25, 3: 0.25, 4: 0.25}
    total = sum(implied.values())
    p = remove_overround_power(implied)
    assert p[1] > implied[1] / total
    assert p[2] < implied[2] / total


def test_power_demargin_fair_book_unchanged():
    implied = {1: 0.5, 2: 0.3, 3: 0.2}
    p = remove_overround_power(implied)
    for rid in implied:
        assert p[rid] == pytest.approx(implied[rid], rel=1e-6)


def test_power_demargin_undercovered_book_scales_up():
    implied = {1: 0.4, 2: 0.2}
    p = remove_overround_power(implied)
    assert sum(p.values()) == pytest.approx(1.0, abs=1e-9)
    assert p[1] > 0.4


def test_power_demargin_preserves_order():
    implied = {1: 0.7, 2: 0.4, 3: 0.2, 4: 0.05}
    p = remove_overround_power(implied)
    assert p[1] > p[2] > p[3] > p[4]


def test_power_demargin_zero_and_empty():
    assert remove_overround_power({}) == {}
    p = remove_overround_power({1: 0.6, 2: 0.0})
    assert p[2] == 0.0
    assert p[1] == pytest.approx(1.0, abs=1e-9)
