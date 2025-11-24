"""
Two-Child Limit Reform Analysis

This script analyzes the impact of removing the two-child benefit limit in the UK.
The reform changes:
- gov.dwp.tax_credits.child_tax_credit.limit.child_count: 102 (effectively unlimited)
- gov.dwp.universal_credit.elements.child.limit.child_count: 100 (effectively unlimited)

Results are saved to a unified CSV file for the dashboard.
"""

import os
import sys

# Add local policyengine-uk to path (for development version with Scenario support)
sys.path.insert(0, '/Users/janansadeqian/policyengine-uk')

import numpy as np
import pandas as pd
from policyengine_uk import Microsimulation, Scenario
from policyengine_uk.data import UKSingleYearDataset

# Configuration
DATASET_PATH = "/Users/janansadeqian/policyengine-uk-data/policyengine_uk_data/storage/enhanced_frs_2023_24.h5"
OUTPUT_CSV = "/Users/janansadeqian/uk-autumn-budget-dashbaord/public/data/reform-results.csv"
REFORM_ID = "two_child_limit"
REFORM_NAME = "2 child limit reforms"

# Years to analyze
YEARS = [2026, 2027, 2028, 2029]

def load_or_create_results_csv(csv_path):
    """Load existing results CSV or create new one with proper structure"""
    if os.path.exists(csv_path):
        return pd.read_csv(csv_path)
    else:
        # Create empty DataFrame with required columns
        return pd.DataFrame(columns=[
            'reform_id',
            'reform_name',
            'metric_type',
            'year',
            'decile',
            'category',
            'value',
            'unit'
        ])

def save_results(df, csv_path):
    """Save results to CSV"""
    # Ensure directory exists
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    df.to_csv(csv_path, index=False)
    print(f"\n✓ Results saved to {csv_path}")

def main():
    print("="*70)
    print("Two-Child Limit Reform Analysis")
    print("="*70)

    # Check if dataset exists
    if not os.path.exists(DATASET_PATH):
        print(f"\n✗ Error: Dataset not found at {DATASET_PATH}")
        print("Please ensure the PolicyEngine UK data is available.")
        sys.exit(1)

    print(f"\n1. Loading dataset from: {DATASET_PATH}")
    dataset = UKSingleYearDataset(file_path=DATASET_PATH)
    print("   ✓ Dataset loaded successfully")

    print("\n2. Setting up reform scenario...")
    print("   Reform parameters:")
    print("   - Child tax credit limit: 102 children (unlimited)")
    print("   - Universal credit child limit: 100 children (unlimited)")

    # Define the reform scenario
    # Set child limit to infinity for all years (removes the 2-child limit)
    scenario = Scenario(
        parameter_changes={
            "gov.dwp.tax_credits.child_tax_credit.limit.child_count": {
                "2026": np.inf,
                "2027": np.inf,
                "2028": np.inf,
                "2029": np.inf
            },
            "gov.dwp.universal_credit.elements.child.limit.child_count": {
                "2026": np.inf,
                "2027": np.inf,
                "2028": np.inf,
                "2029": np.inf
            }
        }
    )

    # Create baseline microsimulation once
    print("\n3. Creating baseline microsimulation...")
    baseline = Microsimulation(dataset=dataset)
    print("   ✓ Baseline created")

    # Calculate budgetary impact over time
    print(f"\n4. Calculating budgetary impact for years {YEARS[0]}-{YEARS[-1]}...")

    # Create reformed microsimulation with the scenario
    print("   Creating reformed microsimulation...")
    reformed = Microsimulation(dataset=dataset, scenario=scenario)
    print("   ✓ Reformed simulation created")

    print("\n   " + "="*60)
    print(f"   {'Year':<10} {'Budgetary Impact':>20}")
    print("   " + "="*60)

    budgetary_results = []
    total_impact = 0

    for year in YEARS:
        baseline_balance = baseline.calculate("gov_balance", period=year)
        reformed_balance = reformed.calculate("gov_balance", period=year)
        difference_balance = reformed_balance - baseline_balance
        year_impact = difference_balance.sum() / 1e9  # Convert to billions
        total_impact += year_impact

        print(f"   {year:<10} £{year_impact:>18,.2f} bn")

        # Store result
        budgetary_results.append({
            'reform_id': REFORM_ID,
            'reform_name': REFORM_NAME,
            'metric_type': 'budgetary_impact',
            'year': year,
            'decile': None,  # Not applicable for budgetary impact
            'category': None,  # Not applicable for budgetary impact
            'value': year_impact,
            'unit': 'GBP_billions'
        })

    print("   " + "="*60)
    print(f"   {'TOTAL':<10} £{total_impact:>18,.2f} bn")
    print(f"   {'AVERAGE':<10} £{total_impact/len(YEARS):>18,.2f} bn/year")
    print("   " + "="*60)

    # Calculate distributional impact by income decile
    # Following official PolicyEngine API approach
    print(f"\n5. Calculating distributional impact by income decile...")
    print("   Analyzing year 2026...")

    # Get household-level data with household weights
    baseline_income = baseline.calculate("household_net_income", period=2026, map_to="household")
    reform_income = reformed.calculate("household_net_income", period=2026, map_to="household")
    household_decile = baseline.calculate("household_income_decile", period=2026, map_to="household")
    household_weight = baseline.calculate("household_weight", period=2026, map_to="household")

    # Calculate income change
    income_change = reform_income - baseline_income

    # Build DataFrame for analysis
    decile_df = pd.DataFrame({
        'household_income_decile': household_decile.values,
        'baseline_income': baseline_income.values,
        'reform_income': reform_income.values,
        'income_change': income_change.values,
        'household_weight': household_weight.values
    })

    # Filter out negative decile values (households with negative income)
    decile_df = decile_df[decile_df['household_income_decile'] >= 1]

    # Calculate relative income change by decile (following official API)
    # rel_income_change = sum(income_change * weight) / sum(baseline_income * weight)
    distributional_results = []

    print("\n   " + "="*60)
    print(f"   {'Decile':<10} {'Relative Change':>20}")
    print("   " + "="*60)

    decile_names = ['1st', '2nd', '3rd', '4th', '5th', '6th', '7th', '8th', '9th', '10th']

    for decile_num in range(1, 11):
        decile_data = decile_df[decile_df['household_income_decile'] == decile_num]

        if len(decile_data) > 0:
            # Calculate weighted sums (matching official API logic)
            weighted_income_change = (decile_data['income_change'] * decile_data['household_weight']).sum()
            weighted_baseline_income = (decile_data['baseline_income'] * decile_data['household_weight']).sum()

            # Relative change: total change / total baseline income
            rel_change = (weighted_income_change / weighted_baseline_income) if weighted_baseline_income > 0 else 0
            pct_change = rel_change * 100  # Convert to percentage

            print(f"   {decile_names[decile_num-1]:<10} {pct_change:>19,.2f}%")

            distributional_results.append({
                'reform_id': REFORM_ID,
                'reform_name': REFORM_NAME,
                'metric_type': 'distributional_impact',
                'year': 2026,
                'decile': decile_names[decile_num-1],
                'category': None,  # Not applicable for distributional impact
                'value': pct_change,
                'unit': 'percent'
            })
        else:
            print(f"   {decile_names[decile_num-1]:<10} {'No data':>20}")

    print("   " + "="*60)

    # Calculate winners and losers by decile (intra-decile impact)
    print(f"\n6. Calculating winners and losers by income decile...")
    print("   Analyzing income change distribution...")

    # Get household count (number of people in household) for population weighting
    household_count_people = baseline.calculate("household_count_people", period=2026, map_to="household")

    # Recalculate income change as percentage
    absolute_change = (reform_income - baseline_income).values
    capped_baseline_income = np.maximum(baseline_income.values, 1)
    capped_reform_income = np.maximum(reform_income.values, 1) + absolute_change
    income_change_pct = (capped_reform_income - capped_baseline_income) / capped_baseline_income

    # Create arrays for analysis
    people = household_count_people.values
    household_weights = household_weight.values
    decile_values = household_decile.values

    # Weighted people count (people * household_weight)
    weighted_people = people * household_weights

    # Define outcome categories
    BOUNDS = [-np.inf, -0.05, -1e-3, 1e-3, 0.05, np.inf]
    LABELS = [
        "Lose more than 5%",
        "Lose less than 5%",
        "No change",
        "Gain less than 5%",
        "Gain more than 5%",
    ]

    winners_losers_results = []

    print("\n   " + "="*70)
    print(f"   {'Decile':<10} {'Gain >5%':>12} {'Gain <5%':>12} {'No change':>12} {'Lose <5%':>12} {'Lose >5%':>12}")
    print("   " + "="*70)

    # Calculate for each decile
    for decile_num in range(1, 11):
        in_decile = decile_values == decile_num
        people_in_decile = weighted_people[in_decile].sum()

        decile_stats = []

        if people_in_decile > 0:
            for lower, upper, label in zip(BOUNDS[:-1], BOUNDS[1:], LABELS):
                # Find people in this decile AND category
                in_category = (income_change_pct > lower) & (income_change_pct <= upper)
                in_both = in_decile & in_category

                people_in_both = weighted_people[in_both].sum()
                percentage = (people_in_both / people_in_decile) * 100

                decile_stats.append(percentage)

                # Store result
                winners_losers_results.append({
                    'reform_id': REFORM_ID,
                    'reform_name': REFORM_NAME,
                    'metric_type': 'winners_losers',
                    'year': 2026,
                    'decile': decile_num,
                    'category': label,
                    'value': percentage,
                    'unit': 'percent'
                })

            # Print in reverse order (gains first)
            print(f"   {decile_num:<10} {decile_stats[4]:>11,.1f}% {decile_stats[3]:>11,.1f}% {decile_stats[2]:>11,.1f}% {decile_stats[1]:>11,.1f}% {decile_stats[0]:>11,.1f}%")
        else:
            print(f"   {decile_num:<10} {'No data':>12}")

    print("   " + "="*70)

    # Calculate overall "All" statistics
    print("\n   Calculating overall (All) statistics...")
    total_people = weighted_people[decile_values >= 1].sum()
    all_stats = []

    if total_people > 0:
        for lower, upper, label in zip(BOUNDS[:-1], BOUNDS[1:], LABELS):
            # Find people in this category (across all deciles)
            in_category = (income_change_pct > lower) & (income_change_pct <= upper) & (decile_values >= 1)
            people_in_category = weighted_people[in_category].sum()
            percentage = (people_in_category / total_people) * 100

            all_stats.append(percentage)

            # Store result with decile = 'All'
            winners_losers_results.append({
                'reform_id': REFORM_ID,
                'reform_name': REFORM_NAME,
                'metric_type': 'winners_losers',
                'year': 2026,
                'decile': 'All',
                'category': label,
                'value': percentage,
                'unit': 'percent'
            })

        # Print in reverse order (gains first)
        print(f"   {'All':<10} {all_stats[4]:>11,.1f}% {all_stats[3]:>11,.1f}% {all_stats[2]:>11,.1f}% {all_stats[1]:>11,.1f}% {all_stats[0]:>11,.1f}%")
        print("   " + "="*70)

    # Calculate additional metrics for 2026
    print("\n7. Calculating additional impact metrics for 2026...")
    additional_results = []

    # 7a. People affected (percentage with income change > 0.01%)
    print("\n   a) Calculating percentage of people affected...")
    income_changed = np.abs(income_change_pct) > 0.0001  # More than 0.01% change
    people_affected = weighted_people[income_changed & (decile_values >= 1)].sum()
    total_people_all = weighted_people[decile_values >= 1].sum()
    percent_affected = (people_affected / total_people_all) * 100 if total_people_all > 0 else 0

    print(f"   People affected: {percent_affected:.1f}%")
    additional_results.append({
        'reform_id': REFORM_ID,
        'reform_name': REFORM_NAME,
        'metric_type': 'people_affected',
        'year': 2026,
        'decile': 'all',
        'category': 'affected',
        'value': percent_affected,
        'unit': 'percent'
    })

    # 7b. Inequality impact (Gini coefficient)
    print("\n   b) Calculating Gini coefficient change...")

    # Calculate Gini using MicroSeries (household level)
    from microdf import MicroSeries
    baseline_hh_income = baseline.calculate("household_net_income", period=2026, map_to="household")
    reformed_hh_income = reformed.calculate("household_net_income", period=2026, map_to="household")
    hh_weight = baseline.calculate("household_weight", period=2026, map_to="household")

    baseline_income_ms = MicroSeries(baseline_hh_income.values, weights=hh_weight.values)
    reformed_income_ms = MicroSeries(reformed_hh_income.values, weights=hh_weight.values)

    baseline_gini = baseline_income_ms.gini()
    reformed_gini = reformed_income_ms.gini()

    gini_change = reformed_gini - baseline_gini
    gini_change_pct = (gini_change / baseline_gini) * 100

    print(f"   Baseline Gini: {baseline_gini:.4f}")
    print(f"   Reformed Gini: {reformed_gini:.4f}")
    print(f"   Change: {gini_change:.4f} ({gini_change_pct:+.2f}%)")

    additional_results.append({
        'reform_id': REFORM_ID,
        'reform_name': REFORM_NAME,
        'metric_type': 'gini_change',
        'year': 2026,
        'decile': 'all',
        'category': 'gini',
        'value': gini_change,  # Store raw coefficient change
        'unit': 'coefficient'
    })

    # 7c. Poverty rate change (absolute BHC - Before Housing Costs)
    print("\n   c) Calculating poverty rate change...")

    # Use WEIGHTED poverty calculation (matching poverty-analysis.ipynb)
    # Get poverty status and person weights
    baseline_in_poverty = baseline.calculate('in_poverty_bhc', period=2026, map_to="person").values
    reformed_in_poverty = reformed.calculate('in_poverty_bhc', period=2026, map_to="person").values
    person_weight_2026 = baseline.calculate('person_weight', period=2026, map_to="person").values

    # Create DataFrame for weighted calculation
    baseline_poverty_df = pd.DataFrame({
        'in_poverty_bhc': baseline_in_poverty,
        'person_weight': person_weight_2026
    })
    reformed_poverty_df = pd.DataFrame({
        'in_poverty_bhc': reformed_in_poverty,
        'person_weight': person_weight_2026
    })

    # Calculate weighted poverty rate: sum(person_weight where in_poverty) / sum(all person_weight)
    baseline_poverty_rate = (
        baseline_poverty_df[baseline_poverty_df['in_poverty_bhc'] == True]['person_weight'].sum() /
        baseline_poverty_df['person_weight'].sum()
    ) * 100

    reformed_poverty_rate = (
        reformed_poverty_df[reformed_poverty_df['in_poverty_bhc'] == True]['person_weight'].sum() /
        reformed_poverty_df['person_weight'].sum()
    ) * 100

    # Calculate both pp and % change
    poverty_rate_change_pp = reformed_poverty_rate - baseline_poverty_rate  # Percentage points
    poverty_rate_change_pct = (poverty_rate_change_pp / baseline_poverty_rate) * 100 if baseline_poverty_rate > 0 else 0  # Percentage

    print(f"   Baseline poverty rate (BHC): {baseline_poverty_rate:.2f}%")
    print(f"   Reformed poverty rate (BHC): {reformed_poverty_rate:.2f}%")
    print(f"   Change: {poverty_rate_change_pp:+.2f}pp ({poverty_rate_change_pct:+.1f}%)")

    # Store percentage point change
    additional_results.append({
        'reform_id': REFORM_ID,
        'reform_name': REFORM_NAME,
        'metric_type': 'poverty_rate_change_pp',
        'year': 2026,
        'decile': 'all',
        'category': 'poverty_bhc',
        'value': poverty_rate_change_pp,  # Store as percentage points (pp)
        'unit': 'percentage_points'
    })

    # Store percentage change
    additional_results.append({
        'reform_id': REFORM_ID,
        'reform_name': REFORM_NAME,
        'metric_type': 'poverty_rate_change_pct',
        'year': 2026,
        'decile': 'all',
        'category': 'poverty_bhc',
        'value': poverty_rate_change_pct,  # Store as percentage change (%)
        'unit': 'percent'
    })

    # Load existing results and update with new data
    print("\n8. Saving results to CSV...")
    results_df = load_or_create_results_csv(OUTPUT_CSV)

    # Remove existing data for this reform (all metric types)
    results_df = results_df[
        ~((results_df['reform_id'] == REFORM_ID) &
          ((results_df['metric_type'] == 'budgetary_impact') |
           (results_df['metric_type'] == 'distributional_impact') |
           (results_df['metric_type'] == 'winners_losers') |
           (results_df['metric_type'] == 'people_affected') |
           (results_df['metric_type'] == 'gini_change') |
           (results_df['metric_type'] == 'poverty_rate_change_pp') |
           (results_df['metric_type'] == 'poverty_rate_change_pct')))
    ]

    # Combine all results
    all_results = budgetary_results + distributional_results + winners_losers_results + additional_results
    new_results_df = pd.DataFrame(all_results)
    results_df = pd.concat([results_df, new_results_df], ignore_index=True)

    # Save to CSV
    save_results(results_df, OUTPUT_CSV)

    print("\n" + "="*70)
    print("Analysis complete!")
    print("="*70)
    print("\nNext steps:")
    print("1. The dashboard will now read these results from the CSV file")
    print("2. Run additional analyses for other metrics (distributional, etc.)")
    print("3. Repeat for other reform scenarios")

if __name__ == "__main__":
    main()
