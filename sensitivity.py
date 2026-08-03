import pandas as pd

def sensitivity_interest_term(calc, age, term, payment, rates):
    rows = []
    for i in rates:
        rows.append({
               'interest': i,
               'net_premium': calc.calculate_net_premium_term_life(age, i, term, payment),
               'reserve_at_t5': calc.reserve_term_life(age, i, term, payment, 5)
        })
    df = pd.DataFrame(rows)
    return df

def sensitivity_interest_whole_life(calc, age, payment, rates):
    rows = []
    for i in rates:
        rows.append({
            'interest': i,
            'A_x': calc.calculate_whole_life_insurance(age, i, payment),
            'a_due': calc.calculate_whole_life_annuity_due(age, i, payment)
        })
    df = pd.DataFrame(rows)
    Base_A = df.loc[df['interest']==0.05, 'A_x'].iloc[0]
    df['A_x_pct'] = (df['A_x'] - Base_A) / Base_A * 100
    Base_a_due = df.loc[df['interest']==0.05, 'a_due'].iloc[0]
    df['a_due_pct'] = (df['a_due'] - Base_a_due) / Base_a_due * 100
    return df

