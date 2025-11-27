"""Reform definitions for UK Autumn Budget 2025.

This module contains all policy reforms announced in the November 2025 Budget,
implemented as Reform objects that can be processed by the data pipeline.

Reforms are organised into:
- Spending measures (costs to treasury)
- Tax measures (revenue raisers)
- Structural reforms (using simulation modifiers)

Since policyengine-uk v2.59.0 includes the Autumn Budget parameter updates,
we use a pre-Autumn Budget baseline to show the impact of budget policies.
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
# PRE-AUTUMN BUDGET BASELINE
# =============================================================================
# These values represent what parameters would have been WITHOUT the November
# 2025 Autumn Budget. Used as baseline for comparing budget policy impacts.
#
# Income tax thresholds: Would have unfrozen after April 2028
# Personal allowance and basic rate threshold uprated by CPI from April 2028
#
# Fuel duty: 5p cut would have ended March 2026 per Spring Budget 2025
# Would return to 57.95p then RPI uprating from April 2027


def _calculate_pre_autumn_budget_baseline() -> dict:
    """Calculate pre-Autumn Budget baseline values programmatically.

    Uses OBR inflation forecasts from policyengine-uk to calculate what
    income tax thresholds and fuel duty rates would have been without
    the November 2025 Autumn Budget.
    """
    from policyengine_uk import Microsimulation

    sim = Microsimulation()
    params = sim.tax_benefit_system.parameters

    # Get OBR inflation indices
    cpi_index = params.gov.economic_assumptions.indices.obr.cpih
    rpi_index = params.gov.economic_assumptions.indices.obr.rpi

    # Income tax thresholds - CPI uprating from April 2028
    # (Previous freeze was until April 2028)
    pa_2027 = 12570  # Personal allowance frozen at this level until Apr 2028
    threshold_2027 = 37700  # Basic rate threshold frozen until Apr 2028

    cpi_2027 = cpi_index("2027-04-01")
    cpi_2028 = cpi_index("2028-04-01")
    cpi_2029 = cpi_index("2029-04-01")

    # Fuel duty - 5p cut would end March 2026, then RPI uprating
    fuel_duty_base = 0.5795  # Rate after 5p cut ends (per Spring Budget 2025)
    rpi_2026 = rpi_index("2026-04-01")
    rpi_2027 = rpi_index("2027-04-01")
    rpi_2028 = rpi_index("2028-04-01")
    rpi_2029 = rpi_index("2029-04-01")

    return {
        # Income tax thresholds - CPI indexed from April 2028
        "gov.hmrc.income_tax.allowances.personal_allowance.amount": {
            "2028": round(pa_2027 * cpi_2028 / cpi_2027),
            "2029": round(pa_2027 * cpi_2029 / cpi_2027),
        },
        "gov.hmrc.income_tax.rates.uk[1].threshold": {
            "2028": round(threshold_2027 * cpi_2028 / cpi_2027),
            "2029": round(threshold_2027 * cpi_2029 / cpi_2027),
        },
        # Fuel duty - 5p cut ends March 2026, then RPI uprating
        "gov.hmrc.fuel_duty.petrol_and_diesel": {
            "2026-03-22": fuel_duty_base,  # 5p cut ends
            "2027-04-01": round(fuel_duty_base * rpi_2027 / rpi_2026, 4),
            "2028-04-01": round(fuel_duty_base * rpi_2028 / rpi_2026, 4),
            "2029-04-01": round(fuel_duty_base * rpi_2029 / rpi_2026, 4),
        },
    }


# Calculate baseline values using OBR forecasts
PRE_AUTUMN_BUDGET_BASELINE = _calculate_pre_autumn_budget_baseline()


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
        "Extends the 5p fuel duty cut until September 2026, then implements a "
        "staggered reversal. Compares Autumn Budget policy (freeze) against "
        "pre-budget baseline (5p cut ending March 2026). "
        "See https://policyengine.org/uk/research/fuel-duty-freeze-2025 for details."
    ),
    # Baseline: Pre-Autumn Budget (5p cut ends March 2026, then RPI uprating)
    baseline_parameter_changes={
        "gov.hmrc.fuel_duty.petrol_and_diesel": (
            PRE_AUTUMN_BUDGET_BASELINE["gov.hmrc.fuel_duty.petrol_and_diesel"]
        )
    },
    # Reform: Current law (Autumn Budget policy) - use default parameters
    # policyengine-uk v2.59.0 has the freeze baked in
    parameter_changes={},
)


# =============================================================================
# TAX MEASURES (revenue raisers)
# =============================================================================

THRESHOLD_FREEZE_EXTENSION = Reform(
    id="threshold_freeze_extension",
    name="Threshold freeze extension",
    description=(
        "Extends the freeze on income tax thresholds from April 2028 to "
        "April 2031. Personal allowance remains at £12,570 and the higher "
        "rate threshold at £37,700. Compares Autumn Budget policy (freeze) "
        "against pre-budget baseline (inflation uprating from 2028)."
    ),
    # Baseline: Pre-Autumn Budget (thresholds unfrozen from April 2028)
    baseline_parameter_changes={
        "gov.hmrc.income_tax.allowances.personal_allowance.amount": (
            PRE_AUTUMN_BUDGET_BASELINE[
                "gov.hmrc.income_tax.allowances.personal_allowance.amount"
            ]
        ),
        "gov.hmrc.income_tax.rates.uk[1].threshold": (
            PRE_AUTUMN_BUDGET_BASELINE[
                "gov.hmrc.income_tax.rates.uk[1].threshold"
            ]
        ),
    },
    # Reform: Current law (Autumn Budget policy) - use default parameters
    # policyengine-uk v2.59.0 has the freeze extension baked in
    parameter_changes={},
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
