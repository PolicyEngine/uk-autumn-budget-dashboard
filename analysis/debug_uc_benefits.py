"""
Debug UC benefits - Check what's happening with the two-child limit
"""
import sys
sys.path.insert(0, '/Users/janansadeqian/policyengine-uk')

from policyengine_uk import Simulation

# Reform dict
reform_dict = {
    "gov.dwp.universal_credit.elements.child.limit.child_count": {
        "2025-01-01.2100-12-31": 100
    }
}

# Family with 3 children
situation = {
    "people": {
        "you": {
            "age": {"2026": 40},
            "employment_income": {"2026": 0}
        },
        "your partner": {
            "age": {"2026": 40},
            "employment_income": {"2026": 0}
        },
        "child1": {
            "age": {"2026": 7},
        },
        "child2": {
            "age": {"2026": 5},
        },
        "child3": {
            "age": {"2026": 3},
        }
    },
    "benunits": {
        "family": {
            "members": ["you", "your partner", "child1", "child2", "child3"],
            "would_claim_uc": {"2026": True}
        }
    },
    "households": {
        "household": {
            "members": ["you", "your partner", "child1", "child2", "child3"],
            "region": {"2026": "LONDON"}
        }
    }
}

print("="*70)
print("Debugging UC Benefits")
print("="*70)

# Baseline
baseline = Simulation(situation=situation)
print("\nBASELINE:")
print(f"  Universal Credit:         £{baseline.calculate('universal_credit', 2026)[0]:,.2f}")
print(f"  Child Tax Credit:         £{baseline.calculate('child_tax_credit', 2026)[0]:,.2f}")
print(f"  Child Benefit:            £{baseline.calculate('child_benefit', 2026)[0]:,.2f}")
print(f"  Income Support:           £{baseline.calculate('income_support', 2026)[0]:,.2f}")
print(f"  Household Net Income:     £{baseline.calculate('household_net_income', 2026)[0]:,.2f}")

# Check if UC eligible
print(f"  UC Eligible:              {baseline.calculate('is_SP_age', 2026)[0]}")
print(f"  Claims all entitled:      {baseline.calculate('claims_all_entitled_benefits', 2026)[0]}")

# Reform
reform = Simulation(reform=reform_dict, situation=situation)
print("\nREFORM:")
print(f"  Universal Credit:         £{reform.calculate('universal_credit', 2026)[0]:,.2f}")
print(f"  Child Tax Credit:         £{reform.calculate('child_tax_credit', 2026)[0]:,.2f}")
print(f"  Child Benefit:            £{reform.calculate('child_benefit', 2026)[0]:,.2f}")
print(f"  Income Support:           £{reform.calculate('income_support', 2026)[0]:,.2f}")
print(f"  Household Net Income:     £{reform.calculate('household_net_income', 2026)[0]:,.2f}")

print("\n" + "="*70)
print(f"DIFFERENCE: £{reform.calculate('household_net_income', 2026)[0] - baseline.calculate('household_net_income', 2026)[0]:,.2f}")
print("="*70)
