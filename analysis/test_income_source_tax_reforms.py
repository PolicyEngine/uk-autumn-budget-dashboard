"""
Test suite for income source-specific tax rate increases.

Tests three reforms:
1. Dividends Tax Increase (from April 2026): +2pp across rates
2. Savings Income Tax Increase (from April 2027): +2pp across rates
3. Property Income Tax Increase (from April 2027): +2pp across rates

Expected yields:
- Dividends: £1.2 billion/year average from 2027-28
- Savings: £0.5 billion/year average from 2028-29
- Property: £0.5 billion/year average from 2028-29
- Combined: £2.1 billion by 2029-30
"""

import numpy as np
import pytest
from pathlib import Path
from policyengine_uk import Microsimulation, Scenario
from policyengine_uk.model_api import Variable, YEAR, Person
from policyengine_uk.data import UKSingleYearDataset

# Path to enhanced dataset
ENHANCED_DATASET_PATH = Path("/Users/janansadeqian/policyengine-uk-data/policyengine_uk_data/storage/enhanced_frs_2023_24.h5")
TEST_YEARS = [2026, 2027, 2028, 2029]

# Global results collector
ALL_RESULTS = []

# OBR projections for comparison
OBR_PROJECTIONS = {
    'Dividends Tax Increase (+2pp)': {
        'description': 'OBR estimate: £1.2bn/year average from 2027-28 (starts April 2026)',
        'years': {
            2026: 1.2,  # Policy starts April 2026 (full year impact assumed)
            2027: 1.2,
            2028: 1.2,
            2029: 1.2,
        }
    },
    'Savings Income Tax Increase (+2pp)': {
        'description': 'OBR estimate: £0.5bn/year average from 2028-29 (starts April 2027)',
        'years': {
            2026: 0.0,  # Not yet implemented
            2027: 0.5,  # Policy starts April 2027 (full year impact assumed)
            2028: 0.5,
            2029: 0.5,
        }
    },
    'Property Income Tax Increase (+2pp)': {
        'description': 'OBR estimate: £0.5bn/year average from 2028-29 (starts April 2027)',
        'years': {
            2026: 0.0,  # Not yet implemented
            2027: 0.5,  # Policy starts April 2027 (full year impact assumed)
            2028: 0.5,
            2029: 0.5,
        }
    },
    'Combined Reforms (All Three)': {
        'description': 'OBR estimate: £2.1bn by 2029-30',
        'years': {
            2026: 1.2,  # Dividends only (starts April 2026)
            2027: 2.2,  # All three (savings + property start April 2027)
            2028: 2.2,  # All three
            2029: 2.1,  # Total expected (slight behavioural adjustment)
        }
    }
}


def create_income_source_tax_reform(
    apply_threshold_freeze: bool = True,
    upper_threshold: float = 80_000,
    rental_base_adj: float = 0.0,
    rental_mid_adj: float = 0.0,
    rental_upper_adj: float = 0.0,
    rental_top_adj: float = 0.0,
    interest_base_adj: float = 0.0,
    interest_mid_adj: float = 0.0,
    interest_upper_adj: float = 0.0,
    interest_top_adj: float = 0.0,
    equity_base_adj: float = 0.0,
    equity_mid_adj: float = 0.0,
    equity_upper_adj: float = 0.0,
    equity_top_adj: float = 0.0,
    wage_base_adj: float = 0.0,
    wage_mid_adj: float = 0.0,
    wage_upper_adj: float = 0.0,
    wage_top_adj: float = 0.0,
    # Year from which each income type's adjustment applies
    rental_start_year: int = 2026,
    interest_start_year: int = 2026,
    equity_start_year: int = 2026,
    wage_start_year: int = 2026,
):
    """
    Create income source-specific tax rate adjustment reform.

    Args:
        apply_threshold_freeze: Whether to freeze thresholds at 2026 levels
        upper_threshold: Custom threshold for new intermediate band
        rental_*_adj: Property income adjustments by band (base/mid/upper/top)
        interest_*_adj: Savings income adjustments by band
        equity_*_adj: Dividend income adjustments by band
        wage_*_adj: Employment/pension income adjustments by band
    """
    param_updates = {}

    if apply_threshold_freeze:
        # Freeze income tax thresholds
        param_updates["gov.hmrc.income_tax.rates.uk[1].threshold"] = {
            "year:2026:10": 37_700
        }
        param_updates["gov.hmrc.income_tax.allowances.personal_allowance.amount"] = {
            "year:2026:10": 12_570
        }
        # Freeze NI thresholds
        param_updates["gov.hmrc.national_insurance.class_1.thresholds.primary_threshold"] = {
            "year:2026:10": 241.73
        }
        param_updates["gov.hmrc.national_insurance.class_1.thresholds.upper_earnings_limit"] = {
            "year:2026:10": 967.73
        }
        param_updates["gov.hmrc.national_insurance.class_4.thresholds.lower_profits_limit"] = {
            "year:2026:10": 12_570
        }
        param_updates["gov.hmrc.national_insurance.class_4.thresholds.upper_profits_limit"] = {
            "year:2026:10": 50_270
        }

    def reform_modifier(simulation):
        """Modify simulation to apply income source-specific tax adjustments."""

        class income_source_tax_adjustment(Variable):
            """Additional tax liability based on income source and marginal rate band."""
            value_type = float
            entity = Person
            label = "Income source-specific tax adjustment"
            definition_period = YEAR
            unit = "currency-GBP"

            def formula(person, period, parameters):
                year = period.start.year
                # Extract income by source
                employment_and_pension = (
                    person("taxable_employment_income", period)
                    + person("taxable_self_employment_income", period)
                    + person("taxable_pension_income", period)
                    + person("state_pension", period)
                )
                rental_receipts = person("taxable_property_income", period)
                interest_receipts = person("taxable_savings_interest_income", period)
                equity_receipts = person("taxable_dividend_income", period)

                # Get tax parameters
                it_structure = parameters.gov.hmrc.income_tax.rates.uk(period)
                allowance = (
                    parameters.gov.hmrc.income_tax.allowances.personal_allowance.amount(period)
                )

                # Helper: extract amount in band range
                extract_band = lambda total, lower, upper: np.minimum(
                    np.maximum(total - lower, 0), np.maximum(upper - lower, 0)
                )

                # Helper: extract amount in band for composite income
                extract_composite_band = (
                    lambda target, preceding, lower, upper: np.maximum(
                        0,
                        extract_band(target + preceding, lower, upper)
                        - extract_band(preceding, lower, upper),
                    )
                )

                # Calculate employment/pension in each band
                wage_in_base = extract_band(
                    employment_and_pension, allowance, it_structure.thresholds[1] + allowance
                )
                wage_in_mid = extract_band(
                    employment_and_pension, it_structure.thresholds[1] + allowance, upper_threshold
                )
                wage_in_upper = extract_band(
                    employment_and_pension, upper_threshold, it_structure.thresholds[2]
                )
                wage_in_top = extract_band(
                    employment_and_pension, it_structure.thresholds[2], np.inf
                )

                # Calculate rental income in each band (stacked after employment)
                rental_in_base = extract_composite_band(
                    rental_receipts,
                    employment_and_pension,
                    allowance,
                    it_structure.thresholds[1] + allowance,
                )
                rental_in_mid = extract_composite_band(
                    rental_receipts,
                    employment_and_pension,
                    it_structure.thresholds[1] + allowance,
                    upper_threshold,
                )
                rental_in_upper = extract_composite_band(
                    rental_receipts,
                    employment_and_pension,
                    upper_threshold,
                    it_structure.thresholds[2],
                )
                rental_in_top = extract_composite_band(
                    rental_receipts,
                    employment_and_pension + rental_in_base + rental_in_mid + rental_in_upper,
                    it_structure.thresholds[2],
                    np.inf,
                )

                # Calculate interest income in each band (stacked after employment + rental)
                interest_in_base = extract_composite_band(
                    interest_receipts,
                    employment_and_pension + rental_receipts,
                    allowance,
                    it_structure.thresholds[1] + allowance,
                )
                interest_in_mid = extract_composite_band(
                    interest_receipts,
                    employment_and_pension + rental_receipts,
                    it_structure.thresholds[1] + allowance,
                    upper_threshold,
                )
                interest_in_upper = extract_composite_band(
                    interest_receipts,
                    employment_and_pension + rental_receipts,
                    upper_threshold,
                    it_structure.thresholds[2],
                )
                interest_in_top = extract_composite_band(
                    interest_receipts,
                    employment_and_pension + rental_receipts + interest_in_base + interest_in_mid + interest_in_upper,
                    it_structure.thresholds[2],
                    np.inf,
                )

                # Calculate equity income in each band (stacked last)
                equity_in_base = extract_composite_band(
                    equity_receipts,
                    employment_and_pension + rental_receipts + interest_receipts,
                    allowance,
                    it_structure.thresholds[1] + allowance,
                )
                equity_in_mid = extract_composite_band(
                    equity_receipts,
                    employment_and_pension + rental_receipts + interest_receipts,
                    it_structure.thresholds[1] + allowance,
                    upper_threshold,
                )
                equity_in_upper = extract_composite_band(
                    equity_receipts,
                    employment_and_pension + rental_receipts + interest_receipts,
                    upper_threshold,
                    it_structure.thresholds[2],
                )
                equity_in_top = extract_composite_band(
                    equity_receipts,
                    employment_and_pension + rental_receipts + interest_receipts
                    + equity_in_base + equity_in_mid + equity_in_upper,
                    it_structure.thresholds[2],
                    np.inf,
                )

                # Calculate total adjustment (only apply from specified start years)
                wage_adjustment = (
                    wage_base_adj * wage_in_base
                    + wage_mid_adj * wage_in_mid
                    + wage_upper_adj * wage_in_upper
                    + wage_top_adj * wage_in_top
                ) if year >= wage_start_year else 0

                rental_adjustment = (
                    rental_base_adj * rental_in_base
                    + rental_mid_adj * rental_in_mid
                    + rental_upper_adj * rental_in_upper
                    + rental_top_adj * rental_in_top
                ) if year >= rental_start_year else 0

                interest_adjustment = (
                    interest_base_adj * interest_in_base
                    + interest_mid_adj * interest_in_mid
                    + interest_upper_adj * interest_in_upper
                    + interest_top_adj * interest_in_top
                ) if year >= interest_start_year else 0

                equity_adjustment = (
                    equity_base_adj * equity_in_base
                    + equity_mid_adj * equity_in_mid
                    + equity_upper_adj * equity_in_upper
                    + equity_top_adj * equity_in_top
                ) if year >= equity_start_year else 0

                return (
                    wage_adjustment
                    + rental_adjustment
                    + interest_adjustment
                    + equity_adjustment
                )

        # Register the new variable
        simulation.tax_benefit_system.update_variable(income_source_tax_adjustment)

        # Add to relevant aggregates
        simulation.tax_benefit_system.variables["hbai_household_net_income"].subtracts.append(
            "income_source_tax_adjustment"
        )
        simulation.tax_benefit_system.variables["post_tax_income"].subtracts.append(
            "income_source_tax_adjustment"
        )
        simulation.tax_benefit_system.variables["gov_balance"].adds.append(
            "income_source_tax_adjustment"
        )

    return Scenario(
        parameter_changes=param_updates,
        simulation_modifier=reform_modifier
    )


def calculate_revenue_impact(baseline_sim, reform_sim, years):
    """Calculate government revenue impact across multiple years."""
    results = []
    for year in years:
        baseline_balance = baseline_sim.calculate("gov_balance", period=year)
        reform_balance = reform_sim.calculate("gov_balance", period=year)
        revenue_gain_bn = (reform_balance - baseline_balance).sum() / 1e9
        results.append({
            "year": year,
            "revenue_bn": revenue_gain_bn
        })
    return results


@pytest.fixture(scope="module")
def baseline_microsim():
    """Load baseline microsimulation once for all tests."""
    dataset = UKSingleYearDataset(file_path=str(ENHANCED_DATASET_PATH))
    return Microsimulation(dataset=dataset)


def test_dividends_tax_increase(baseline_microsim):
    """
    Test dividends tax increase of 2pp across all rates from April 2026.

    Expected yield: £1.2 billion/year average from 2027-28
    """
    reform = create_income_source_tax_reform(
        apply_threshold_freeze=False,
        equity_base_adj=0.02,    # Basic rate: 8.75% → 10.75%
        equity_mid_adj=0.02,     # Higher rate: 33.75% → 35.75%
        equity_top_adj=0.02,     # Additional rate: 39.35% → 41.35%
        equity_start_year=2026,  # Policy starts April 2026
    )

    dataset = UKSingleYearDataset(file_path=str(ENHANCED_DATASET_PATH))
    reform_sim = Microsimulation(dataset=dataset, scenario=reform)

    results = calculate_revenue_impact(baseline_microsim, reform_sim, TEST_YEARS)

    # Print results
    print("\n=== Dividends Tax Increase (+2pp) ===")
    for r in results:
        print(f"Year {r['year']}: £{r['revenue_bn']:.2f}bn")

    # Calculate average for 2027-28 onwards
    avg_2027_onwards = np.mean([r['revenue_bn'] for r in results if r['year'] >= 2027])
    print(f"Average 2027-28 onwards: £{avg_2027_onwards:.2f}bn")

    # Store results
    ALL_RESULTS.append({
        'reform': 'Dividends Tax Increase (+2pp)',
        'results': results,
        'avg_2027_onwards': avg_2027_onwards
    })


def test_savings_tax_increase(baseline_microsim):
    """
    Test savings income tax increase of 2pp across all rates from April 2027.

    Expected yield: £0.5 billion/year average from 2028-29
    """
    reform = create_income_source_tax_reform(
        apply_threshold_freeze=False,
        interest_base_adj=0.02,    # Basic rate: 20% → 22%
        interest_mid_adj=0.02,     # Higher rate: 40% → 42%
        interest_top_adj=0.02,     # Additional rate: 45% → 47%
        interest_start_year=2027,  # Policy starts April 2027
    )

    dataset = UKSingleYearDataset(file_path=str(ENHANCED_DATASET_PATH))
    reform_sim = Microsimulation(dataset=dataset, scenario=reform)

    results = calculate_revenue_impact(baseline_microsim, reform_sim, TEST_YEARS)

    # Print results
    print("\n=== Savings Income Tax Increase (+2pp) ===")
    for r in results:
        print(f"Year {r['year']}: £{r['revenue_bn']:.2f}bn")

    # Calculate average for 2028-29 onwards
    avg_2028_onwards = np.mean([r['revenue_bn'] for r in results if r['year'] >= 2028])
    print(f"Average 2028-29 onwards: £{avg_2028_onwards:.2f}bn")

    # Store results
    ALL_RESULTS.append({
        'reform': 'Savings Income Tax Increase (+2pp)',
        'results': results,
        'avg_2028_onwards': avg_2028_onwards
    })


def test_property_tax_increase(baseline_microsim):
    """
    Test property income tax increase of 2pp across all rates from April 2027.

    Expected yield: £0.5 billion/year average from 2028-29
    """
    reform = create_income_source_tax_reform(
        apply_threshold_freeze=False,
        rental_base_adj=0.02,    # Basic rate: 20% → 22%
        rental_mid_adj=0.02,     # Higher rate: 40% → 42%
        rental_top_adj=0.02,     # Additional rate: 45% → 47%
        rental_start_year=2027,  # Policy starts April 2027
    )

    dataset = UKSingleYearDataset(file_path=str(ENHANCED_DATASET_PATH))
    reform_sim = Microsimulation(dataset=dataset, scenario=reform)

    results = calculate_revenue_impact(baseline_microsim, reform_sim, TEST_YEARS)

    # Print results
    print("\n=== Property Income Tax Increase (+2pp) ===")
    for r in results:
        print(f"Year {r['year']}: £{r['revenue_bn']:.2f}bn")

    # Calculate average for 2028-29 onwards
    avg_2028_onwards = np.mean([r['revenue_bn'] for r in results if r['year'] >= 2028])
    print(f"Average 2028-29 onwards: £{avg_2028_onwards:.2f}bn")

    # Store results
    ALL_RESULTS.append({
        'reform': 'Property Income Tax Increase (+2pp)',
        'results': results,
        'avg_2028_onwards': avg_2028_onwards
    })


def test_combined_reforms(baseline_microsim):
    """
    Test all three reforms combined.

    Expected combined yield: £2.1 billion by 2029-30
    """
    reform = create_income_source_tax_reform(
        apply_threshold_freeze=False,
        # Dividends +2pp (from April 2026)
        equity_base_adj=0.02,
        equity_mid_adj=0.02,
        equity_top_adj=0.02,
        equity_start_year=2026,
        # Savings +2pp (from April 2027)
        interest_base_adj=0.02,
        interest_mid_adj=0.02,
        interest_top_adj=0.02,
        interest_start_year=2027,
        # Property +2pp (from April 2027)
        rental_base_adj=0.02,
        rental_mid_adj=0.02,
        rental_top_adj=0.02,
        rental_start_year=2027,
    )

    dataset = UKSingleYearDataset(file_path=str(ENHANCED_DATASET_PATH))
    reform_sim = Microsimulation(dataset=dataset, scenario=reform)

    results = calculate_revenue_impact(baseline_microsim, reform_sim, TEST_YEARS)

    # Print results
    print("\n=== Combined Reforms ===")
    for r in results:
        print(f"Year {r['year']}: £{r['revenue_bn']:.2f}bn")

    # Check 2029 revenue
    revenue_2029 = [r['revenue_bn'] for r in results if r['year'] == 2029][0]
    print(f"2029-30 revenue: £{revenue_2029:.2f}bn (expected ~£2.1bn)")

    # Store results
    ALL_RESULTS.append({
        'reform': 'Combined Reforms (All Three)',
        'results': results,
        'revenue_2029': revenue_2029
    })


def write_results_to_file(output_path="income_source_tax_reforms_results.txt"):
    """Write all collected results to a text file with OBR comparison."""
    from datetime import datetime

    with open(output_path, 'w') as f:
        f.write("=" * 100 + "\n")
        f.write("INCOME SOURCE-SPECIFIC TAX REFORMS - REVENUE IMPACT ANALYSIS\n")
        f.write("Comparison: PolicyEngine Simulation vs OBR Projections\n")
        f.write("=" * 100 + "\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        for reform_data in ALL_RESULTS:
            reform_name = reform_data['reform']
            f.write("\n" + "=" * 100 + "\n")
            f.write(f"{reform_name}\n")
            f.write("=" * 100 + "\n\n")

            # Get OBR projections for this reform
            obr_data = OBR_PROJECTIONS.get(reform_name, {})
            obr_years = obr_data.get('years', {})
            obr_desc = obr_data.get('description', 'No OBR estimate available')

            f.write(f"OBR Projection: {obr_desc}\n\n")

            # Write side-by-side comparison
            f.write("Revenue Impact by Year (Side-by-Side Comparison):\n")
            f.write("-" * 100 + "\n")
            f.write(f"{'Year':<10} {'Simulation (£bn)':<25} {'OBR Estimate (£bn)':<25} {'Difference (£bn)':<25}\n")
            f.write("-" * 100 + "\n")

            for r in reform_data['results']:
                year = r['year']
                sim_value = r['revenue_bn']
                obr_value = obr_years.get(year)

                sim_str = f"£{sim_value:.2f}bn"
                obr_str = f"£{obr_value:.2f}bn" if obr_value is not None else "N/A"

                if obr_value is not None:
                    diff = sim_value - obr_value
                    # Avoid division by zero for OBR = 0.0
                    if obr_value != 0:
                        diff_str = f"£{diff:+.2f}bn ({diff/obr_value*100:+.1f}%)"
                    else:
                        diff_str = f"£{diff:+.2f}bn (OBR=0)"
                else:
                    diff_str = "N/A"

                f.write(f"{year:<10} {sim_str:<25} {obr_str:<25} {diff_str:<25}\n")

            f.write("-" * 100 + "\n\n")

            # Write summary statistics
            f.write("Summary Statistics:\n")
            f.write("-" * 50 + "\n")

            if 'avg_2027_onwards' in reform_data:
                sim_avg = reform_data['avg_2027_onwards']
                f.write(f"  Simulation average 2027-28 onwards: £{sim_avg:.2f}bn\n")

                # Calculate OBR average for same period
                obr_values = [obr_years.get(y) for y in [2027, 2028, 2029] if obr_years.get(y) is not None]
                if obr_values:
                    obr_avg = np.mean(obr_values)
                    f.write(f"  OBR average 2027-28 onwards: £{obr_avg:.2f}bn\n")
                    f.write(f"  Difference: £{sim_avg - obr_avg:+.2f}bn ({(sim_avg - obr_avg)/obr_avg*100:+.1f}%)\n")

            if 'avg_2028_onwards' in reform_data:
                sim_avg = reform_data['avg_2028_onwards']
                f.write(f"  Simulation average 2028-29 onwards: £{sim_avg:.2f}bn\n")

                # Calculate OBR average for same period
                obr_values = [obr_years.get(y) for y in [2028, 2029] if obr_years.get(y) is not None]
                if obr_values:
                    obr_avg = np.mean(obr_values)
                    f.write(f"  OBR average 2028-29 onwards: £{obr_avg:.2f}bn\n")
                    f.write(f"  Difference: £{sim_avg - obr_avg:+.2f}bn ({(sim_avg - obr_avg)/obr_avg*100:+.1f}%)\n")

            if 'revenue_2029' in reform_data:
                sim_2029 = reform_data['revenue_2029']
                obr_2029 = obr_years.get(2029)
                f.write(f"  Simulation 2029-30: £{sim_2029:.2f}bn\n")
                if obr_2029:
                    f.write(f"  OBR 2029-30: £{obr_2029:.2f}bn\n")
                    f.write(f"  Difference: £{sim_2029 - obr_2029:+.2f}bn ({(sim_2029 - obr_2029)/obr_2029*100:+.1f}%)\n")

        f.write("\n" + "=" * 100 + "\n")
        f.write("END OF REPORT\n")
        f.write("=" * 100 + "\n")

    print(f"\n\n✓ Results saved to {output_path}")


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "-s"])
