import pandas as pd
from assumptions import ExpenseAssumptions
from premium_calculator import LifeInsuranceCalculator, load_table

def project_cashflows(mortality_df, issue_age, term, death_benefits, premium, expenses):
    if mortality_df.index.name != 'age': 
        mortality_df = mortality_df.set_index('age')
    df = mortality_df.loc[issue_age: issue_age + term - 1].copy()
    df['t'] = df.index - issue_age
    df['tpx'] = df['l'] / df.at[issue_age, 'l']
    df['expected_premium'] = df['tpx'] * premium
    df['expected_death_benefit'] = df['tpx'] * df['qx'] * death_benefits 
    if expenses is None:
        df['expected_expense'] = 0.0
    else:
        df['expected_expense'] = premium * expenses.cr + expenses.Er
        df.loc[df['t'] == 0, 'expected_expense'] = premium * expenses.c1 + expenses.E1
        df['expected_expense'] *= df['tpx']
    df['net_outflow'] = df['expected_death_benefit'] + df['expected_expense'] - df['expected_premium'] 
    return df


mortality = load_table()
calc = LifeInsuranceCalculator(mortality)
P = calc.calculate_net_premium_term_life(30, 0.05, 10, 100_000)
df = project_cashflows(mortality, 30, 10, 100_000, P, None)


A = calc.calculate_term_life(30, 0.05, 10, 100_000)
a_due = calc.calculate_term_life_annuity_due(30, 0.05, 10, 1)
exp = ExpenseAssumptions()
G = calc.gross_premium(A, a_due, exp)


def present_value(df, discount, t=0):
    df = df.reset_index().set_index('t')
    df = df.loc[t:].copy()
    df['discounted_expected_premium'] = df['expected_premium'] * discount(df.index - t)
    df['discounted_expected_death_benefit'] = df['expected_death_benefit'] * discount(df.index + 1 - t)
    df['discounted_expected_expense'] = df['expected_expense'] * discount(df.index - t)
    sum_premium = df['discounted_expected_premium'].sum()
    sum_death_benefit = df['discounted_expected_death_benefit'].sum()
    sum_expense = df['discounted_expected_expense'].sum()

    return (sum_death_benefit + sum_expense - sum_premium ) / df.at[t, 'tpx']      #since the denominator is L base, diving tpx could help to adjust to L base + t.



