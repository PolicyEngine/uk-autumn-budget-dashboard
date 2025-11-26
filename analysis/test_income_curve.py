"""
Test script for income curve calculation with varying children and pension contributions.
Tests by importing directly from create_data.py
"""

import sys
import numpy as np
import pandas as pd

# Import from the actual create_data.py file
from create_data import calculate_income_curve, YEARS

# Try different scenario approaches
try:
    from policyengine_uk import Scenario
    print("✓ Imported Scenario from policyengine_uk")
except ImportError:
    print("⚠ Could not import Scenario - trying policyengine_core")
    try:
        from policyengine_core.reforms import Reform
        print("✓ Using Reform from policyengine_core")
        # Use Reform as a substitute
        Scenario = Reform
    except ImportError:
        print("✗ Could not import scenario handling")
        sys.exit(1)


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("TESTING TWO-CHILD LIMIT REPEAL")
    print("=" * 60)

    # Create two-child limit repeal scenario
    try:
        from policyengine_uk import Scenario
        two_child_scenario = Scenario(
            parameter_changes={
                "gov.dwp.tax_credits.child_tax_credit.limit.child_count": {
                    str(y): np.inf for y in YEARS
                },
                "gov.dwp.universal_credit.elements.child.limit.child_count": {
                    str(y): np.inf for y in YEARS
                },
            }
        )
    except Exception as e:
        print(f"Error creating scenario: {e}")
        print("\nTrying direct PolicyEngine API...")
        # Alternative: use PolicyEngine's reform API
        from policyengine_core.reforms import Reform
        from policyengine_uk import CountryTaxBenefitSystem

        def two_child_reform(parameters):
            for year in YEARS:
                parameters.gov.dwp.tax_credits.child_tax_credit.limit.child_count.update(
                    period=str(year), value=np.inf
                )
                parameters.gov.dwp.universal_credit.elements.child.limit.child_count.update(
                    period=str(year), value=np.inf
                )
            return parameters

        class TwoChildReform(Reform):
            def apply(self):
                self.modify_parameters(two_child_reform)

        two_child_scenario = TwoChildReform

    print(f"\n✓ Created two-child limit repeal scenario")

    # Run test for 2026 only
    print("\nRunning calculate_income_curve for 2026...")
    try:
        results = calculate_income_curve(
            scenario=two_child_scenario,
            reform_id="two_child_limit",
            reform_name="2 child limit repeal",
            year=2026
        )

        # Convert to DataFrame
        df = pd.DataFrame(results)

        print("\n" + "=" * 60)
        print("RESULTS SUMMARY")
        print("=" * 60)
        print(f"\nTotal rows generated: {len(df)}")
        print(f"\nColumns: {list(df.columns)}")

        if 'num_children' in df.columns:
            print(f"\n✓ SUCCESS: 'num_children' column exists!")
            print(f"Unique children counts: {sorted(df['num_children'].unique())}")
        else:
            print(f"\n✗ ERROR: 'num_children' column missing!")

        if 'pension_contributions' in df.columns:
            print(f"\n✓ SUCCESS: 'pension_contributions' column exists!")
            print(f"Unique pension contributions: {sorted(df['pension_contributions'].unique())}")
        else:
            print(f"\n✗ ERROR: 'pension_contributions' column missing!")

        print("\n" + "-" * 60)
        print("Sample data (first 15 rows):")
        print("-" * 60)
        print(df.head(15).to_string(index=False))

        # Check specific combinations
        if 'num_children' in df.columns and 'pension_contributions' in df.columns:
            print("\n" + "-" * 60)
            print("Data shape check:")
            print("-" * 60)
            for n_child in sorted(df['num_children'].unique())[:3]:
                for pension in sorted(df['pension_contributions'].unique())[:2]:
                    count = len(df[(df['num_children'] == n_child) & (df['pension_contributions'] == pension)])
                    print(f"  {n_child} children, £{pension:,} pension: {count} income points")

            print("\n" + "-" * 60)
            print("Sample: 3 children, £10,000 pension (if exists):")
            print("-" * 60)
            sample = df[(df['num_children'] == 3) & (df['pension_contributions'] == 10000)]
            if len(sample) > 0:
                sample['income_gain'] = sample['reform_net_income'] - sample['baseline_net_income']
                print(sample[['employment_income', 'baseline_net_income', 'reform_net_income', 'income_gain']].head(10).to_string(index=False))
                print(f"\n✓ Found {len(sample)} rows for this combination")
            else:
                print("No data found for this combination")

        # Save test results
        output_path = "./test_income_curve_output.csv"
        df.to_csv(output_path, index=False)
        print(f"\n✓ Test results saved to: {output_path}")
        print("\n" + "=" * 60)
        print("✓ TEST COMPLETED SUCCESSFULLY!")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ Error running test: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
