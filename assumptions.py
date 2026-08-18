from dataclasses import dataclass

@dataclass(frozen=True)
class ExpenseAssumptions:
    c1: float = 0.50        #first year percentage of premium expense
    E1: float = 150.0       #first year flat expense
    cr: float = 0.05        #renewal year percentage of premium expense
    Er: float = 30.0        #renewal year flat expense
    theta: float = 0.12     #profit percentage 


