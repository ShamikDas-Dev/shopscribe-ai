import pytest

from core.pricing import calculate_discount_percent


def test_discount_calculation():
    assert calculate_discount_percent(500, 400) == 20.0


def test_no_discount_returns_zero():
    assert calculate_discount_percent(299, 299) == 0.0


def test_missing_price_returns_none():
    assert calculate_discount_percent(None, 199) is None


def test_selling_price_greater_than_mrp_is_rejected():
    with pytest.raises(ValueError):
        calculate_discount_percent(200, 250)
