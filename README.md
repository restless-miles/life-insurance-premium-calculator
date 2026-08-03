# Actuarial Premium Calculator

## 1. Overview

Inspired by the SOA Exam FAM syllabus, this project translates the fundamentals
of life-contingent products into code. It calculates the present value of
several common life insurance and annuity products from a mortality table.

The project applies:
- Pandas DataFrames for vectorized actuarial calculations
- A SQLite database for loading and storing the mortality table
- CSV file imports
- Object-oriented programming, with a dedicated input-validation class

## 2. Products Supported

1. Whole life insurance
2. Term life insurance
3. Deferred term life insurance
4. Endowment insurance
5. Pure endowment
6. Whole life annuity (immediate and due)
7. Term life annuity (immediate and due)

## 3. Mortality Table

The default table is the **Standard Ultimate Life Table** (Basic Functions and
Single Net Premiums at i = 0.05) from the Society of Actuaries (SOA) Tables
for Exam FAM-L. The age range is 20 to 100. For simplicity, all lives beyond
age 100 are assumed to be 0, so the mortality rate at the terminal age is set
to 1 when the table is loaded.

## 4. Usage

```python
from premium_calculator import LifeInsuranceCalculator, load_table

df = load_table("Mortality_Table.csv")
calc = LifeInsuranceCalculator(df)

# Present value of a 10-year term life insurance, age 30, i = 5%, benefit = 1
print(calc.calculate_term_life(30, 0.05, 10, 1))
```

Or run the bundled example directly:

```bash
python premium_calculator.py
```

## 5. Validation

The implementation is verified using standard actuarial identities, which hold
to within rounding error of the table:

- `A_x + d * ä_x = 1`
- `A_x:n + d * ä_x:n = 1` (endowment and term annuity-due)
- `Endowment = Term insurance + Pure endowment`

These checks were also used during development to catch two bugs: an
off-by-one error in the annuity timing (payment time vs. survival probability
were misaligned by one year), and an invalid terminal mortality rate in the
source data.

## 6. Assumptions

- All payments are annual and level.
- Annuity-immediate: payments at the **end** of each year.
- Annuity-due: payments at the **beginning** of each year.
