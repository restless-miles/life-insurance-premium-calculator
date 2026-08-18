import numpy as np

"""Discount factor construction.

Each function is a factory: it takes a rate basis and returns

    discount(years) -> factor

`years` may be a scalar or an array. Hiding the rate basis behind one
interface is what lets the same cashflows be valued on two curves at once —
the current curve for fulfilment cashflows, the locked-in curve for CSM
interest accretion.
"""

def flat(rate):
    """Single flat annual effective rate. A simplification; IFRS 17 requires
    a term structure."""
    def discount(years):
        return (1 + rate) ** -years
    return discount


def curve(spots):
    """Discount function for a term structure of annual effective spot rates.

    `spots[k]` is the k-year spot rate, i.e. the rate used to discount a
    single cashflow falling k years after the valuation date. Note this means
    `spots` is the curve observed at the valuation date, not the curve at
    issue projected forward.

    Limitations:
      - `spots` must cover the longest discount period. For an n-year contract
        valued at inception, the last death benefit falls at time n, so
        `spots` needs n + 1 entries.
      - Integer years only. Non-integer terms (e.g. mid-year claims) would
        need interpolation, which is not implemented.
    """
    spots  = np.asanyarray(spots)

    def discount(years):
        return (1 + spots[years]) ** -years
    return discount