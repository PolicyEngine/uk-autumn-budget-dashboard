"""
Dashboard data generator.

Takes a list of ScenarioConfig objects and generates all metrics for the dashboard.
"""

import os
from pathlib import Path
from typing import Any

import h5py
import numpy as np
import pandas as pd
from microdf import MicroSeries
from policyengine_uk import Microsimulation, Scenario, Simulation
from policyengine_uk.model_api import Variable, YEAR, Household
from pydantic import BaseModel
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

DATA_INPUTS = Path("./data_inputs")
DATA_DIR = Path("./data")
OUTPUT_DIR = Path("./public/data")
YEARS = [2026, 2027, 2028, 2029]


class ScenarioConfig(BaseModel):
    """Configuration for a single reform scenario."""

    id: str
    name: str
    scenario: Any  # Scenario object (can't be validated by pydantic)

    class Config:
        arbitrary_types_allowed = True


def check_input_data() -> None:
    """Check that required input files exist locally."""
    weights_path = DATA_DIR / "parliamentary_constituency_weights.h5"
    constituencies_path = DATA_INPUTS / "constituencies_2024.csv"

    if not weights_path.exists():
        console.print(f"[red]Error: {weights_path} not found[/red]")
        raise FileNotFoundError(f"Required file not found: {weights_path}")

    if not constituencies_path.exists():
        console.print(f"[red]Error: {constituencies_path} not found[/red]")
        raise FileNotFoundError(f"Required file not found: {constituencies_path}")

    console.print("[green]✓[/green] Found required constituency data files")


def save_csv(df: pd.DataFrame, csv_path: Path) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(csv_path, index=False)


def calculate_budgetary_impact(
    baseline: Microsimulation,
    reformed: Microsimulation,
    reform_id: str,
    reform_name: str,
) -> list[dict]:
    results = []
    for year in YEARS:
        baseline_balance = baseline.calculate("gov_balance", period=year)
        reformed_balance = reformed.calculate("gov_balance", period=year)
        impact = (reformed_balance - baseline_balance).sum() / 1e9
        results.append({
            "reform_id": reform_id,
            "reform_name": reform_name,
            "year": year,
            "value": impact,
        })
    return results


def calculate_distributional_impact(
    baseline: Microsimulation,
    reformed: Microsimulation,
    reform_id: str,
    reform_name: str,
    year: int = 2026,
) -> tuple[list[dict], pd.DataFrame]:
    baseline_income = baseline.calculate("household_net_income", period=year, map_to="household")
    reform_income = reformed.calculate("household_net_income", period=year, map_to="household")
    household_decile = baseline.calculate("household_income_decile", period=year, map_to="household")
    household_weight = baseline.calculate("household_weight", period=year, map_to="household")

    decile_df = pd.DataFrame({
        "household_income_decile": household_decile.values,
        "baseline_income": baseline_income.values,
        "reform_income": reform_income.values,
        "income_change": (reform_income - baseline_income).values,
        "household_weight": household_weight.values,
    })
    decile_df = decile_df[decile_df["household_income_decile"] >= 1]

    decile_names = ["1st", "2nd", "3rd", "4th", "5th", "6th", "7th", "8th", "9th", "10th"]
    results = []

    for decile_num in range(1, 11):
        decile_data = decile_df[decile_df["household_income_decile"] == decile_num]
        if len(decile_data) > 0:
            weighted_change = (decile_data["income_change"] * decile_data["household_weight"]).sum()
            weighted_baseline = (decile_data["baseline_income"] * decile_data["household_weight"]).sum()
            rel_change = (weighted_change / weighted_baseline) * 100 if weighted_baseline > 0 else 0
            results.append({
                "reform_id": reform_id,
                "reform_name": reform_name,
                "year": year,
                "decile": decile_names[decile_num - 1],
                "value": rel_change,
            })

    return results, decile_df


def calculate_winners_losers(
    decile_df: pd.DataFrame,
    reform_id: str,
    reform_name: str,
    year: int = 2026,
) -> list[dict]:
    results = []

    for decile_num in range(1, 11):
        decile_data = decile_df[decile_df["household_income_decile"] == decile_num]
        if len(decile_data) > 0:
            weighted_change = (decile_data["income_change"] * decile_data["household_weight"]).sum()
            total_hh = decile_data["household_weight"].sum()
            avg_change = weighted_change / total_hh if total_hh > 0 else 0
            results.append({
                "reform_id": reform_id,
                "reform_name": reform_name,
                "year": year,
                "decile": str(decile_num),
                "avg_change": avg_change,
            })

    overall_weighted = (decile_df["income_change"] * decile_df["household_weight"]).sum()
    overall_hh = decile_df["household_weight"].sum()
    overall_avg = overall_weighted / overall_hh if overall_hh > 0 else 0
    results.append({
        "reform_id": reform_id,
        "reform_name": reform_name,
        "year": year,
        "decile": "all",
        "avg_change": overall_avg,
    })

    return results


def calculate_metrics(
    baseline: Microsimulation,
    reformed: Microsimulation,
    reform_id: str,
    reform_name: str,
    year: int = 2026,
) -> list[dict]:
    results = []

    baseline_income = baseline.calculate("household_net_income", period=year, map_to="household")
    reform_income = reformed.calculate("household_net_income", period=year, map_to="household")
    household_decile = baseline.calculate("household_income_decile", period=year, map_to="household")
    household_count = baseline.calculate("household_count_people", period=year, map_to="household")
    household_weight = baseline.calculate("household_weight", period=year, map_to="household")

    income_change = reform_income - baseline_income
    capped_baseline = np.maximum(baseline_income.values, 1)
    income_change_pct = income_change.values / capped_baseline

    weighted_people = household_count.values * household_weight.values
    income_changed = np.abs(income_change_pct) > 0.0001
    valid_deciles = household_decile.values >= 1

    people_affected = weighted_people[income_changed & valid_deciles].sum()
    total_people = weighted_people[valid_deciles].sum()
    percent_affected = (people_affected / total_people) * 100 if total_people > 0 else 0

    baseline_equiv = baseline.calculate("equiv_household_net_income", period=year, map_to="household")
    reformed_equiv = reformed.calculate("equiv_household_net_income", period=year, map_to="household")
    hh_count = baseline.calculate("household_count_people", period=year, map_to="household")
    hh_weight = baseline.calculate("household_weight", period=year, map_to="household")

    baseline_equiv_values = np.maximum(baseline_equiv.values, 0)
    reformed_equiv_values = np.maximum(reformed_equiv.values, 0)
    adjusted_weights = hh_weight.values * hh_count.values

    baseline_gini = MicroSeries(baseline_equiv_values, weights=adjusted_weights).gini()
    reformed_gini = MicroSeries(reformed_equiv_values, weights=adjusted_weights).gini()
    gini_change = (reformed_gini - baseline_gini) / baseline_gini

    baseline_poverty = baseline.calculate("in_poverty_bhc", period=year, map_to="person").values
    reformed_poverty = reformed.calculate("in_poverty_bhc", period=year, map_to="person").values
    person_weight = baseline.calculate("person_weight", period=year, map_to="person").values

    baseline_rate = (person_weight[baseline_poverty].sum() / person_weight.sum()) * 100
    reformed_rate = (person_weight[reformed_poverty].sum() / person_weight.sum()) * 100

    poverty_pp = reformed_rate - baseline_rate
    poverty_pct = (poverty_pp / baseline_rate) * 100 if baseline_rate > 0 else 0

    results.append({
        "reform_id": reform_id,
        "reform_name": reform_name,
        "year": year,
        "people_affected": percent_affected,
        "gini_change": gini_change,
        "poverty_change_pp": poverty_pp,
        "poverty_change_pct": poverty_pct,
    })

    return results


def calculate_income_curve(
    scenario: Scenario,
    reform_id: str,
    reform_name: str,
    year: int = 2026,
) -> list[dict]:
    base_situation = {
        "people": {
            "adult1": {"age": {str(year): 40}, "employment_income": {str(year): 0}},
            "adult2": {"age": {str(year): 40}, "employment_income": {str(year): 0}},
            "child1": {"age": {str(year): 7}, "employment_income": {str(year): 0}},
            "child2": {"age": {str(year): 5}, "employment_income": {str(year): 0}},
            "child3": {"age": {str(year): 3}, "employment_income": {str(year): 0}},
        },
        "benunits": {
            "family": {
                "members": ["adult1", "adult2", "child1", "child2", "child3"],
                "would_claim_uc": {str(year): True},
            }
        },
        "households": {
            "household": {
                "brma": {str(year): "MAIDSTONE"},
                "region": {str(year): "LONDON"},
                "members": ["adult1", "adult2", "child1", "child2", "child3"],
                "local_authority": {str(year): "MAIDSTONE"},
            }
        },
        "axes": [[
            {"name": "employment_income", "min": 0, "max": 100_000, "count": 501, "period": str(year)},
        ]]
    }

    baseline_sim = Simulation(situation=base_situation)
    reform_sim = Simulation(scenario=scenario, situation=base_situation)
    employment_incomes = baseline_sim.calculate("employment_income", year, map_to="household")
    baseline_hnet = baseline_sim.calculate("household_net_income", year)
    reform_hnet = reform_sim.calculate("household_net_income", year)
    results = []

    for i in range(len(employment_incomes)):
        results.append({
            "reform_id": reform_id,
            "reform_name": reform_name,
            "year": year,
            "employment_income": employment_incomes[i],
            "baseline_net_income": baseline_hnet[i],
            "reform_net_income": reform_hnet[i],
        })

    return results


def calculate_household_scatter(
    baseline: Microsimulation,
    reformed: Microsimulation,
    reform_id: str,
    reform_name: str,
    year: int = 2026,
) -> list[dict]:
    baseline_income = baseline.calculate("household_net_income", period=year, map_to="household")
    reform_income = reformed.calculate("household_net_income", period=year, map_to="household")
    household_weight = baseline.calculate("household_weight", period=year, map_to="household")

    income_change = (reform_income - baseline_income).values
    baseline_values = baseline_income.values
    weights = household_weight.values

    mask = (baseline_values >= 0) & (baseline_values <= 150000)
    results = []

    for i in range(len(baseline_values)):
        if mask[i]:
            results.append({
                "reform_id": reform_id,
                "reform_name": reform_name,
                "year": year,
                "baseline_income": baseline_values[i],
                "income_change": income_change[i],
                "household_weight": weights[i],
            })

    return results


def calculate_constituency_impacts(
    baseline: Microsimulation,
    reformed: Microsimulation,
    reform_id: str,
    year: int = 2026,
) -> list[dict]:
    weights_path = DATA_DIR / "parliamentary_constituency_weights.h5"
    constituencies_path = DATA_INPUTS / "constituencies_2024.csv"

    if not weights_path.exists() or not constituencies_path.exists():
        console.print("[yellow]Constituency data not found in data_inputs/[/yellow]")
        return []

    try:
        with h5py.File(weights_path, "r") as f:
            weights = f["2025"][...]

        constituency_df = pd.read_csv(constituencies_path)

        baseline_income = baseline.calculate("household_net_income", period=year, map_to="household").values
        reform_income = reformed.calculate("household_net_income", period=year, map_to="household").values

        results = []
        for i in range(len(constituency_df)):
            name = constituency_df.iloc[i]["name"]
            code = constituency_df.iloc[i]["code"]
            weight = weights[i]

            baseline_ms = MicroSeries(baseline_income, weights=weight)
            reform_ms = MicroSeries(reform_income, weights=weight)

            avg_change = (reform_ms.sum() - baseline_ms.sum()) / baseline_ms.count()
            avg_baseline = baseline_ms.sum() / baseline_ms.count()
            rel_change = (avg_change / avg_baseline) * 100 if avg_baseline > 0 else 0

            results.append({
                "reform_id": reform_id,
                "year": year,
                "constituency_code": code,
                "constituency_name": name,
                "average_gain": avg_change,
                "relative_change": rel_change,
            })

        return results

    except Exception as e:
        console.print(f"[red]Error calculating constituency impacts: {e}[/red]")
        return []


def calculate_demographic_constituency_impacts(
    baseline: Microsimulation,
    reformed: Microsimulation,
    reform_id: str,
    year: int = 2026,
) -> list[dict]:
    """Calculate impacts by children count, marital status, and constituency."""
    weights_path = DATA_DIR / "parliamentary_constituency_weights.h5"
    constituencies_path = DATA_INPUTS / "constituencies_2024.csv"

    if not weights_path.exists() or not constituencies_path.exists():
        console.print("[yellow]Constituency data not found in data_inputs/[/yellow]")
        return []

    try:
        with h5py.File(weights_path, "r") as f:
            constituency_weights = f["2025"][...]

        constituency_df = pd.read_csv(constituencies_path)

        baseline_income = baseline.calculate("household_net_income", period=year, map_to="household").values
        reform_income = reformed.calculate("household_net_income", period=year, map_to="household").values
        income_change = reform_income - baseline_income

        # Get household characteristics
        num_children = baseline.calculate("num_children", period=year, map_to="household").values
        is_married = baseline.calculate("is_married", period=year, map_to="household").values

        # Cap children at 4+
        num_children_capped = np.minimum(num_children, 4).astype(int)

        results = []

        for const_idx in range(len(constituency_df)):
            name = constituency_df.iloc[const_idx]["name"]
            code = constituency_df.iloc[const_idx]["code"]
            weights = constituency_weights[const_idx]

            for n_children in range(5):  # 0, 1, 2, 3, 4+
                for married in [True, False]:
                    mask = (num_children_capped == n_children) & (is_married == married)

                    if mask.sum() == 0:
                        continue

                    masked_weights = weights * mask
                    total_weight = masked_weights.sum()

                    if total_weight == 0:
                        continue

                    avg_change = (income_change * masked_weights).sum() / total_weight
                    avg_baseline = (baseline_income * masked_weights).sum() / total_weight
                    rel_change = (avg_change / avg_baseline) * 100 if avg_baseline > 0 else 0

                    results.append({
                        "reform_id": reform_id,
                        "year": year,
                        "constituency_code": code,
                        "constituency_name": name,
                        "num_children": f"{n_children}+" if n_children == 4 else str(n_children),
                        "is_married": married,
                        "average_gain": avg_change,
                        "relative_change": rel_change,
                        "household_count": total_weight,
                    })

        return results

    except Exception as e:
        console.print(f"[red]Error calculating demographic constituency impacts: {e}[/red]")
        return []


class ScenarioResults(BaseModel):
    """Results from processing a scenario."""

    budgetary_impact: list[dict]
    distributional_impact: list[dict]
    winners_losers: list[dict]
    metrics: list[dict]
    income_curve: list[dict]
    household_scatter: list[dict]
    constituency: list[dict]
    demographic_constituency: list[dict]

    class Config:
        arbitrary_types_allowed = True


def process_scenario(config: ScenarioConfig) -> ScenarioResults:
    baseline = Microsimulation()
    reformed = Microsimulation(scenario=config.scenario)

    # Calculate budgetary impact across all years
    budgetary = calculate_budgetary_impact(baseline, reformed, config.id, config.name)

    # Calculate distributional data, metrics, etc. for each year
    all_distributional = []
    all_winners_losers = []
    all_metrics = []
    all_income_curve = []
    all_household_scatter = []
    all_constituency = []
    all_demographic_constituency = []

    for year in YEARS:
        distributional, decile_df = calculate_distributional_impact(baseline, reformed, config.id, config.name, year)
        winners_losers = calculate_winners_losers(decile_df, config.id, config.name, year)
        metrics = calculate_metrics(baseline, reformed, config.id, config.name, year)
        income_curve = calculate_income_curve(config.scenario, config.id, config.name, year)
        household_scatter = calculate_household_scatter(baseline, reformed, config.id, config.name, year)
        constituency = calculate_constituency_impacts(baseline, reformed, config.id, year=year)
        demographic_constituency = calculate_demographic_constituency_impacts(baseline, reformed, config.id, year=year)

        all_distributional.extend(distributional)
        all_winners_losers.extend(winners_losers)
        all_metrics.extend(metrics)
        all_income_curve.extend(income_curve)
        all_household_scatter.extend(household_scatter)
        all_constituency.extend(constituency)
        all_demographic_constituency.extend(demographic_constituency)

    return ScenarioResults(
        budgetary_impact=budgetary,
        distributional_impact=all_distributional,
        winners_losers=all_winners_losers,
        metrics=all_metrics,
        income_curve=all_income_curve,
        household_scatter=all_household_scatter,
        constituency=all_constituency,
        demographic_constituency=all_demographic_constituency,
    )


def run(scenarios: list[ScenarioConfig]) -> None:
    check_input_data()

    # Start with empty dataframes
    budgetary_df = pd.DataFrame()
    distributional_df = pd.DataFrame()
    winners_losers_df = pd.DataFrame()
    metrics_df = pd.DataFrame()
    income_curve_df = pd.DataFrame()
    household_scatter_df = pd.DataFrame()
    constituency_df = pd.DataFrame()
    demographic_constituency_df = pd.DataFrame()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        for config in scenarios:
            task = progress.add_task(f"Processing {config.name}...", total=None)

            results = process_scenario(config)

            budgetary_df = pd.concat([budgetary_df, pd.DataFrame(results.budgetary_impact)], ignore_index=True)
            distributional_df = pd.concat([distributional_df, pd.DataFrame(results.distributional_impact)], ignore_index=True)
            winners_losers_df = pd.concat([winners_losers_df, pd.DataFrame(results.winners_losers)], ignore_index=True)
            metrics_df = pd.concat([metrics_df, pd.DataFrame(results.metrics)], ignore_index=True)
            income_curve_df = pd.concat([income_curve_df, pd.DataFrame(results.income_curve)], ignore_index=True)
            household_scatter_df = pd.concat([household_scatter_df, pd.DataFrame(results.household_scatter)], ignore_index=True)
            if results.constituency:
                constituency_df = pd.concat([constituency_df, pd.DataFrame(results.constituency)], ignore_index=True)
            if results.demographic_constituency:
                demographic_constituency_df = pd.concat([demographic_constituency_df, pd.DataFrame(results.demographic_constituency)], ignore_index=True)

            progress.remove_task(task)
            console.print(f"[green]✓[/green] {config.name}")

    # Save all CSVs
    save_csv(budgetary_df, OUTPUT_DIR / "budgetary_impact.csv")
    save_csv(distributional_df, OUTPUT_DIR / "distributional_impact.csv")
    save_csv(winners_losers_df, OUTPUT_DIR / "winners_losers.csv")
    save_csv(metrics_df, OUTPUT_DIR / "metrics.csv")
    save_csv(income_curve_df, OUTPUT_DIR / "income_curve.csv")
    save_csv(household_scatter_df, OUTPUT_DIR / "household_scatter.csv")
    if len(constituency_df) > 0:
        save_csv(constituency_df, OUTPUT_DIR / "constituency.csv")
    if len(demographic_constituency_df) > 0:
        save_csv(demographic_constituency_df, OUTPUT_DIR / "demographic_constituency.csv")

    console.print(f"Saved results to {OUTPUT_DIR}/")


def zero_rate_energy_vat(sim):
    """
    Structural reform: Zero-rate VAT on domestic energy consumption.

    This reform removes the 5% VAT on domestic energy bills by:
    1. Calculating baseline VAT using the standard formula
    2. Extracting VAT embedded in energy spending: energy × (0.05/1.05)
    3. Subtracting energy VAT from total VAT

    Based on Guardian article (2 Nov 2025) and Nesta report analysis:
    - Estimated revenue loss: £2.5-3.0 billion per year
    - Average household saving: £86-95 per year
    """

    class vat(Variable):
        label = "VAT (reformed to zero-rate energy)"
        entity = Household
        definition_period = YEAR
        value_type = float
        unit = "currency-GBP"

        def formula(household, period, parameters):
            # Calculate baseline VAT using the original formula
            full_rate_consumption = household("full_rate_vat_consumption", period)
            reduced_rate_consumption = household("reduced_rate_vat_consumption", period)
            p = parameters(period).gov

            baseline_vat = (
                full_rate_consumption * p.hmrc.vat.standard_rate
                + reduced_rate_consumption * p.hmrc.vat.reduced_rate
            ) / p.simulation.microdata_vat_coverage

            # Calculate VAT on energy (energy spending includes VAT)
            domestic_energy = household("domestic_energy_consumption", period)
            energy_vat = domestic_energy * (p.hmrc.vat.reduced_rate / (1 + p.hmrc.vat.reduced_rate))

            # Reformed VAT = baseline VAT - VAT on energy
            return baseline_vat - energy_vat

    # Update the VAT variable with the reformed calculation
    sim.tax_benefit_system.update_variable(vat)

    return sim


if __name__ == "__main__":
    scenarios = [
        ScenarioConfig(
            id="zero_vat_energy",
            name="Zero-rate VAT on domestic energy",
            scenario=Scenario(
                simulation_modifier=zero_rate_energy_vat
            ),
        ),
        ScenarioConfig(
            id="two_child_limit",
            name="2 child limit repeal",
            scenario=Scenario(
                parameter_changes={
                    "gov.dwp.tax_credits.child_tax_credit.limit.child_count": {
                        str(y): np.inf for y in YEARS
                    },
                    "gov.dwp.universal_credit.elements.child.limit.child_count": {
                        str(y): np.inf for y in YEARS
                    },
                }
            ),
        ),
        ScenarioConfig(
            id="income_tax_increase_2pp",
            name="Income tax rate increase (basic and higher rates +2pp)",
            scenario=Scenario(
                parameter_changes={
                    "gov.hmrc.income_tax.rates.uk[0].rate": {
                        str(y): 0.22 for y in YEARS
                    },
                    "gov.hmrc.income_tax.rates.uk[1].rate": {
                        str(y): 0.42 for y in YEARS
                    }
                }
            ),
        ),
        ScenarioConfig(
            id="threshold_freeze_extension",
            name="Threshold freeze extension",
            scenario=Scenario(
                parameter_changes={
                    "gov.hmrc.income_tax.rates.uk[1].threshold": {
                        str(y): 37700 for y in YEARS
                    },
                    "gov.hmrc.income_tax.allowances.personal_allowance.amount": {
                        str(y): 12570 for y in YEARS
                    },
                }
            ),
        ),
        ScenarioConfig(
            id="ni_rate_reduction",
            name="National Insurance rate reduction",
            scenario=Scenario(
                parameter_changes={
                    "gov.hmrc.national_insurance.class_1.rates.employee.main": {
                        str(y): 0.06 for y in YEARS
                    },
                }
            ),
        )
    ]

    run(scenarios)
