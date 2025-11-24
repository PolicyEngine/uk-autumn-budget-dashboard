"""
Two-Child Limit Reform Analysis

This script analyzes the impact of removing the two-child benefit limit in the UK.
The reform changes:
- gov.dwp.tax_credits.child_tax_credit.limit.child_count: 102 (effectively unlimited)
- gov.dwp.universal_credit.elements.child.limit.child_count: 100 (effectively unlimited)

Results are saved to CSV files for the dashboard:
- Reform-level metrics: public/data/reform-results.csv
- Constituency-level impacts: public/data/scenario_gains_by_constituency.csv
"""

import os
import sys

# Add local policyengine-uk to path (for development version with Scenario support)
sys.path.insert(0, '/Users/janansadeqian/policyengine-uk')

import numpy as np
import pandas as pd
import copy
import h5py
from policyengine_uk import Microsimulation, Scenario, Simulation
from policyengine_uk.data import UKSingleYearDataset
from microdf import MicroSeries

# Configuration
DATASET_PATH = "/Users/janansadeqian/policyengine-uk-data/policyengine_uk_data/storage/enhanced_frs_2023_24.h5"
OUTPUT_CSV = "/Users/janansadeqian/uk-autumn-budget-dashbaord/public/data/reform-results.csv"
CONSTITUENCY_CSV = "/Users/janansadeqian/uk-autumn-budget-dashbaord/public/data/scenario_gains_by_constituency.csv"
CONSTITUENCY_WEIGHTS_PATH = "/Users/janansadeqian/uk-autumn-budget-dashbaord/data/parliamentary_constituency_weights.h5"
REFORM_ID = "two_child_limit"
REFORM_NAME = "2 child limit reforms"
SCENARIO_ID = "remove_2_child_limit"

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
            'unit',
            'employment_income',  # Optional: for income_curve metric
            'household_weight'  # Optional: for household_scatter metric
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

    # Calculate average absolute income change by decile
    # Use the same DataFrame approach as distributional impact
    winners_losers_results = []

    print("\n   " + "="*70)
    print(f"   {'Decile':<10} {'Average change (£)':>20}")
    print("   " + "="*70)

    # Calculate for each decile using the same pattern as distributional impact
    for decile_num in range(1, 11):
        decile_data = decile_df[decile_df['household_income_decile'] == decile_num]

        if len(decile_data) > 0:
            # Calculate weighted income change (same as distributional section)
            weighted_income_change = (decile_data['income_change'] * decile_data['household_weight']).sum()
            total_households = decile_data['household_weight'].sum()

            # Average change per household
            avg_change = weighted_income_change / total_households if total_households > 0 else 0

            # Store result
            winners_losers_results.append({
                'reform_id': REFORM_ID,
                'reform_name': REFORM_NAME,
                'metric_type': 'winners_losers',
                'year': 2026,
                'decile': str(decile_num),
                'category': 'avg_change',
                'value': avg_change,
                'unit': 'gbp'
            })

            print(f"   {decile_num:<10} £{avg_change:>18,.2f}")
        else:
            print(f"   {decile_num:<10} {'No data':>20}")

    print("   " + "="*70)

    # Calculate overall average (all deciles)
    print("\n   Calculating overall average...")

    # Use entire DataFrame for overall calculation
    overall_weighted_income_change = (decile_df['income_change'] * decile_df['household_weight']).sum()
    overall_total_households = decile_df['household_weight'].sum()
    overall_avg_change = overall_weighted_income_change / overall_total_households if overall_total_households > 0 else 0

    winners_losers_results.append({
        'reform_id': REFORM_ID,
        'reform_name': REFORM_NAME,
        'metric_type': 'winners_losers',
        'year': 2026,
        'decile': 'all',
        'category': 'avg_change',
        'value': overall_avg_change,
        'unit': 'gbp'
    })

    print(f"   {'All':<10} £{overall_avg_change:>18,.2f}")
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
    # Use equivalised household income with household count weighting (official method)
    baseline_equiv_income = baseline.calculate("equiv_household_net_income", period=2026, map_to="household")
    reformed_equiv_income = reformed.calculate("equiv_household_net_income", period=2026, map_to="household")
    household_count = baseline.calculate("household_count_people", period=2026, map_to="household")
    hh_weight = baseline.calculate("household_weight", period=2026, map_to="household")

    # Set negative incomes to zero
    baseline_equiv_income_values = np.maximum(baseline_equiv_income.values, 0)
    reformed_equiv_income_values = np.maximum(reformed_equiv_income.values, 0)

    # Weight by household count people
    adjusted_weights = hh_weight.values * household_count.values

    baseline_income_ms = MicroSeries(baseline_equiv_income_values, weights=adjusted_weights)
    reformed_income_ms = MicroSeries(reformed_equiv_income_values, weights=adjusted_weights)

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
        'value': gini_change_pct / 100,  # Store as decimal (e.g., -0.52% = -0.0052)
        'unit': 'relative_change'
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

    # 7d. Employment income to net income curve
    print("\n   d) Calculating employment income to net income curve...")

    # Define reform dict for Simulation API
    reform_dict = {
        "gov.dwp.tax_credits.child_tax_credit.limit.child_count": {
            "2025-01-01.2100-12-31": 102
        },
        "gov.dwp.universal_credit.elements.child.limit.child_count": {
            "2025-01-01.2100-12-31": 100
        }
    }

    # Base situation: Family with 3 children (affected by two-child limit)
    base_situation = {
        "people": {
            "you": {
                "age": {"2026": 40},
                "employment_income": {"2026": 0}  # Will vary this
            },
            "your partner": {
                "age": {"2026": 40},
                "employment_income": {"2026": 0}
            },
            "your first child": {
                "age": {"2026": 7},
                "employment_income": {"2026": 0}
            },
            "your second child": {
                "age": {"2026": 5},
                "employment_income": {"2026": 0}
            },
            "your third child": {
                "age": {"2026": 3},
                "employment_income": {"2026": 0}
            }
        },
        "benunits": {
            "your immediate family": {
                "members": [
                    "you",
                    "your partner",
                    "your first child",
                    "your second child",
                    "your third child"
                ],
                "would_claim_uc": {"2026": True}
            }
        },
        "households": {
            "your household": {
                "brma": {"2026": "MAIDSTONE"},
                "region": {"2026": "LONDON"},
                "members": [
                    "you",
                    "your partner",
                    "your first child",
                    "your second child",
                    "your third child"
                ],
                "local_authority": {"2026": "MAIDSTONE"}
            }
        }
    }

    # Employment income range: £0 to £200,000 with 30 points
    employment_incomes = np.linspace(0, 200_000, 30)
    income_curve_results = []

    print(f"   Calculating {len(employment_incomes)} income points from £0 to £200,000...")

    for emp_income in employment_incomes:
        # Update employment income for household head
        situation = copy.deepcopy(base_situation)
        situation["people"]["you"]["employment_income"]["2026"] = float(emp_income)

        # Baseline simulation (no reform)
        baseline_sim_pe = Simulation(situation=situation)
        baseline_net_income = baseline_sim_pe.calculate("household_net_income", 2026)[0]

        # Reform simulation
        reform_sim_pe = Simulation(reform=reform_dict, situation=situation)
        reform_net_income = reform_sim_pe.calculate("household_net_income", 2026)[0]

        # Store baseline result
        income_curve_results.append({
            'reform_id': REFORM_ID,
            'reform_name': REFORM_NAME,
            'metric_type': 'income_curve',
            'year': 2026,
            'decile': None,
            'category': 'baseline',
            'value': baseline_net_income,
            'unit': 'GBP',
            'employment_income': emp_income  # Extra field for reference
        })

        # Store reform result
        income_curve_results.append({
            'reform_id': REFORM_ID,
            'reform_name': REFORM_NAME,
            'metric_type': 'income_curve',
            'year': 2026,
            'decile': None,
            'category': 'reform',
            'value': reform_net_income,
            'unit': 'GBP',
            'employment_income': emp_income  # Extra field for reference
        })

    print(f"   ✓ Income curve calculated for {len(employment_incomes)} employment income levels")

    # Calculate maximum benefit
    baseline_values = [r['value'] for r in income_curve_results if r['category'] == 'baseline']
    reform_values = [r['value'] for r in income_curve_results if r['category'] == 'reform']
    benefits = [reform_values[i] - baseline_values[i] for i in range(len(baseline_values))]
    max_benefit = max(benefits)
    print(f"   Maximum household benefit: £{max_benefit:,.0f}")

    # 7e. Household income change scatter data
    print("\n   e) Generating household scatter plot data...")

    # Calculate income change for all households
    hh_baseline_income = baseline_income.values  # Already calculated in section 5
    hh_reform_income = reform_income.values
    hh_income_change = hh_reform_income - hh_baseline_income
    hh_weight = household_weight.values

    # Filter to households with baseline income 0-150k for better visualization
    mask = (hh_baseline_income >= 0) & (hh_baseline_income <= 150000)

    scatter_results = []
    for i in range(len(hh_baseline_income)):
        if mask[i]:
            scatter_results.append({
                'reform_id': REFORM_ID,
                'reform_name': REFORM_NAME,
                'metric_type': 'household_scatter',
                'year': 2026,
                'decile': None,
                'category': None,
                'value': hh_baseline_income[i],  # Y-axis: baseline income
                'unit': 'GBP',
                'employment_income': hh_income_change[i],  # X-axis: income change (reusing this field)
                'household_weight': hh_weight[i]  # For dot size
            })

    print(f"   ✓ Generated scatter data for {len(scatter_results):,} households")

    # Calculate constituency-level impacts
    print("\n8. Calculating constituency-level impacts...")

    # Check if constituency weights file exists
    if not os.path.exists(CONSTITUENCY_WEIGHTS_PATH):
        print(f"   ✗ Warning: Constituency weights file not found at {CONSTITUENCY_WEIGHTS_PATH}")
        print("   Skipping constituency analysis...")
        constituency_results = []
    else:
        print(f"   Loading constituency weights from: {CONSTITUENCY_WEIGHTS_PATH}")

        try:
            # Load constituency weights
            with h5py.File(CONSTITUENCY_WEIGHTS_PATH, "r") as f:
                weights = f["2025"][...]  # Shape: (650 constituencies, ~100k households)
            print(f"   ✓ Loaded weights for {weights.shape[0]} constituencies")

            # Download constituency metadata (names and codes)
            from policyengine_core.tools.hugging_face import download_huggingface_dataset

            try:
                constituency_names_path = download_huggingface_dataset(
                    repo="policyengine/policyengine-uk-data-public",
                    repo_filename="constituencies_2024.csv",
                )
                constituency_df = pd.read_csv(constituency_names_path)
                print(f"   ✓ Loaded metadata for {len(constituency_df)} constituencies")

                # Calculate household net income for baseline and reform (year 2026)
                baseline_hnet = baseline_income.values  # Already calculated in section 5
                reform_hnet = reform_income.values

                # Calculate impact for each constituency
                constituency_results = []

                print(f"   Calculating impacts for {len(constituency_df)} constituencies...")

                for i in range(len(constituency_df)):
                    name = constituency_df.iloc[i]["name"]
                    code = constituency_df.iloc[i]["code"]
                    weight = weights[i]

                    # Calculate weighted income using MicroSeries
                    baseline_income_const = MicroSeries(baseline_hnet, weights=weight)
                    reform_income_const = MicroSeries(reform_hnet, weights=weight)

                    # Average household income change (absolute)
                    avg_change = (reform_income_const.sum() - baseline_income_const.sum()) / baseline_income_const.count()

                    # Average household baseline income
                    avg_baseline_income = baseline_income_const.sum() / baseline_income_const.count()

                    # Relative change (percentage) - gain relative to constituency's average income
                    rel_change = (avg_change / avg_baseline_income) * 100 if avg_baseline_income > 0 else 0

                    # Store in dashboard format
                    constituency_results.append({
                        "scenario": SCENARIO_ID,
                        "constituency_code": code,
                        "constituency_name": name,
                        "average_gain": avg_change,
                        "relative_change": rel_change,
                    })

                print(f"   ✓ Calculated impacts for {len(constituency_results)} constituencies")

                # Calculate summary statistics
                constituency_results_df = pd.DataFrame(constituency_results)
                print(f"\n   Summary statistics:")
                print(f"   Mean gain: £{constituency_results_df['average_gain'].mean():,.2f}")
                print(f"   Median gain: £{constituency_results_df['average_gain'].median():,.2f}")
                print(f"   Min gain: £{constituency_results_df['average_gain'].min():,.2f}")
                print(f"   Max gain: £{constituency_results_df['average_gain'].max():,.2f}")

            except Exception as e:
                print(f"   ✗ Error loading constituency metadata: {e}")
                print("   Skipping constituency analysis...")
                constituency_results = []

        except Exception as e:
            print(f"   ✗ Error loading constituency weights: {e}")
            print("   Skipping constituency analysis...")
            constituency_results = []

    # Save constituency results to separate CSV
    if constituency_results:
        print("\n9. Saving constituency results to CSV...")

        # Load existing constituency data if file exists
        if os.path.exists(CONSTITUENCY_CSV):
            print(f"   Loading existing data from {CONSTITUENCY_CSV}")
            existing_const_df = pd.read_csv(CONSTITUENCY_CSV)
            # Remove existing data for this scenario
            existing_const_df = existing_const_df[existing_const_df['scenario'] != SCENARIO_ID]
            print(f"   Removed existing '{SCENARIO_ID}' data")
            # Combine with new data
            combined_const_df = pd.concat([existing_const_df, pd.DataFrame(constituency_results)], ignore_index=True)
        else:
            print(f"   Creating new file at {CONSTITUENCY_CSV}")
            combined_const_df = pd.DataFrame(constituency_results)

        # Ensure only required columns in correct order
        combined_const_df = combined_const_df[['scenario', 'constituency_code', 'constituency_name', 'average_gain', 'relative_change']]

        # Save to CSV
        os.makedirs(os.path.dirname(CONSTITUENCY_CSV), exist_ok=True)
        combined_const_df.to_csv(CONSTITUENCY_CSV, index=False)
        print(f"   ✓ Saved {len(constituency_results)} constituency records for scenario '{SCENARIO_ID}'")
        print(f"   ✓ Total records in file: {len(combined_const_df)}")

    # Load existing results and update with new data
    print(f"\n{10 if constituency_results else 9}. Saving reform results to CSV...")
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
           (results_df['metric_type'] == 'poverty_rate_change_pct') |
           (results_df['metric_type'] == 'income_curve') |
           (results_df['metric_type'] == 'household_scatter')))
    ]

    # Combine all results
    all_results = budgetary_results + distributional_results + winners_losers_results + additional_results + income_curve_results + scatter_results
    new_results_df = pd.DataFrame(all_results)
    results_df = pd.concat([results_df, new_results_df], ignore_index=True)

    # Save to CSV
    save_results(results_df, OUTPUT_CSV)

    print("\n" + "="*70)
    print("Analysis complete!")
    print("="*70)
    print("\nResults saved:")
    print(f"1. Reform metrics: {OUTPUT_CSV}")
    if constituency_results:
        print(f"2. Constituency impacts: {CONSTITUENCY_CSV}")
    print("\nThe dashboard will automatically read these results.")

if __name__ == "__main__":
    main()
