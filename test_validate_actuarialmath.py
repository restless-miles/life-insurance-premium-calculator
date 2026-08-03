"""
Third-party validation against the `actuarialmath` library (Terence Lim).

Both price from the Standard Ultimate Life Table (SULT) at i = 0.05.

Tolerance is two-tier, and this is the important design point:

  * Short-duration products (e.g. a 10-year term at 30) never involve mortality
    near the end of the table, so my rounded CSV table and actuarialmath's
    Makeham-based SULT agree to table-rounding precision (~1e-6).

  * Whole-life products DO depend on survival to very old ages, where my table
    truncates at age 100 (q_100 = 1) while actuarialmath extrapolates via
    Makeham. That modelling difference shows up as ~1e-4 in A_x, and propagates
    to the annuity as ~1e-3 through the identity  A_x + d * a-due_x = 1
    (so  delta a-due = delta A / d). Hence the looser tolerance below — it is
    an explained, expected difference, not a defect.

Run from the project folder, inside the venv:
    pip install actuarialmath ipython
    pytest -v test_validate_actuarialmath.py
"""

import pytest
from actuarialmath import SULT
from premium_calculator import LifeInsuranceCalculator, load_table

INTEREST = 0.05
AGE, TERM = [30, 50, 70], 10


@pytest.fixture
def calc():
    df = load_table("Mortality_Table.csv")
    return LifeInsuranceCalculator(df)


@pytest.fixture
def life():
    return SULT()   # built-in SULT, i = 0.05


# ---------------------------------------------------------------------------
# Short-duration: tight tolerance (does not touch the terminal age)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("age", AGE)
def test_term_insurance(calc, life, age):
    lib = life.term_insurance(x=age, t=TERM)
    mine = calc.calculate_term_life(age, INTEREST, TERM, 1)
    assert mine == pytest.approx(lib, abs=1e-4)

@pytest.mark.parametrize("age", AGE)
def test_whole_life(calc, life, age):
    lib = life.whole_life_insurance(x=age)
    mine = calc.calculate_whole_life_insurance(age, INTEREST, 1)
    assert mine == pytest.approx(lib, rel=5e-3)

@pytest.mark.parametrize("age", AGE)
def test_whole_life_annuity(calc, life, age):
    lib = life.whole_life_annuity(x=age)
    mine = calc.calculate_whole_life_annuity_due(age, INTEREST, 1)
    assert mine == pytest.approx(lib, rel=5e-3)
# def test_whole_life_insurance(calc, life):
#     lib  = life.whole_life_insurance(x=AGE)
#     mine = calc.calculate_whole_life_insurance(AGE, INTEREST, 1)
#     assert mine == pytest.approx(lib, rel=???)
#
# def test_whole_life_annuity(calc, life):
#     lib  = life.whole_life_annuity(x=AGE)
#     mine = calc.calculate_whole_life_annuity_due(AGE, INTEREST, 1)
#     assert mine == pytest.approx(lib, rel=???)
