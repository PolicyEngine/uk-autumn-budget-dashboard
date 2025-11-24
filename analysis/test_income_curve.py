"""
Test Income Curve Generation - Baseline vs Reform
Generates household net income across different employment income levels
for a family with 3 children affected by two-child limit reform.
"""
import sys
sys.path.insert(0, '/Users/janansadeqian/policyengine-uk')

import numpy as np
import pandas as pd
from policyengine_uk import Simulation

print("="*70)
print("Income Curve Test - Two-Child Limit Reform")
print("="*70)

# Define the reform (removing two-child limit) as a dict
reform_dict = {
    "gov.dwp.tax_credits.child_tax_credit.limit.child_count": {
        "2025-01-01.2100-12-31": 102
    },
    "gov.dwp.universal_credit.elements.child.limit.child_count": {
        "2025-01-01.2100-12-31": 100
    }
}

# Base situation: Family with 3 children
base_situation = {
    "people": {
        "you": {
            "age": {"2026": 40},
            "employment_income": {"2026": 0}  # Will vary this
        },
        "your partner": {
            "age": {"2026": 40},
            "employment_income": {"2026": 0}
        },
        "your first child": {
            "age": {"2026": 7},
            "employment_income": {"2026": 0}
        },
        "your second child": {
            "age": {"2026": 5},
            "employment_income": {"2026": 0}
        },
        "your third child": {
            "age": {"2026": 3},
            "employment_income": {"2026": 0}
        }
    },
    "benunits": {
        "your immediate family": {
            "members": [
                "you",
                "your partner",
                "your first child",
                "your second child",
                "your third child"
            ],
            "would_claim_uc": {"2026": True}
        }
    },
    "households": {
        "your household": {
            "brma": {"2026": "MAIDSTONE"},
            "region": {"2026": "LONDON"},
            "members": [
                "you",
                "your partner",
                "your first child",
                "your second child",
                "your third child"
            ],
            "local_authority": {"2026": "MAIDSTONE"}
        }
    }
}

# Employment income range: £0 to £200,000
employment_incomes = np.linspace(0, 200_000, 20)

print("\nCalculating household net income across employment income range...")
print(f"Testing {len(employment_incomes)} points from £0 to £200,000\n")

results = []

for emp_income in employment_incomes:
    # Update employment income for household head
    situation = base_situation.copy()
    situation["people"]["you"]["employment_income"]["2026"] = float(emp_income)

    # Baseline simulation (no reform)
    baseline_sim = Simulation(situation=situation)
    baseline_net_income = baseline_sim.calculate("household_net_income", 2026)[0]

    # Reform simulation
    reform_sim = Simulation(reform=reform_dict, situation=situation)
    reform_net_income = reform_sim.calculate("household_net_income", 2026)[0]

    # Store results
    results.append({
        'employment_income': emp_income,
        'baseline_net_income': baseline_net_income,
        'reform_net_income': reform_net_income,
        'difference': reform_net_income - baseline_net_income
    })

# Convert to DataFrame
df = pd.DataFrame(results)

print("Sample results:")
print("="*70)
print(f"{'Employment Income':>20} {'Baseline Net':>20} {'Reform Net':>20} {'Difference':>15}")
print("="*70)

# Show all points
sample_indices = range(len(df))
for idx in sample_indices:
    row = df.iloc[idx]
    print(f"£{row['employment_income']:>18,.0f} £{row['baseline_net_income']:>18,.0f} £{row['reform_net_income']:>18,.0f} £{row['difference']:>13,.0f}")

print("="*70)

# Save to CSV
output_file = "/Users/janansadeqian/uk-autumn-budget-dashbaord/analysis/income_curve_data.csv"
df.to_csv(output_file, index=False)
print(f"\n✓ Data saved to: {output_file}")

# Calculate some statistics
max_difference = df['difference'].max()
max_diff_income = df.loc[df['difference'].idxmax(), 'employment_income']

print("\nKey findings:")
print(f"  - Maximum benefit: £{max_difference:,.0f}")
print(f"  - Occurs at employment income: £{max_diff_income:,.0f}")
print(f"  - Reform increases income across employment range: {(df['difference'] >= 0).all()}")

print("\n" + "="*70)
print("Generating plot...")
print("="*70)

# Plot the results
import matplotlib.pyplot as plt

plt.figure(figsize=(12, 7))
plt.plot(df['employment_income'], df['baseline_net_income'],
         label='Baseline', color='gray', linewidth=2, linestyle='-')
plt.plot(df['employment_income'], df['reform_net_income'],
         label='Reform', color='#4A7BA7', linewidth=2, linestyle='--')

plt.xlabel('Household head employment income', fontsize=12)
plt.ylabel('Household net income', fontsize=12)
plt.title('Policy #93219: Baseline vs Reform - Household Net Income', fontsize=14, pad=20)
plt.legend(loc='upper left', fontsize=11)
plt.grid(True, alpha=0.3)

# Format axes as currency
ax = plt.gca()
ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'£{int(x):,}'))
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, p: f'£{int(y):,}'))

plt.tight_layout()

# Save plot
plot_file = "/Users/janansadeqian/uk-autumn-budget-dashbaord/analysis/income_curve_plot.png"
plt.savefig(plot_file, dpi=150, bbox_inches='tight')
print(f"\n✓ Plot saved to: {plot_file}")

plt.show()
