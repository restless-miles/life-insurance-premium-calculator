import numpy as np
import pandas as pd

def simulate_one_policy(calc, age, interest, term, payment):
    v = 1 / (1 + interest)
    for t in range(term):
        q = calc.df.at[age + t, 'qx'] 
        u = np.random.random()
        if u < q:
            return payment * v ** (t + 1) 
    return 0

def simulate_portfolio(calc, age, interest, term, payment, n_sims):
    return np.array([simulate_one_policy(calc, age, interest, term, payment) for _ in range(n_sims)])
        