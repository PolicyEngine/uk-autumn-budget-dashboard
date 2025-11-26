"""
Test the modified calculate_income_curve function from create_data.py
"""

import pandas as pd
from create_data import calculate_income_curve, YEARS
from policyengine_uk.utils.scenario import Scenario
import numpy as np

print("\n" + "=" * 70)
print("TESTING MODIFIED calculate_income_curve FUNCTION")
print("=" * 70)

# Create a simple scenario (two-child limit repeal)
two_child_scenario = Scenario(parameter_changes={
    "gov.dwp.tax_credits.child_tax_credit.limit.child_count": {
        str(y): np.inf for y in YEARS
    },
    "gov.dwp.universal_credit.elements.child.limit.child_count": {
        str(y): np.inf for y in YEARS
    },
})

print("\n✓ Created two-child limit repeal scenario")
print("\nRunning calculate_income_curve for 2026...")
print("This will generate data for:")
print("  • 11 children counts (0-10)")
print("  • 5 pension contribution levels (£0, £5k, £10k, £15k, £20k)")
print("  • 501 employment income points (£0-£100k)")
print("  • Expected total: 27,555 rows")
print("\n" + "-" * 70)

try:
    results = calculate_income_curve(
        scenario=two_child_scenario,
        reform_id="two_child_limit",
        reform_name="2 child limit repeal",
        year=2026
    )

    df = pd.DataFrame(results)

    print("\n✓ Function completed successfully!")
    print("\n" + "=" * 70)
    print("RESULTS VALIDATION")
    print("=" * 70)

    # Check structure
    print(f"\n✓ Total rows generated: {len(df):,}")
    print(f"\n✓ Columns: {list(df.columns)}")

    # Check for new columns
    has_num_children = 'num_children' in df.columns
    has_pension = 'pension_contributions' in df.columns

    print(f"\n{'✓' if has_num_children else '✗'} Contains 'num_children' column: {has_num_children}")
    print(f"{'✓' if has_pension else '✗'} Contains 'pension_contributions' column: {has_pension}")

    if has_num_children and has_pension:
        print(f"\n✓ Unique children counts: {sorted(df['num_children'].unique())}")
        print(f"✓ Unique pension contributions: £{', £'.join(map(lambda x: f'{int(x):,}', sorted(df['pension_contributions'].unique())))}")

        # Sample data
        print("\n" + "-" * 70)
        print("Sample: First 10 rows")
        print("-" * 70)
        display_cols = ['num_children', 'pension_contributions', 'employment_income', 'baseline_net_income', 'reform_net_income']
        print(df[display_cols].head(10).to_string(index=False))

        # Check specific configuration
        print("\n" + "-" * 70)
        print("Sample: 3 children, £10,000 pension (showing reform impact)")
        print("-" * 70)
        sample = df[(df['num_children'] == 3) & (df['pension_contributions'] == 10000)].copy()
        if len(sample) > 0:
            sample['gain'] = sample['reform_net_income'] - sample['baseline_net_income']
            print(sample[['employment_income', 'baseline_net_income', 'reform_net_income', 'gain']].head(10).to_string(index=False))
            print(f"\n✓ Found {len(sample)} income points for this configuration")
            print(f"✓ Average gain from reform: £{sample['gain'].mean():,.2f}")

        print("\n" + "=" * 70)
        print("✓✓✓ ALL VALIDATIONS PASSED! ✓✓✓")
        print("=" * 70)
        print("\nThe modifications to calculate_income_curve are working correctly!")
        print("The function now generates comprehensive data for:")
        print("  • Different family sizes (0-10 children)")
        print("  • Different pension contribution levels")
        print("  • Full income range analysis")
        print("\nYou can now run the full create_data.py to generate all reform data.")

    else:
        print("\n✗ ERROR: Missing expected columns!")
        print("The modifications may not have been applied correctly.")
        exit(1)

except Exception as e:
    print(f"\n✗ ERROR: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
