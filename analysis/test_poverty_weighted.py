"""
Test Poverty with WEIGHTED calculation (matching poverty-analysis.ipynb)
"""

import sys
sys.path.insert(0, '/Users/janansadeqian/policyengine-uk')

import numpy as np
import pandas as pd
from policyengine_uk import Microsimulation, Scenario
from policyengine_uk.data import UKSingleYearDataset

DATASET_PATH = "/Users/janansadeqian/policyengine-uk-data/policyengine_uk_data/storage/enhanced_frs_2023_24.h5"

print("="*70)
print("Poverty Test - WEIGHTED Calculation (matching notebook)")
print("="*70)

print("\n1. Loading dataset and creating simulations...")
dataset = UKSingleYearDataset(file_path=DATASET_PATH)
baseline = Microsimulation(dataset=dataset)

scenario = Scenario(
    parameter_changes={
        "gov.dwp.tax_credits.child_tax_credit.limit.child_count": {"2026": np.inf},
        "gov.dwp.universal_credit.elements.child.limit.child_count": {"2026": np.inf}
    }
)
reformed = Microsimulation(dataset=dataset, scenario=scenario)
print("   ✓ Simulations created")

print("\n2. Calculating poverty using WEIGHTED method (from notebook)...")

# Function from poverty-analysis.ipynb
def calculate_poverty_stats(df, metric):
    """Calculate weighted poverty rate using person_weight"""
    pop = df['person_weight'].sum() / 1e6
    num_in_poverty = df[df[metric] == True]['person_weight'].sum() / 1e6
    rate = (num_in_poverty / pop) * 100
    return rate, num_in_poverty, pop

# Load data into DataFrame (matching notebook pattern)
vars_to_load = ['person_weight', 'in_poverty_bhc']

print("\n   Loading baseline data...")
baseline_dict = {}
for var in vars_to_load:
    baseline_dict[var] = baseline.calculate(var, 2026, map_to="person").values
baseline_df = pd.DataFrame(baseline_dict)

print("   Loading reformed data...")
reformed_dict = {}
for var in vars_to_load:
    reformed_dict[var] = reformed.calculate(var, 2026, map_to="person").values
reformed_df = pd.DataFrame(reformed_dict)

# Calculate weighted poverty rates
baseline_rate, baseline_num, baseline_pop = calculate_poverty_stats(baseline_df, 'in_poverty_bhc')
reformed_rate, reformed_num, reformed_pop = calculate_poverty_stats(reformed_df, 'in_poverty_bhc')

poverty_reduction = baseline_rate - reformed_rate
poverty_reduction_pct = (poverty_reduction / baseline_rate) * 100

print(f"\n   Results:")
print(f"   ✓ Baseline poverty rate: {baseline_rate:.2f}%")
print(f"   ✓ Reformed poverty rate: {reformed_rate:.2f}%")
print(f"   ✓ Poverty reduction: {poverty_reduction:+.2f}pp ({poverty_reduction_pct:+.1f}%)")
print(f"   ✓ Population: {baseline_pop:.2f} million")
print(f"   ✓ People lifted out of poverty: {baseline_num - reformed_num:.2f} million")

print("\n" + "="*70)
print("Summary:")
print(f"  Poverty reduction: {poverty_reduction:+.2f}pp ({poverty_reduction_pct:+.1f}%)")
print("="*70)
