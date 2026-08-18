import pandas as pd
import pathlib
import matplotlib.pyplot as plt
from assumptions import ExpenseAssumptions

class InputValidation:
    """Helper class to validate user inputs for the calculator."""

    def __init__(self, df):
        self.df = df
        self.max_age = self.df.index.max()
        self.min_age = self.df.index.min()

    def validate_input_age(self, age):
        if not (self.min_age <= age <= self.max_age):
            raise ValueError(f"Age {age} out of range ({self.min_age} - {self.max_age})")

    def validate_death_benefit_term(self, age, term):
        """For products paying only on death within the term (e.g. term life).
        Last possible death benefit comes from age (age + term - 1)."""
        if not (self.min_age <= age + term - 1 <= self.max_age):
            raise ValueError(f"age+term-1 = {age + term - 1} out of range ({self.min_age} - {self.max_age})")

    def validate_survival_benefit_term(self, age, term):
        """For products that pay on survival to maturity (endowment, pure
        endowment, term annuities). Needs the (age + term) row."""
        if not (self.min_age <= age + term <= self.max_age):
            raise ValueError(f"age+term = {age + term} out of range ({self.min_age} - {self.max_age})")

    def validate_input_age_term_deferral(self, age, term, deferral):
        """Deferred term life pays only on death; last benefit from
        age (age + deferral + term - 1)."""
        if not (self.min_age <= age + deferral + term - 1 <= self.max_age):
            raise ValueError(
                f"age+deferral+term-1 = {age + deferral + term - 1} out of range ({self.min_age} - {self.max_age})")

    def validate_payment(self, payment):
        if not (payment > 0):
            raise ValueError("Payment must be a positive number.")

    def validate_interest(self, interest):
        if not (interest > 0):
            raise ValueError("Interest must be a positive number.")


class LifeInsuranceCalculator:
    """Calculates the present value of several common life insurance and
    annuity products from a mortality table.

    Expected DataFrame columns: 'l' (number living) and 'qx' (mortality rate),
    indexed by integer 'age'.

    Parameter conventions:
        age:      positive integer
        interest: positive real number (annual effective rate)
        payment:  positive real number (level annual payment / benefit)
        term:     positive integer (number of years)
        deferral: non-negative integer (deferral period in years)
    """

    def __init__(self, df):
        df = df.copy()
        if df.index.name != 'age':
            df = df.set_index('age')
        # Terminal-age mortality must be 1 (everyone alive at the last age
        # dies within that year)
        df.loc[df.index.max(), 'qx'] = 1.0
        if not df['qx'].between(0, 1).all():
            raise ValueError("Column 'qx' contains values outside [0, 1].")
        self.df = df
        self.validator = InputValidation(df)
       


    def calculate_whole_life_insurance(self, age, interest, payment):
        """Present value of a whole life insurance (benefit paid at end of
        year of death)."""
        self.validator.validate_interest(interest)
        self.validator.validate_input_age(age)
        self.validator.validate_payment(payment)
        v = 1 / (1 + interest)

        
        df_slice = self.df.loc[age:].copy()
        lx = self.df.at[age, 'l']
        df_slice['tpx'] = df_slice['l'] / lx
        df_slice['pv'] = v ** (df_slice.index - age + 1) * df_slice['tpx'] * df_slice['qx']
        return df_slice['pv'].sum() * payment

    def calculate_term_life(self, age, interest, term, payment):
        """Present value of an n-year term life insurance (death benefit only)."""
        self.validator.validate_interest(interest)
        self.validator.validate_death_benefit_term(age, term)
        self.validator.validate_payment(payment)
        v = 1 / (1 + interest)

        df_slice = self.df.loc[age:age + term - 1].copy()
        lx = self.df.at[age, 'l']
        df_slice['tpx'] = df_slice['l'] / lx
        df_slice['pv'] = v ** (df_slice.index - age + 1) * df_slice['tpx'] * df_slice['qx']
        return df_slice['pv'].sum() * payment

    def calculate_deferred_term_life(self, age, interest, term, deferral, payment):
        """Present value of a deferred term life insurance (death benefit only)."""
        self.validator.validate_interest(interest)
        self.validator.validate_input_age_term_deferral(age, term, deferral)
        self.validator.validate_payment(payment)
        v = 1 / (1 + interest)

        df_slice = self.df.loc[age + deferral: age + deferral + term - 1].copy()
        lx = self.df.at[age + deferral, 'l']
        df_slice['tpx'] = df_slice['l'] / lx
        df_slice['pv'] = v ** (df_slice.index - age - deferral + 1) * df_slice['tpx'] * df_slice['qx']
        sum_value = df_slice['pv'].sum()
        lives_age = self.df.at[age, 'l']
        
        sum_value = sum_value * v ** deferral * lx / lives_age
        return sum_value * payment

    def calculate_endowment_life(self, age, interest, term, payment):
        """Present value of an n-year endowment = term life + pure endowment."""
        self.validator.validate_interest(interest)
        self.validator.validate_survival_benefit_term(age, term)
        self.validator.validate_payment(payment)
        v = 1 / (1 + interest)

        df_slice = self.df.loc[age:age + term - 1].copy()
        lx = self.df.at[age, 'l']
        df_slice['tpx'] = df_slice['l'] / lx
        df_slice['pv'] = v ** (df_slice.index - age + 1) * df_slice['tpx'] * df_slice['qx']
        sum_value = df_slice['pv'].sum()
       
        tpx_last = self.df.at[age + term, 'l'] / lx
        sum_value = tpx_last * v ** term + sum_value
        return sum_value * payment

    def calculate_pure_endowment(self, age, interest, term, payment):
        """Present value of a pure endowment (pays only on survival to maturity)."""
        self.validator.validate_interest(interest)
        self.validator.validate_survival_benefit_term(age, term)
        self.validator.validate_payment(payment)
        v = 1 / (1 + interest)

        lx = self.df.at[age, 'l']
        present_value = v ** term * self.df.at[age + term, 'l'] / lx
        return present_value * payment

    def calculate_whole_life_annuity_immediate(self, age, interest, payment):
        """Present value of a whole life annuity-immediate (payments at year end)."""
        self.validator.validate_interest(interest)
        self.validator.validate_input_age(age)
        self.validator.validate_payment(payment)
        v = 1 / (1 + interest)

        
        df_slice = self.df.loc[age + 1:].copy()
        lx = self.df.at[age, 'l']
        df_slice['tpx'] = df_slice['l'] / lx
        df_slice['pv'] = v ** (df_slice.index - age) * df_slice['tpx']
        return df_slice['pv'].sum() * payment

    def calculate_whole_life_annuity_due(self, age, interest, payment):
        """Present value of a whole life annuity-due = annuity-immediate + payment at time 0."""
        annuity_immediate = self.calculate_whole_life_annuity_immediate(age, interest, payment)
        return payment + annuity_immediate

    def calculate_term_life_annuity_immediate(self, age, interest, term, payment):
        """Present value of an n-year term annuity-immediate (payments at year end)."""
        self.validator.validate_interest(interest)
        self.validator.validate_survival_benefit_term(age, term)
        self.validator.validate_payment(payment)
        v = 1 / (1 + interest)

        df_slice = self.df.loc[age + 1: age + term].copy()
        lx = self.df.at[age, 'l']
        df_slice['tpx'] = df_slice['l'] / lx
        df_slice['pv'] = v ** (df_slice.index - age) * df_slice['tpx']
        return df_slice['pv'].sum() * payment

    def calculate_term_life_annuity_due(self, age, interest, term, payment):
        """Present value of an n-year term annuity-due. Add the time-0 payment
        and remove the final payment at time `term`."""
        self.validator.validate_interest(interest)
        self.validator.validate_survival_benefit_term(age, term)
        self.validator.validate_payment(payment)
        v = 1 / (1 + interest)

        annuity_immediate = self.calculate_term_life_annuity_immediate(age, interest, term, payment)
        time_n_term = payment * (self.df.at[age + term, 'l'] / self.df.at[age, 'l']) * v ** term
        return payment + annuity_immediate - time_n_term
    

    def calculate_net_premium_whole_life(self, age, interest, payment):
        A = self.calculate_whole_life_insurance(age, interest, 1)
        a_due = self.calculate_whole_life_annuity_due(age, interest, 1)
        return payment * A / a_due
    
    
    def calculate_reserve_whole_life(self, age, interest, payment, t):
        A = self.calculate_whole_life_insurance(age, interest, 1)
        a_due = self.calculate_whole_life_annuity_due(age, interest, 1)
        P = payment * A / a_due
        return self.calculate_whole_life_insurance(age + t, interest, payment) - P * self.calculate_whole_life_annuity_due(age + t, interest, 1)
    
    def project_term_life(self, age, term, interest, payment):
        df = self.df.loc[age: age + term - 1].copy()
        lx = self.df.at[age, 'l']
        df['tpx'] = df['l'] / lx
        df['expected_death'] = payment * df['tpx'] * df['qx']
        P = payment * self.calculate_net_premium_term_life(age, interest, term, 1)
        df['expected_premium'] = P * df['tpx']
        df['net_cash_flow'] = df['expected_premium'] - df['expected_death']
        df['reserve'] = [self.reserve_term_life(age, interest, term, payment, t) for t in range(term)]

        return df[['l', 'qx', 'tpx', 'expected_death', 'expected_premium', 'net_cash_flow', 'reserve']]
    
    def calculate_net_premium_term_life(self, age, interest, term, payment):
        A = self.calculate_term_life(age, interest, term, 1)
        a_due = self.calculate_term_life_annuity_due(age, interest, term, 1)
        return payment * A / a_due

    def reserve_term_life(self, age, interest, term, payment, t):
    
        A = payment * self.calculate_term_life(age + t, interest, term - t, 1)
        P = payment * self.calculate_net_premium_term_life(age, interest, term, 1)
        a_due = self.calculate_term_life_annuity_due(age + t, interest, term - t, 1)
        return A - P * a_due
    
    def profit_test_term_life(self, age, term, interest, payment, earned_rate):
        df = self.project_term_life(age, term, interest, payment)
        P = payment * self.calculate_net_premium_term_life(age, interest, term, 1)
        df['profit'] = (df['reserve'] + P) * (1 + earned_rate) - (df['qx']) * (payment) - (1 - df['qx']) * (df['reserve'].shift(-1).fillna(0))
        return df

    def reserve_term_life_two_rates(self, age, pricing_rate, valuation_rate, term, payment, t):
        P = self.calculate_net_premium_term_life(age, pricing_rate, term, payment)
        A = self.calculate_term_life(age + t, valuation_rate, term - t, payment)
        a_due = self.calculate_term_life_annuity_due(age + t, valuation_rate, term - t, 1)
        return A - P * a_due
    
    def gross_premium(self, A, annuity_due, exp: ExpenseAssumptions) -> float:
        c1, E1, cr, Er, theta = exp.c1, exp.E1, exp.cr, exp.Er, exp.theta

        numerator = A + E1 + Er * (annuity_due - 1)
        denominator = annuity_due - c1 - cr * (annuity_due - 1) - theta * annuity_due
        return numerator / denominator 




def load_table(csv_path=None):
    if csv_path is None:
        csv_path = pathlib.Path(__file__).resolve().parent / 'Mortality_Table.csv'
    df = pd.read_csv(csv_path)
    df = df.rename(columns={'x': 'age', 'q': 'qx'})
    return df[['age', 'l', 'qx']]


def main():
    base_dir = pathlib.Path(__file__).resolve().parent
    df = load_table(base_dir / 'Mortality_Table.csv')
    calc = LifeInsuranceCalculator(df)

   #age, interest, payment, term, deferral = 30, 0.05, 1, 10, 5

if __name__ == "__main__":
    main()
