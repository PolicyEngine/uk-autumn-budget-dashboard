"""
Quick test script for Gini and Poverty calculations
Tests only these two metrics without running full analysis
"""

import sys
sys.path.insert(0, '/Users/janansadeqian/policyengine-uk')

import numpy as np
from policyengine_uk import Microsimulation, Scenario
from policyengine_uk.data import UKSingleYearDataset

DATASET_PATH = "/Users/janansadeqian/policyengine-uk-data/policyengine_uk_data/storage/enhanced_frs_2023_24.h5"

print("="*70)
print("Quick Gini & Poverty Test")
print("="*70)

print("\n1. Loading dataset...")
dataset = UKSingleYearDataset(file_path=DATASET_PATH)
print("   ✓ Dataset loaded")

print("\n2. Creating simulations...")
# Baseline
baseline = Microsimulation(dataset=dataset)

# Reform: Remove two-child limit
scenario = Scenario(
    parameter_changes={
        "gov.dwp.tax_credits.child_tax_credit.limit.child_count": {
            "2026": np.inf,
        },
        "gov.dwp.universal_credit.elements.child.limit.child_count": {
            "2026": np.inf,
        }
    }
)
reformed = Microsimulation(dataset=dataset, scenario=scenario)
print("   ✓ Simulations created")

print("\n3. Calculating Gini coefficient (manual calculation)...")
from microdf import MicroSeries

# Get household income and weights
baseline_income = baseline.calculate("household_net_income", period=2026, map_to="household")
reform_income = reformed.calculate("household_net_income", period=2026, map_to="household")
household_weight = baseline.calculate("household_weight", period=2026, map_to="household")

# Create MicroSeries
baseline_income_ms = MicroSeries(baseline_income.values, weights=household_weight.values)
reform_income_ms = MicroSeries(reform_income.values, weights=household_weight.values)

# Calculate Gini using MicroSeries .gini() method
baseline_gini = baseline_income_ms.gini()
reformed_gini = reform_income_ms.gini()

gini_change = reformed_gini - baseline_gini
gini_change_pct = (gini_change / baseline_gini) * 100

print(f"   ✓ Baseline Gini: {baseline_gini:.4f}")
print(f"   ✓ Reformed Gini: {reformed_gini:.4f}")
print(f"   ✓ Change: {gini_change:.4f} ({gini_change_pct:+.2f}%)")

print("\n4. Calculating poverty rate (manual calculation)...")

# Get poverty status and weights - person level
# Note: in_poverty_bhc returns True/False for people in poverty
baseline_in_poverty = baseline.calculate('in_poverty_bhc', period=2026)
reformed_in_poverty = reformed.calculate('in_poverty_bhc', period=2026)

# Get person weights - but only for the subset where poverty is defined
# Strategy: Calculate poverty rate as simple mean (poverty is boolean)
baseline_poverty_rate = baseline_in_poverty.values.mean() * 100
reformed_poverty_rate = reformed_in_poverty.values.mean() * 100

poverty_rate_change = reformed_poverty_rate - baseline_poverty_rate
poverty_rate_change_pct = (poverty_rate_change / baseline_poverty_rate) * 100

print(f"   Note: Using unweighted poverty rate (poverty defined for {len(baseline_in_poverty.values):,} people)")
print(f"   ✓ Baseline poverty rate: {baseline_poverty_rate:.2f}%")
print(f"   ✓ Reformed poverty rate: {reformed_poverty_rate:.2f}%")
print(f"   ✓ Change: {poverty_rate_change:+.2f}pp ({poverty_rate_change_pct:+.1f}%)")

print("\n" + "="*70)
print("Test complete!")
print("="*70)
