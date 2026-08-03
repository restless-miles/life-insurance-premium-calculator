"""
Test suite for premium_calculator.

Two kinds of checks:
  1. Cross-validation — the commutation-function implementation
     (CommutationCalculator) must agree with the summation-based public API
     (LifeInsuranceCalculator).
  2. Actuarial identities — relationships that must hold regardless of method.

Run from the project folder (where Mortality_Table.csv lives):
    pip install pytest
    pytest -v
"""

import pytest
from premium_calculator import LifeInsuranceCalculator, load_table
from commutation import CommutationCalculator

INTEREST = 0.05
AGE, TERM, DEFERRAL, PAY = 30, 10, 5, 100_000


@pytest.fixture
def summ():
    """Summation-based calculator — the primary public API."""
    df = load_table("Mortality_Table.csv")
    return LifeInsuranceCalculator(df)


@pytest.fixture
def comm():
    """Commutation-function calculator — the independent cross-check."""
    df = load_table("Mortality_Table.csv")
    return CommutationCalculator(df, INTEREST)


# ---------------------------------------------------------------------------
# 1. Commutation vs summation — each pair must match to floating-point precision
# ---------------------------------------------------------------------------
# Each row is (commutation call, summation call). Signatures differ: the
# commutation methods dropped `interest` (baked into the columns at construction).
@pytest.mark.parametrize("comm_fn, summ_fn", [
    (lambda c: c.whole_life_insurance_comm(AGE, PAY),
     lambda s: s.calculate_whole_life_insurance(AGE, INTEREST, PAY)),

    (lambda c: c.term_life_comm(AGE, TERM, PAY),
     lambda s: s.calculate_term_life(AGE, INTEREST, TERM, PAY)),

    (lambda c: c.deferred_term_life_comm(AGE, TERM, DEFERRAL, PAY),
     lambda s: s.calculate_deferred_term_life(AGE, INTEREST, TERM, DEFERRAL, PAY)),

    (lambda c: c.endowment_life_comm(AGE, TERM, PAY),
     lambda s: s.calculate_endowment_life(AGE, INTEREST, TERM, PAY)),

    (lambda c: c.pure_endowment_life_comm(AGE, TERM, PAY),
     lambda s: s.calculate_pure_endowment(AGE, INTEREST, TERM, PAY)),

    (lambda c: c.annuity_due_comm(AGE, PAY),
     lambda s: s.calculate_whole_life_annuity_due(AGE, INTEREST, PAY)),

    (lambda c: c.term_annuity_due_comm(AGE, TERM, PAY),
     lambda s: s.calculate_term_life_annuity_due(AGE, INTEREST, TERM, PAY)),

    (lambda c: c.annuity_immediate_comm(AGE, PAY),
     lambda s: s.calculate_whole_life_annuity_immediate(AGE, INTEREST, PAY)),

    (lambda c: c.term_annuity_immediate_comm(AGE, TERM, PAY),
     lambda s: s.calculate_term_life_annuity_immediate(AGE, INTEREST, TERM, PAY)),
])
def test_commutation_matches_summation(comm, summ, comm_fn, summ_fn):
    assert comm_fn(comm) == pytest.approx(summ_fn(summ))


# ---------------------------------------------------------------------------
# 2. Actuarial identities (hold only to table rounding, hence abs=1e-4)
# ---------------------------------------------------------------------------
def test_identity_whole_life(comm):
    """A_x + d * a-due_x = 1"""
    A = comm.whole_life_insurance_comm(AGE, 1)
    a_due = comm.annuity_due_comm(AGE, 1)
    d = INTEREST / (1 + INTEREST)
    assert A + d * a_due == pytest.approx(1.0, abs=1e-4)


def test_identity_endowment(comm):
    """A_x:n + d * a-due_x:n = 1"""
    A = comm.endowment_life_comm(AGE, TERM, 1)
    a_due = comm.term_annuity_due_comm(AGE, TERM, 1)
    d = INTEREST / (1 + INTEREST)
    assert A + d * a_due == pytest.approx(1.0, abs=1e-4)


def test_endowment_equals_term_plus_pure(comm):
    """Endowment = term insurance + pure endowment"""
    endow = comm.endowment_life_comm(AGE, TERM, PAY)
    parts = (comm.term_life_comm(AGE, TERM, PAY)
             + comm.pure_endowment_life_comm(AGE, TERM, PAY))
    assert endow == pytest.approx(parts)
