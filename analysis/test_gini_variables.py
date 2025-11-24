"""
Test to find Gini coefficient variables in PolicyEngine UK
"""

import sys
sys.path.insert(0, '/Users/janansadeqian/policyengine-uk')

from policyengine_uk import Microsimulation
from policyengine_uk.data import UKSingleYearDataset

DATASET_PATH = "/Users/janansadeqian/policyengine-uk-data/policyengine_uk_data/storage/enhanced_frs_2023_24.h5"

print("="*70)
print("Testing Gini Coefficient Variables in PolicyEngine UK")
print("="*70)

dataset = UKSingleYearDataset(file_path=DATASET_PATH)
sim = Microsimulation(dataset=dataset)

# Try different possible Gini variable names
possible_gini_vars = [
    'gini',
    'household_income_gini',
    'equivalised_household_income_gini',
    'income_gini',
    'household_net_income_gini',
    'equivalised_household_net_income_gini',
]

print("\nTrying to calculate Gini variables...\n")

for var in possible_gini_vars:
    print(f"Testing: {var}")
    try:
        result = sim.calculate(var, 2026)
        print(f"   ✓ SUCCESS! Variable exists")
        print(f"   Result type: {type(result)}")
        print(f"   Result shape: {result.values.shape if hasattr(result, 'values') else 'N/A'}")
        print(f"   Value: {result.values[0] if hasattr(result, 'values') and len(result.values) > 0 else result}")
        print()
    except Exception as e:
        error_msg = str(e)
        if "does not exist" in error_msg:
            print(f"   ✗ Variable does not exist")
        else:
            print(f"   ✗ Error: {error_msg}")
        print()

print("="*70)
print("If no variable exists, use MicroSeries.gini() method instead")
print("="*70)
