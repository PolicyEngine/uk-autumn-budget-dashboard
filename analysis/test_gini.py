"""Test Gini index calculation for two-child limit reform."""

import sys
sys.path.insert(0, '/Users/janansadeqian/policyengine-uk')

import numpy as np
from policyengine_uk import Microsimulation, Scenario


def calculate_inequality_metrics(simulation: Microsimulation, year: int = 2026):
    """Calculate Gini coefficient and top shares from simulation.

    This exactly replicates the GeneralEconomyTask.calculate_inequality_metrics method.

    Args:
        simulation: PolicyEngine microsimulation
        year: Year to calculate metrics for

    Returns:
        Tuple of (gini, top_10_share, top_1_share)
    """
    # Get household count people for weighting
    household_count_people = simulation.calculate("household_count_people", period=year)

    # Get weighted household income (equivalent to _get_weighted_household_income)
    income = simulation.calculate("equiv_household_net_income", period=year)
    income[income < 0] = 0
    income.weights *= household_count_people

    # Calculate Gini
    try:
        gini = income.gini()
    except Exception as e:
        print(f"WARNING: Gini index calculations resulted in an error: returning no change, but this is inaccurate.")
        print(f"Error: {e}")
        gini = 0.4

    # Calculate top 10% and top 1% shares
    in_top_10_pct = income.decile_rank() == 10
    in_top_1_pct = income.percentile_rank() == 100

    # Divide weights by household_count_people for share calculations
    income.weights /= household_count_people

    top_10_share = (
        income[in_top_10_pct].sum() / income.sum()
    )
    top_1_share = (
        income[in_top_1_pct].sum() / income.sum()
    )

    return gini, top_10_share, top_1_share


def main():
    """Test Gini calculation for two-child limit reform."""

    year = 2026

    print("Creating baseline simulation...")
    baseline = Microsimulation()
    print("✓ Baseline created")

    print("\nCreating reform simulation (abolish two-child limit)...")
    print("Reform parameters:")
    print("  - Child tax credit limit: unlimited")
    print("  - Universal credit child limit: unlimited")

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

    reform = Microsimulation(scenario=scenario)
    print("✓ Reform created")

    print(f"\nCalculating inequality metrics for year {year}...")

    baseline_gini, baseline_top10, baseline_top1 = calculate_inequality_metrics(baseline, year)
    reform_gini, reform_top10, reform_top1 = calculate_inequality_metrics(reform, year)

    print(f"\n{'Metric':<20} {'Baseline':>15} {'Reform':>15} {'Change':>15} {'% Change':>12}")
    print("=" * 80)

    # Gini index
    gini_change = reform_gini - baseline_gini
    gini_pct_change = (gini_change / baseline_gini) * 100
    print(f"{'Gini index':<20} {baseline_gini:>15.6f} {reform_gini:>15.6f} {gini_change:>+15.6f} {gini_pct_change:>+11.2f}%")

    # Top 10% share
    top10_change = reform_top10 - baseline_top10
    top10_pct_change = (top10_change / baseline_top10) * 100
    print(f"{'Top 10% share':<20} {baseline_top10:>15.6f} {reform_top10:>15.6f} {top10_change:>+15.6f} {top10_pct_change:>+11.2f}%")

    # Top 1% share
    top1_change = reform_top1 - baseline_top1
    top1_pct_change = (top1_change / baseline_top1) * 100
    print(f"{'Top 1% share':<20} {baseline_top1:>15.6f} {reform_top1:>15.6f} {top1_change:>+15.6f} {top1_pct_change:>+11.2f}%")

    print("\n" + "=" * 80)

    if gini_change < 0:
        print("✓ Reform reduces inequality (Gini decreased)")
    elif gini_change > 0:
        print("✗ Reform increases inequality (Gini increased)")
    else:
        print("→ Reform has no effect on inequality")

    print("\nDone!")


if __name__ == "__main__":
    main()
