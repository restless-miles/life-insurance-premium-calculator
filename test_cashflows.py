"""
Test suite for cashflows

Check:

Two kinds of checks:
  1. Net premium basis — present_value() must agree with reserve_term_life()
     at every duration.
  2. Gross premium basis — with expenses loaded, PV at inception must equal
     the profit margin -theta * G * a_due.

"""

import pytest
from premium_calculator import LifeInsuranceCalculator, load_table
from cashflows import project_cashflows, present_value
from assumptions import ExpenseAssumptions
from discounting import flat, curve

AGE, TERM, PAY, INTEREST = 30, 10, 100_000, 0.05

@pytest.fixture
def calc():
    return LifeInsuranceCalculator(load_table())

@pytest.fixture
def cf(calc):
    P = calc.calculate_net_premium_term_life(AGE, INTEREST, TERM, PAY)
    return project_cashflows(load_table(), AGE, TERM, PAY, P, None)

@pytest.fixture
def a_due(calc):
    return calc.calculate_term_life_annuity_due(AGE, INTEREST, TERM, 1)

@pytest.fixture
def gross(calc, a_due):
    A = calc.calculate_term_life(AGE, INTEREST, TERM, PAY)
    return calc.gross_premium(A, a_due, ExpenseAssumptions())

@pytest.fixture
def cf_gross(gross):
    return project_cashflows(load_table(), AGE, TERM, PAY, gross, ExpenseAssumptions())

@pytest.mark.parametrize("t", range(TERM))
def test_pv_matches_reserve(calc, cf, t):
    assert present_value(cf, flat(INTEREST), t) == pytest.approx(calc.reserve_term_life(AGE, INTEREST, TERM, PAY, t), abs=1e-9)

def test_gross_premium_pv_equals_profit_margin(cf_gross, gross, a_due):
    expected = -ExpenseAssumptions().theta * a_due * gross
    assert present_value(cf_gross, flat(INTEREST), 0) == pytest.approx(expected, abs=1e-9)

def test_curve_uses_per_year_rate():
    d = curve([0.05, 0.04, 0.03])
    assert d(0) == pytest.approx(1.0)
    assert d(1) == pytest.approx(1 / 1.04)
    assert d(2) == pytest.approx(1 / 1.03**2)

@pytest.mark.parametrize("t", range(TERM))
def test_flat_curve_equal_flat(cf, t):
    by_flat = present_value(cf, flat(INTEREST),t)
    by_curve = present_value(cf, curve([INTEREST] * (TERM + 1)), t)
    assert by_curve == pytest.approx(by_flat, abs=1e-9)

