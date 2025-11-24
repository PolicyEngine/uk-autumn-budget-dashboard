"""
Simple Test - Using .mean() directly on PolicyEngine results
Matching the exact pattern from the user's code
"""

import sys
sys.path.insert(0, '/Users/janansadeqian/policyengine-uk')

import numpy as np
from policyengine_uk import Microsimulation, Scenario
from policyengine_uk.data import UKSingleYearDataset
from microdf import MicroSeries

DATASET_PATH = "/Users/janansadeqian/policyengine-uk-data/policyengine_uk_data/storage/enhanced_frs_2023_24.h5"

print("="*70)
print("Simple Gini & Poverty Test - Direct .mean() Pattern")
print("="*70)

print("\n1. Loading dataset and creating simulations...")
dataset = UKSingleYearDataset(file_path=DATASET_PATH)
baseline = Microsimulation(dataset=dataset)

scenario = Scenario(
    parameter_changes={
        "gov.dwp.tax_credits.child_tax_credit.limit.child_count": {"2025": np.inf, "2026": np.inf},
        "gov.dwp.universal_credit.elements.child.limit.child_count": {"2025": np.inf, "2026": np.inf}
    }
)
reformed = Microsimulation(dataset=dataset, scenario=scenario)
print("   ✓ Simulations created")

print("\n2. Testing poverty with direct .mean() pattern...")

# Test different poverty variables and years
poverty_tests = [
    ("in_poverty", 2025, "Absolute poverty (year 2025)"),
    ("in_poverty_bhc", 2025, "Absolute poverty BHC (year 2025)"),
    ("in_poverty", 2026, "Absolute poverty (year 2026)"),
    ("in_poverty_bhc", 2026, "Absolute poverty BHC (year 2026)"),
]

for var, year, label in poverty_tests:
    print(f"\n   Testing: {label}")
    print(f"   Variable: {var}, Year: {year}")

    # Unweighted mean
    baseline_poverty_unweighted = baseline.calculate(var, year).mean()
    reformed_poverty_unweighted = reformed.calculate(var, year).mean()
    reduction_unweighted = baseline_poverty_unweighted - reformed_poverty_unweighted
    reduction_pct_unweighted = (reduction_unweighted / baseline_poverty_unweighted) * 100

    # Weighted mean (using person_weight)
    baseline_in_poverty = baseline.calculate(var, year)
    reformed_in_poverty = reformed.calculate(var, year)
    person_weight = baseline.calculate("person_weight", year)

    # Weighted average: sum(value * weight) / sum(weight)
    baseline_poverty_weighted = (baseline_in_poverty.values * person_weight.values).sum() / person_weight.values.sum()
    reformed_poverty_weighted = (reformed_in_poverty.values * person_weight.values).sum() / person_weight.values.sum()
    reduction_weighted = baseline_poverty_weighted - reformed_poverty_weighted
    reduction_pct_weighted = (reduction_weighted / baseline_poverty_weighted) * 100

    print(f"   → Unweighted: {baseline_poverty_unweighted*100:.2f}% → {reformed_poverty_unweighted*100:.2f}% = {reduction_pct_unweighted:+.1f}%")
    print(f"   → Weighted:   {baseline_poverty_weighted*100:.2f}% → {reformed_poverty_weighted*100:.2f}% = {reduction_pct_weighted:+.1f}%")

print("\n3. Calculating Gini with MicroSeries...")
# Get household income and weights
baseline_income = baseline.calculate("household_net_income", period=2026, map_to="household")
reform_income = reformed.calculate("household_net_income", period=2026, map_to="household")
household_weight = baseline.calculate("household_weight", period=2026, map_to="household")

# Create MicroSeries for Gini calculation
baseline_income_ms = MicroSeries(baseline_income.values, weights=household_weight.values)
reform_income_ms = MicroSeries(reform_income.values, weights=household_weight.values)

baseline_gini = baseline_income_ms.gini()
reform_gini = reform_income_ms.gini()
gini_change = reform_gini - baseline_gini
gini_change_pct = (gini_change / baseline_gini) * 100

print(f"   ✓ Baseline Gini: {baseline_gini:.4f}")
print(f"   ✓ Reform Gini: {reform_gini:.4f}")
print(f"   ✓ Gini change: {gini_change:.4f} ({gini_change_pct:+.2f}%)")

print("\n" + "="*70)
print("Summary:")
print(f"  Poverty reduction: {poverty_reduction_pct:+.1f}%")
print(f"  Gini change: {gini_change_pct:+.2f}%")
print("="*70)
