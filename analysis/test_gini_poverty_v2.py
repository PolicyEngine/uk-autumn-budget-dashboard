"""
Test Gini and Poverty - Matching Reference Code Exactly
Creates baseline/reform dicts in the same format as the reference code
"""

import sys
sys.path.insert(0, '/Users/janansadeqian/policyengine-uk')

import numpy as np
from policyengine_uk import Microsimulation, Scenario
from policyengine_uk.data import UKSingleYearDataset
from microdf import MicroSeries

DATASET_PATH = "/Users/janansadeqian/policyengine-uk-data/policyengine_uk_data/storage/enhanced_frs_2023_24.h5"

print("="*70)
print("Gini & Poverty Test - Matching Reference Code")
print("="*70)

print("\n1. Loading dataset and creating simulations...")
dataset = UKSingleYearDataset(file_path=DATASET_PATH)
baseline_sim = Microsimulation(dataset=dataset)

scenario = Scenario(
    parameter_changes={
        "gov.dwp.tax_credits.child_tax_credit.limit.child_count": {"2026": np.inf},
        "gov.dwp.universal_credit.elements.child.limit.child_count": {"2026": np.inf}
    }
)
reform_sim = Microsimulation(dataset=dataset, scenario=scenario)
print("   ✓ Simulations created")

print("\n2. Building baseline dict (matching reference format)...")
# Extract data in the same format as reference code expects
baseline = {
    "household_net_income": baseline_sim.calculate("household_net_income", period=2026, map_to="household").values,
    "household_weight": baseline_sim.calculate("household_weight", period=2026, map_to="household").values,
    "person_in_poverty": baseline_sim.calculate("in_poverty_bhc", period=2026).values,
    "person_weight": baseline_sim.calculate("person_weight", period=2026).values,
}

print("\n3. Building reform dict (matching reference format)...")
reform = {
    "household_net_income": reform_sim.calculate("household_net_income", period=2026, map_to="household").values,
    "household_weight": reform_sim.calculate("household_weight", period=2026, map_to="household").values,
    "person_in_poverty": reform_sim.calculate("in_poverty_bhc", period=2026).values,
    "person_weight": reform_sim.calculate("person_weight", period=2026).values,
}

print("\n4. Calculating Gini (matching reference code logic)...")
# The reference inequality_impact function expects baseline["gini"] to exist
# We need to calculate it the same way the backend does

# Create MicroSeries for household income with weights
baseline_income_ms = MicroSeries(baseline["household_net_income"], weights=baseline["household_weight"])
reform_income_ms = MicroSeries(reform["household_net_income"], weights=reform["household_weight"])

# Calculate Gini using MicroSeries .gini() method
baseline["gini"] = baseline_income_ms.gini()
reform["gini"] = reform_income_ms.gini()

# Now use the reference code's inequality_impact logic
gini_baseline = baseline["gini"]
gini_reform = reform["gini"]
gini_change = gini_reform - gini_baseline
gini_change_pct = (gini_change / gini_baseline) * 100

print(f"   Baseline Gini: {gini_baseline:.4f}")
print(f"   Reform Gini: {gini_reform:.4f}")
print(f"   Change: {gini_change:.4f} ({gini_change_pct:+.2f}%)")

print("\n5. Calculating Poverty (matching reference code logic)...")
# Use exact code from poverty_impact function
print(f"   Debug: person_in_poverty length: {len(baseline['person_in_poverty'])}")
print(f"   Debug: person_weight length: {len(baseline['person_weight'])}")

# Check if we have the array length mismatch issue
if len(baseline['person_in_poverty']) != len(baseline['person_weight']):
    print(f"   ⚠ Array length mismatch detected!")
    print(f"   This means person_weight includes ALL people, but person_in_poverty only includes")
    print(f"   people for whom poverty can be calculated.")
    print()
    print(f"   Solution: We need to get the matching subset of person_weight")
    print(f"   Or: Calculate poverty on the subset where it's defined (unweighted)")

    # Use unweighted approach (simple mean of boolean array)
    baseline_poverty_rate = baseline["person_in_poverty"].mean()
    reform_poverty_rate = reform["person_in_poverty"].mean()

else:
    # Arrays match - use the reference code exactly
    baseline_poverty = MicroSeries(
        baseline["person_in_poverty"], weights=baseline["person_weight"]
    )
    reform_poverty = MicroSeries(
        reform["person_in_poverty"], weights=baseline_poverty.weights
    )

    baseline_poverty_rate = baseline_poverty.mean()
    reform_poverty_rate = reform_poverty.mean()

poverty_change = reform_poverty_rate - baseline_poverty_rate
poverty_change_pct = (poverty_change / baseline_poverty_rate) * 100

print(f"   Baseline poverty rate: {baseline_poverty_rate*100:.2f}%")
print(f"   Reform poverty rate: {reform_poverty_rate*100:.2f}%")
print(f"   Change: {poverty_change*100:+.2f}pp ({poverty_change_pct:+.1f}%)")

print("\n" + "="*70)
print("Summary:")
print(f"  Gini change: {gini_change_pct:+.2f}%")
print(f"  Poverty change: {poverty_change_pct:+.1f}%")
print("="*70)
