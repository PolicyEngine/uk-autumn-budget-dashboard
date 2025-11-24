"""
Test Gini Coefficient Calculation - Following Reference Code Pattern
Expected result: -0.5% (decrease in inequality)
"""

import sys
sys.path.insert(0, '/Users/janansadeqian/policyengine-uk')

import numpy as np
from policyengine_uk import Microsimulation, Scenario
from policyengine_uk.data import UKSingleYearDataset
from microdf import MicroSeries

DATASET_PATH = "/Users/janansadeqian/policyengine-uk-data/policyengine_uk_data/storage/enhanced_frs_2023_24.h5"

print("="*70)
print("Gini Coefficient Test - Following Reference Code Pattern")
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
reformed_sim = Microsimulation(dataset=dataset, scenario=scenario)
print("   ✓ Simulations created")

print("\n2. Building baseline and reform dicts (matching reference format)...")

# Method from reference code: Extract data into dict format
baseline = {
    "household_net_income": baseline_sim.calculate("household_net_income", period=2026, map_to="household").values,
    "household_weight": baseline_sim.calculate("household_weight", period=2026, map_to="household").values,
}

reform = {
    "household_net_income": reformed_sim.calculate("household_net_income", period=2026, map_to="household").values,
    "household_weight": reformed_sim.calculate("household_weight", period=2026, map_to="household").values,
}

print(f"   Baseline households: {len(baseline['household_net_income']):,}")
print(f"   Total population weight: {baseline['household_weight'].sum()/1e6:.2f} million")

print("\n3. Calculating Gini using MicroSeries (reference pattern)...")

# Create MicroSeries with income and weights
baseline_income = MicroSeries(
    baseline["household_net_income"], weights=baseline["household_weight"]
)
reform_income = MicroSeries(
    reform["household_net_income"], weights=baseline["household_weight"]
)

# Calculate Gini coefficient
baseline["gini"] = baseline_income.gini()
reform["gini"] = reform_income.gini()

# Calculate change
gini_change = reform["gini"] - baseline["gini"]
gini_change_pct = (gini_change / baseline["gini"]) * 100

print(f"\n   Baseline Gini: {baseline['gini']:.4f}")
print(f"   Reform Gini:   {reform['gini']:.4f}")
print(f"   Gini change:   {gini_change:.4f} ({gini_change_pct:+.2f}%)")

print("\n" + "="*70)
print("Results:")
print(f"  Gini coefficient change: {gini_change:.4f} ({gini_change_pct:+.2f}%)")
print(f"  Expected: ~-0.5% (decrease in inequality)")
print(f"  Actual:   {gini_change_pct:+.2f}%")
if abs(gini_change_pct - (-0.5)) < 0.1:
    print("  ✓ Result matches expected value!")
else:
    print(f"  ⚠ Result differs from expected by {abs(gini_change_pct - (-0.5)):.2f}pp")
print("="*70)

print("\n4. Testing with equivalised household income...")
print("   (Using household equivalisation scale)")

# Try with equivalised income
baseline_equiv = {
    "household_net_income": baseline_sim.calculate("equivalised_household_net_income", period=2026, map_to="household").values,
    "household_weight": baseline_sim.calculate("household_weight", period=2026, map_to="household").values,
}

reform_equiv = {
    "household_net_income": reformed_sim.calculate("equivalised_household_net_income", period=2026, map_to="household").values,
    "household_weight": reformed_sim.calculate("household_weight", period=2026, map_to="household").values,
}

baseline_income_equiv = MicroSeries(
    baseline_equiv["household_net_income"], weights=baseline_equiv["household_weight"]
)
reform_income_equiv = MicroSeries(
    reform_equiv["household_net_income"], weights=baseline_equiv["household_weight"]
)

baseline_gini_equiv = baseline_income_equiv.gini()
reform_gini_equiv = reform_income_equiv.gini()
gini_change_equiv = reform_gini_equiv - baseline_gini_equiv
gini_change_pct_equiv = (gini_change_equiv / baseline_gini_equiv) * 100

print(f"\n   Baseline Gini (equiv): {baseline_gini_equiv:.4f}")
print(f"   Reform Gini (equiv):   {reform_gini_equiv:.4f}")
print(f"   Gini change (equiv):   {gini_change_equiv:.4f} ({gini_change_pct_equiv:+.2f}%)")

print("\n" + "="*70)
print("Comparison:")
print(f"  Non-equivalised: {gini_change_pct:+.2f}%")
print(f"  Equivalised:     {gini_change_pct_equiv:+.2f}%")
print("="*70)
