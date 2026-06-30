import pytest
from engine.odds_converter import probability_to_decimal, decimal_to_fractional

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
