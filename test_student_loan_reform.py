import sys

sys.path.insert(0, "src")

from policyengine_uk import Microsimulation

# Import reforms module directly without triggering __init__.py
import importlib.util

spec = importlib.util.spec_from_file_location(
    "reforms", "src/uk_budget_data/reforms.py"
)
reforms = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reforms)

# Get the student loan threshold freeze reform
slr_reform = reforms.get_reform("freeze_student_loan_thresholds")

if slr_reform:
    print("✓ Student loan threshold freeze reform found!")
    print(f"  ID: {slr_reform.id}")
    print(f"  Name: {slr_reform.name}")
    print(f"  Description: {slr_reform.description}")
    print()

    # Create baseline and reformed scenarios
    baseline_scenario = slr_reform.to_baseline_scenario()
    reform_scenario = slr_reform.to_scenario()

    # Create microsimulations
    print("Creating microsimulations (this may take a minute)...")
    baseline = Microsimulation(scenario=baseline_scenario)
    reformed = Microsimulation(scenario=reform_scenario)

    # OBR estimates from Autumn Budget 2025
    # "Freeze Plan 2 repayment threshold for three years from 6 April 2027"
    # OBR shows this as a COST (+£255-380m)
    obr_estimates = {
        2026: 0.285,  # 2025-26
        2027: 0.255,  # 2026-27 (policy starts April 2027 per OBR)
        2028: 0.290,  # 2027-28
        2029: 0.355,  # 2028-29
        2030: 0.380,  # 2029-30
    }

    # Test fiscal impact
    print("\n=== Student Loan Threshold Freeze: Comparison with OBR ===")
    print(
        f"{'Year':<8} {'Model Cost':>13} {'OBR Cost':>13} {'Difference':>13} {'Fewer Payers':>18}"
    )
    print("=" * 72)

    for year in [2025, 2026, 2027, 2028, 2029]:
        # Calculate student loan repayments (modelled)
        baseline_slr = (
            baseline.calculate(
                "student_loan_repayments_modelled", period=year
            ).sum()
            / 1e9
        )
        reform_slr = (
            reformed.calculate(
                "student_loan_repayments_modelled", period=year
            ).sum()
            / 1e9
        )
        # Cost to government = baseline repayments - reform repayments (fewer collections)
        cost = baseline_slr - reform_slr

        # Count change in payers (should be fewer in reform)
        baseline_repayers = (
            baseline.calculate("student_loan_repayments_modelled", period=year)
            > 0
        ).sum()
        reform_repayers = (
            reformed.calculate("student_loan_repayments_modelled", period=year)
            > 0
        ).sum()
        fewer_payers = baseline_repayers - reform_repayers

        # Get OBR estimate
        obr_value = obr_estimates.get(year, 0.0)
        difference = cost - obr_value

        print(
            f"{year:<8} £{cost:>11.3f}bn £{obr_value:>11.3f}bn £{difference:>11.3f}bn {fewer_payers:>16,.0f}"
        )

    print("\n📊 INTERPRETATION:")
    print("    Baseline: Thresholds frozen at 2025 levels (stricter)")
    print("    Reform:   Thresholds uprate with RPI from 2027 (more generous)")
    print("    Result:   Fewer repayments collected = Cost to government")

    # Verify via HBAI household net income (should increase in reform)
    print("\n=== Verification via HBAI Household Net Income ===")
    print(
        f"{'Year':<8} {'Baseline HBAI':>15} {'Reform HBAI':>15} {'HH Gain':>15}"
    )
    print("=" * 58)

    for year in [2026, 2027, 2028, 2029]:
        baseline_hbai = (
            baseline.calculate(
                "hbai_household_net_income", period=year, map_to="household"
            ).sum()
            / 1e9
        )
        reform_hbai = (
            reformed.calculate(
                "hbai_household_net_income", period=year, map_to="household"
            ).sum()
            / 1e9
        )
        # Household gain = higher income in reform (fewer repayments)
        hh_gain = reform_hbai - baseline_hbai

        print(
            f"{year:<8} £{baseline_hbai:>13.2f}bn £{reform_hbai:>13.2f}bn £{hh_gain:>13.3f}bn"
        )

    print("\n✓ Test completed successfully!")
else:
    print("✗ Student loan threshold freeze reform not found!")
