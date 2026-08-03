# Actuarial Premium Calculator

A Python model that prices and values life-contingent products from a mortality
table. Inspired by the SOA Exam FAM syllabus, it covers the full path from
pricing a policy through to projecting its cash flows, reserves and profit.

## Features

**Actuarial present values** — nine life-contingent products:

| Insurances | Annuities |
|---|---|
| Whole life | Whole life annuity-due |
| Term | Whole life annuity-immediate |
| Deferred term | Term annuity-due |
| Endowment | Term annuity-immediate |
| Pure endowment | |

**Pricing and valuation**

- Net premiums by the equivalence principle
- Policy values (reserves), prospective basis
- Annual cash flow projection — premium income, death cost, net cash flow, reserve
- Profit testing with a separate earned rate, producing a profit signature
- Interest rate sensitivity, including separate pricing and valuation rates
  (negative spread on in-force business)

## Repository

| File | Purpose |
|---|---|
| `premium_calculator.py` | Core model — the `LifeInsuranceCalculator` class |
| `commutation.py` | Independent second implementation via commutation functions |
| `sensitivity.py` | Sensitivity analysis helpers |
| `analysis.ipynb` | Walkthrough of a single policy, from pricing to valuation |
| `test_premium_calculator.py` | Internal consistency tests (12) |
| `test_validate_actuarialmath.py` | Third-party validation tests (9) |
| `Mortality_Table.csv` | SOA Standard Ultimate Life Table |

## Mortality table

The default table is the **Standard Ultimate Life Table** from the SOA Tables
for Exam FAM-L, at i = 0.05, covering ages 20–100. The table is truncated at
age 100, where `qx` is set to 1 (all remaining lives are assumed to die within
that year).

## Usage

```python
from premium_calculator import LifeInsuranceCalculator, load_table

df = load_table()                       # defaults to Mortality_Table.csv
calc = LifeInsuranceCalculator(df)

# EPV of a 10-year term insurance: age 30, i = 5%, benefit 100,000
calc.calculate_term_life(30, 0.05, 10, 100_000)          # 295.16

# Annual net premium for the same policy
calc.calculate_net_premium_term_life(30, 0.05, 10, 100_000)   # 36.46

# Year-by-year cash flow projection with reserves
calc.project_term_life(30, 10, 0.05, 100_000)

# Profit signature when the earned rate exceeds the pricing rate
calc.profit_test_term_life(30, 10, 0.05, 100_000, earned_rate=0.06)
```

See `analysis.ipynb` for the full walkthrough with charts and commentary.

## Validation

Correctness is established at two independent levels.

**Internal consistency.** Every product is implemented twice — once by summing
survival-weighted discounted cash flows, and once via precomputed commutation
functions (D, N, C, M). The two agree to floating-point precision (~1e-16).
Standard actuarial identities are also asserted:

- `A_x + d · ä_x = 1`
- `A_x:n + d · ä_x:n = 1`
- `Endowment = term insurance + pure endowment`

**Third-party validation.** Results are benchmarked against the
[`actuarialmath`](https://pypi.org/project/actuarialmath/) library across
several ages. Short-duration products agree to ~1e-6; whole-life products
differ by ~1e-4, traced to terminal-age truncation in this table versus the
library's Makeham extrapolation — an explained difference rather than a defect.

The two layers catch different failure modes: cross-implementation testing
finds coding errors, while benchmarking against an external library would
expose a conceptual error shared by both implementations. The suite of 21 tests
also surfaced a latent scaling bug in the original annuity-due code that was
invisible at unit benefit.

```bash
pip install -r requirements.txt
pytest -v
```

## Design notes

**Commutation functions.** Every present value repeats the same discounting and
survival weighting. The commutation columns precompute this once at
construction, turning an O(n) summation per call into an O(1) lookup — for
example `A_x = M_x / D_x`. These are no longer taught in the modern FAM
syllabus, which uses spreadsheet-style summation, but they remain a clean
illustration of trading precomputation for query speed. Here they serve as the
independent cross-check on the primary implementation.

**Interest rate handling.** The summation-based calculator takes the interest
rate per call; the commutation calculator fixes it at construction, since the
rate is baked into the columns. Comparing rates therefore means building one
calculator per rate — the rate is part of the valuation basis, not a per-query
parameter.

## Limitations

Net premium framework only — no expenses, lapses or mortality improvement. All
calculations are deterministic; the model quantifies expected values and their
sensitivity to assumptions, but not the distribution of outcomes. Natural
extensions would be gross premium pricing, a multiple-decrement model, and
stochastic simulation of mortality and interest.
