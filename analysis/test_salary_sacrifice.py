"""
Test file to check if salary sacrifice reform generates budgetary impact.
Only runs the salary sacrifice cap reform.
"""

import os
from pathlib import Path

import numpy as np
from policyengine_uk import Microsimulation, Scenario
from policyengine_uk.data import UKSingleYearDataset
from pydantic import BaseModel
from rich.console import Console

console = Console()

OUTPUT_DIR = Path("./test_output")
YEARS = [2026, 2027, 2028, 2029]

# Path to enhanced dataset with salary sacrifice data
ENHANCED_DATASET_PATH = "/Users/janansadeqian/policyengine-uk-data/policyengine_uk_data/storage/enhanced_frs_2023_24.h5"


class ScenarioConfig(BaseModel):
    """Configuration for a single reform scenario."""

    id: str
    name: str
    scenario: any

    class Config:
        arbitrary_types_allowed = True


def create_ss_cap_reform(employer_response_haircut: float = 0.13, cap_amount: float = 2000):
    """
    Salary sacrifice cap reform.

    This reform caps salary sacrifice pension contributions at a specified amount per year,
    after which national insurance applies. The default cap is £2,000 per year.

    Based on Financial Times reporting (24 November 2025):
    - Estimated revenue: £3-4 billion per year
    - Default employer response haircut: 13% (proportion of excess that employers reduce)
    - When contributions exceed the cap, the excess is converted to regular employment income

    Args:
        employer_response_haircut: Proportion by which employers reduce their response (default 0.13)
        cap_amount: Annual cap on NI-free salary sacrifice in £ (default 2000)
    """
    def modify(sim):
        for year in range(2026, 2031):
            ss_contrib = sim.calculate("pension_contributions_via_salary_sacrifice", period=year)
            excess_ss_contrib = np.maximum(
                ss_contrib - cap_amount, 0
            )
            emp_income = sim.calculate("employment_income", period=year)
            new_employment_income = emp_income + excess_ss_contrib * (1 - employer_response_haircut)
            sim.set_input("employment_income", year, new_employment_income)
            sim.set_input("employee_pension_contributions", year, excess_ss_contrib * (1 - employer_response_haircut) + sim.calculate("employee_pension_contributions", period=year))
            sim.set_input("pension_contributions_via_salary_sacrifice", year, ss_contrib - excess_ss_contrib)
    return Scenario(simulation_modifier=modify)


def test_reform():
    """Test the salary sacrifice cap reform."""
    console.print("[yellow]Testing salary sacrifice cap reform...[/yellow]")

    # Load enhanced dataset with salary sacrifice data
    console.print(f"[cyan]Loading enhanced dataset from: {ENHANCED_DATASET_PATH}[/cyan]")
    dataset = UKSingleYearDataset(file_path=ENHANCED_DATASET_PATH)

    # Create baseline and reformed simulations
    baseline = Microsimulation(dataset=dataset)
    reformed = Microsimulation(dataset=dataset, scenario=create_ss_cap_reform(employer_response_haircut=0.13, cap_amount=2000))

    console.print("\n[cyan]Budgetary Impact:[/cyan]")
    for year in YEARS:
        baseline_balance = baseline.calculate("gov_balance", period=year).sum() / 1e9
        reformed_balance = reformed.calculate("gov_balance", period=year).sum() / 1e9
        impact = reformed_balance - baseline_balance

        console.print(f"  {year}: £{impact:.2f}bn")

    # Try to check if salary sacrifice variable exists
    console.print("\n[cyan]Checking salary sacrifice data:[/cyan]")
    try:
        ss_contrib = baseline.calculate("pension_contributions_via_salary_sacrifice", period=2026)
        console.print(f"  ✓ Variable exists")
        console.print(f"  Total people with SS: {(ss_contrib > 0).sum()}")
        console.print(f"  Total SS amount: £{ss_contrib.sum() / 1e9:.2f}bn")
        console.print(f"  Average among those with SS: £{ss_contrib[ss_contrib > 0].mean():.0f}")
        console.print(f"  People above £2000 cap: {(ss_contrib > 2000).sum()}")
    except Exception as e:
        console.print(f"  ✗ Error: {e}")

    # Check other pension variables
    console.print("\n[cyan]Other pension variables:[/cyan]")
    for var in ['employee_pension_contributions', 'pension_contributions', 'personal_pension_contributions']:
        try:
            values = baseline.calculate(var, period=2026)
            console.print(f"  {var}:")
            console.print(f"    Total: £{values.sum() / 1e9:.2f}bn")
            console.print(f"    People with contributions: {(values > 0).sum()}")
            console.print(f"    Average among contributors: £{values[values > 0].mean():.0f}")
        except Exception as e:
            console.print(f"  {var}: Error - {e}")


if __name__ == "__main__":
    test_reform()
