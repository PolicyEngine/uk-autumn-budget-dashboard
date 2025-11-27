"""Reform definitions for UK Autumn Budget 2025.

This module contains all policy reforms announced in the November 2025 Budget,
implemented as Reform objects that can be processed by the data pipeline.

Reforms are organised into:
- Spending measures (costs to treasury)
- Tax measures (revenue raisers)
- Structural reforms (using simulation modifiers)
"""

from typing import Optional

import numpy as np
from policyengine_uk import Simulation
from policyengine_uk.model_api import YEAR, Household, Variable

from uk_budget_data.models import Reform

# Default years for parameter changes
DEFAULT_YEARS = [2026, 2027, 2028, 2029]


def _years_dict(value, years: list[int] = None) -> dict[str, any]:
    """Create a {year: value} dict for parameter changes."""
    years = years or DEFAULT_YEARS
    return {str(y): value for y in years}


# =============================================================================
# SPENDING MEASURES (costs to treasury)
# =============================================================================

TWO_CHILD_LIMIT_REPEAL = Reform(
    id="two_child_limit",
    name="2 child limit repeal",
    description=(
        "Removes the two-child limit on benefits. The limit restricts "
        "child-related payments in Universal Credit and Tax Credits to "
        "the first two children in a family."
    ),
    parameter_changes={
        "gov.dwp.tax_credits.child_tax_credit.limit.child_count": _years_dict(
            np.inf
        ),
        "gov.dwp.universal_credit.elements.child.limit.child_count": (
            _years_dict(np.inf)
        ),
    },
)

FUEL_DUTY_FREEZE = Reform(
    id="fuel_duty_freeze",
    name="Fuel duty freeze extension",
    description=(
        "Freezes fuel duty rates until September 2026, comparing the announced "
        "policy (freeze at 52.95p until September 2026, then staggered reversal) "
        "against a baseline where the 5p cut ends on 22 March 2026. "
        "See https://policyengine.org/uk/research/fuel-duty-freeze-2025 for details."
    ),
    # Baseline: Higher fuel duty rates (no freeze)
    # The 5p cut ends on 22 March 2026, returning to 57.95p, then RPI uprating
    baseline_parameter_changes={
        "gov.hmrc.fuel_duty.petrol_and_diesel": {
            "2026": 0.58,
            "2027": 0.61,
            "2028": 0.63,
            "2029": 0.64,
        }
    },
    # Reform: Lower fuel duty rates (with freeze)
    # Freeze at 52.95p until September 2026, then staggered reversal
    parameter_changes={
        "gov.hmrc.fuel_duty.petrol_and_diesel": {
            "2026": 0.54,
            "2027": 0.60,
            "2028": 0.62,
            "2029": 0.63,
        }
    },
)


# =============================================================================
# TAX MEASURES (revenue raisers)
# =============================================================================

THRESHOLD_FREEZE_EXTENSION = Reform(
    id="threshold_freeze_extension",
    name="Threshold freeze extension",
    description=(
        "Extends the freeze on income tax thresholds to 2030-31. "
        "Personal allowance remains at £12,570 and the higher rate "
        "threshold at £37,700, dragging more people into higher bands "
        "through fiscal drag."
    ),
    parameter_changes={
        "gov.hmrc.income_tax.rates.uk[1].threshold": _years_dict(37700),
        "gov.hmrc.income_tax.allowances.personal_allowance.amount": (
            _years_dict(12570)
        ),
    },
)

# Placeholder reforms - parameter paths need verification
DIVIDEND_TAX_INCREASE = Reform(
    id="dividend_tax_increase_2pp",
    name="Dividend tax increase (+2pp)",
    description=(
        "Increases dividend tax rates by 2 percentage points from April 2026. "
        "Basic rate: 8.75% -> 10.75%, Higher rate: 33.75% -> 35.75%."
    ),
    parameter_changes={
        # TODO: Add correct parameter paths for dividend tax rates
    },
)

SAVINGS_TAX_INCREASE = Reform(
    id="savings_tax_increase_2pp",
    name="Savings income tax increase (+2pp)",
    description=(
        "Increases savings income tax rates by 2 percentage points "
        "from April 2027."
    ),
    parameter_changes={
        # TODO: Add correct parameter paths for savings tax rates
    },
)

PROPERTY_TAX_INCREASE = Reform(
    id="property_tax_increase_2pp",
    name="Property income tax increase (+2pp)",
    description=(
        "Increases property income tax rates by 2 percentage points "
        "from April 2027."
    ),
    parameter_changes={
        # TODO: This may require a structural reform
    },
)


# =============================================================================
# STRUCTURAL REFORMS (using simulation modifiers)
# =============================================================================


def _zero_rate_energy_vat_modifier(sim: Simulation) -> Simulation:
    """Structural reform: Zero-rate VAT on domestic energy consumption.

    This reform removes the 5% VAT on domestic energy bills by:
    1. Calculating baseline VAT using the standard formula
    2. Extracting VAT embedded in energy spending: energy × (0.05/1.05)
    3. Subtracting energy VAT from total VAT
    """

    class vat(Variable):
        label = "VAT (reformed to zero-rate energy)"
        entity = Household
        definition_period = YEAR
        value_type = float
        unit = "currency-GBP"

        def formula(household, period, parameters):
            full_rate_consumption = household(
                "full_rate_vat_consumption", period
            )
            reduced_rate_consumption = household(
                "reduced_rate_vat_consumption", period
            )
            p = parameters(period).gov

            baseline_vat = (
                full_rate_consumption * p.hmrc.vat.standard_rate
                + reduced_rate_consumption * p.hmrc.vat.reduced_rate
            ) / p.simulation.microdata_vat_coverage

            domestic_energy = household("domestic_energy_consumption", period)
            energy_vat = domestic_energy * (
                p.hmrc.vat.reduced_rate / (1 + p.hmrc.vat.reduced_rate)
            )

            return baseline_vat - energy_vat

    sim.tax_benefit_system.update_variable(vat)
    return sim


ZERO_VAT_ENERGY = Reform(
    id="zero_vat_energy",
    name="Zero-rate VAT on energy",
    description=(
        "Removes the 5% VAT on domestic energy bills. "
        "Estimated cost: £2.5-3.0 billion per year. "
        "Average household saving: £86-95 per year."
    ),
    simulation_modifier=_zero_rate_energy_vat_modifier,
)


def create_salary_sacrifice_cap_reform(
    cap_amount: float = 2000,
    employer_response_haircut: float = 0.13,
) -> Reform:
    """Create a salary sacrifice cap reform with configurable parameters.

    This reform caps salary sacrifice pension contributions, after which
    national insurance applies to the excess.

    Args:
        cap_amount: Annual cap on NI-free salary sacrifice in GBP.
        employer_response_haircut: Proportion of excess that employers retain.

    Returns:
        Reform object configured with the specified parameters.
    """

    def modifier(sim: Simulation) -> Simulation:
        for year in range(2026, 2031):
            ss_contrib = sim.calculate(
                "pension_contributions_via_salary_sacrifice", period=year
            )
            excess_ss_contrib = np.maximum(ss_contrib - cap_amount, 0)
            emp_income = sim.calculate("employment_income", period=year)
            new_employment_income = emp_income + excess_ss_contrib * (
                1 - employer_response_haircut
            )
            sim.set_input("employment_income", year, new_employment_income)

            employee_pension = sim.calculate(
                "employee_pension_contributions", period=year
            )
            new_employee_pension = employee_pension + excess_ss_contrib * (
                1 - employer_response_haircut
            )
            sim.set_input(
                "employee_pension_contributions", year, new_employee_pension
            )

            new_ss = ss_contrib - excess_ss_contrib
            sim.set_input(
                "pension_contributions_via_salary_sacrifice", year, new_ss
            )

        return sim

    return Reform(
        id="salary_sacrifice_cap",
        name=f"NICs on salary sacrifice (>{cap_amount:,.0f})",
        description=(
            f"Caps salary sacrifice pension contributions at £{cap_amount:,.0f} "
            f"per year. Contributions above the cap become employment income "
            f"subject to income tax and NICs. Employer response haircut: "
            f"{employer_response_haircut:.0%}."
        ),
        simulation_modifier=modifier,
    )


# =============================================================================
# REFORM COLLECTIONS
# =============================================================================

# Main reforms for the November 2025 Autumn Budget
AUTUMN_BUDGET_2025_REFORMS: list[Reform] = [
    TWO_CHILD_LIMIT_REPEAL,
    FUEL_DUTY_FREEZE,
    THRESHOLD_FREEZE_EXTENSION,
    DIVIDEND_TAX_INCREASE,
    SAVINGS_TAX_INCREASE,
    PROPERTY_TAX_INCREASE,
    ZERO_VAT_ENERGY,
]

# All available reforms including experimental ones
ALL_REFORMS: list[Reform] = AUTUMN_BUDGET_2025_REFORMS + [
    create_salary_sacrifice_cap_reform(),
]

# Reform lookup by ID
_REFORM_LOOKUP: dict[str, Reform] = {r.id: r for r in ALL_REFORMS}


def get_reform(reform_id: str) -> Optional[Reform]:
    """Get a reform by its ID.

    Args:
        reform_id: The unique identifier of the reform.

    Returns:
        The Reform object, or None if not found.
    """
    return _REFORM_LOOKUP.get(reform_id)


def list_reform_ids() -> list[str]:
    """Get a list of all available reform IDs."""
    return list(_REFORM_LOOKUP.keys())
