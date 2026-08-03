"""
Commutation-function implementation of the life-contingent products.

This is an *independent second implementation*, kept as a cross-check against
the summation-based LifeInsuranceCalculator in premium_calculator.py. Both are
priced from the same mortality table; the test suite asserts they agree to
floating-point precision.

Design note: the interest rate is fixed at construction, because it is baked
into the commutation columns (D, N, C, M). To compare interest rates, build a
separate CommutationCalculator per rate.
"""


class CommutationCalculator:
    """Prices life insurance and annuity products via commutation functions.

    Expected DataFrame columns: 'l' (number living) and 'qx' (mortality rate),
    indexed by integer 'age'.
    """

    def __init__(self, df, interest):
        df = df.copy()
        if df.index.name != 'age':
            df = df.set_index('age')
        # Terminal-age mortality must be 1 (everyone alive at the last age
        # dies within that year).
        df.loc[df.index.max(), 'qx'] = 1.0
        if not df['qx'].between(0, 1).all():
            raise ValueError("Column 'qx' contains values outside [0, 1].")
        self.df = df
        self._build_commutation(interest)

    def _build_commutation(self, interest):
        """Add the D, C, N, M commutation columns to self.df.

        D_x = v^x * l_x                 (discounted living)
        C_x = v^(x+1) * l_x * q_x       (discounted deaths, paid year-end)
        N_x = sum of D_k for k >= x      (running sum, bottom-up)
        M_x = sum of C_k for k >= x      (running sum, bottom-up)
        """
        v = 1 / (1 + interest)
        df = self.df
        df['D'] = v ** df.index * df['l']
        df['C'] = v ** (df.index + 1) * df['l'] * df['qx']
        df['N'] = df['D'][::-1].cumsum()[::-1]
        df['M'] = df['C'][::-1].cumsum()[::-1]

    # ---- Insurances ----------------------------------------------------
    def whole_life_insurance_comm(self, age, payment):
        """A_x = M_x / D_x"""
        return payment * self.df.at[age, 'M'] / self.df.at[age, 'D']

    def term_life_comm(self, age, term, payment):
        """A^1_x:n = (M_x - M_{x+n}) / D_x"""
        M_x = self.df.at[age, 'M']
        M_xn = self.df.at[age + term, 'M']
        D = self.df.at[age, 'D']
        return payment * (M_x - M_xn) / D

    def deferred_term_life_comm(self, age, term, deferral, payment):
        """m|A^1_x:n = (M_{x+m} - M_{x+m+n}) / D_x, with m = deferral."""
        M_1 = self.df.at[age + deferral, 'M']
        M_2 = self.df.at[age + deferral + term, 'M']
        D = self.df.at[age, 'D']
        return payment * (M_1 - M_2) / D

    def pure_endowment_life_comm(self, age, term, payment):
        """nE_x = D_{x+n} / D_x"""
        D_xn = self.df.at[age + term, 'D']
        D_x = self.df.at[age, 'D']
        return payment * D_xn / D_x

    def endowment_life_comm(self, age, term, payment):
        """Endowment = term insurance + pure endowment."""
        term_life = self.term_life_comm(age, term, payment)
        nEx = self.pure_endowment_life_comm(age, term, payment)
        return term_life + nEx

    # ---- Annuities -----------------------------------------------------
    def annuity_due_comm(self, age, payment):
        """a-due_x = N_x / D_x"""
        N = self.df.at[age, 'N']
        D = self.df.at[age, 'D']
        return payment * N / D

    def term_annuity_due_comm(self, age, term, payment):
        """a-due_x:n = (N_x - N_{x+n}) / D_x"""
        N_x = self.df.at[age, 'N']
        N_xn = self.df.at[age + term, 'N']
        D = self.df.at[age, 'D']
        return payment * (N_x - N_xn) / D

    def annuity_immediate_comm(self, age, payment):
        """a_x = N_{x+1} / D_x"""
        N = self.df.at[age + 1, 'N']
        D = self.df.at[age, 'D']
        return payment * N / D

    def term_annuity_immediate_comm(self, age, term, payment):
        """a_x:n = (N_{x+1} - N_{x+n+1}) / D_x"""
        N_1 = self.df.at[age + 1, 'N']
        N_2 = self.df.at[age + term + 1, 'N']
        D = self.df.at[age, 'D']
        return payment * (N_1 - N_2) / D
