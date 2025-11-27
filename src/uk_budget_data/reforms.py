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
from policyengine_uk import Simulation, Microsimulation
from policyengine_uk.model_api import *

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
    from policyengine_uk.system import system

    params = system.parameters

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


# Cache for lazy-loaded baseline
_PRE_AUTUMN_BUDGET_BASELINE_CACHE: dict | None = None


def get_pre_autumn_budget_baseline() -> dict:
    """Get the pre-Autumn Budget baseline values (lazy-loaded).

    Returns cached values on subsequent calls to avoid repeated
    Microsimulation initialization.
    """
    global _PRE_AUTUMN_BUDGET_BASELINE_CACHE
    if _PRE_AUTUMN_BUDGET_BASELINE_CACHE is None:
        _PRE_AUTUMN_BUDGET_BASELINE_CACHE = (
            _calculate_pre_autumn_budget_baseline()
        )
    return _PRE_AUTUMN_BUDGET_BASELINE_CACHE


# Alias for backwards compatibility (lazy-loaded)
PRE_AUTUMN_BUDGET_BASELINE = None  # Set lazily below


def _get_pre_ab_baseline_key(key: str) -> dict:
    """Get a specific key from the pre-AB baseline (lazy-loaded)."""
    return get_pre_autumn_budget_baseline()[key]


# =============================================================================
# SPENDING MEASURES (costs to treasury)
# =============================================================================


def _create_two_child_limit_repeal() -> Reform:
    """Create the two-child limit repeal reform."""
    return Reform(
        id="two_child_limit",
        name="2 child limit repeal",
        description=(
            "Removes the two-child limit on benefits. The limit restricts "
            "child-related payments in Universal Credit and Tax Credits to "
            "the first two children in a family."
        ),
        parameter_changes={
            "gov.dwp.tax_credits.child_tax_credit.limit.child_count": (
                _years_dict(np.inf)
            ),
            "gov.dwp.universal_credit.elements.child.limit.child_count": (
                _years_dict(np.inf)
            ),
        },
    )


def _create_fuel_duty_freeze() -> Reform:
    """Create the fuel duty freeze extension reform."""
    baseline = get_pre_autumn_budget_baseline()
    return Reform(
        id="fuel_duty_freeze",
        name="Fuel duty freeze extension",
        description=(
            "Extends the 5p fuel duty cut until September 2026, then "
            "implements a staggered reversal. Compares Autumn Budget policy "
            "(freeze) against pre-budget baseline (5p cut ending March 2026). "
            "See https://policyengine.org/uk/research/fuel-duty-freeze-2025"
        ),
        baseline_parameter_changes={
            "gov.hmrc.fuel_duty.petrol_and_diesel": baseline[
                "gov.hmrc.fuel_duty.petrol_and_diesel"
            ]
        },
        parameter_changes={},
    )


# =============================================================================
# TAX MEASURES (revenue raisers)
# =============================================================================


def _create_threshold_freeze_extension() -> Reform:
    """Create the threshold freeze extension reform."""
    baseline = get_pre_autumn_budget_baseline()
    return Reform(
        id="threshold_freeze_extension",
        name="Threshold freeze extension",
        description=(
            "Extends the freeze on income tax thresholds from April 2028 to "
            "April 2031. Personal allowance remains at £12,570 and the higher "
            "rate threshold at £37,700. Compares Autumn Budget policy (freeze) "
            "against pre-budget baseline (inflation uprating from 2028)."
        ),
        baseline_parameter_changes={
            "gov.hmrc.income_tax.allowances.personal_allowance.amount": (
                baseline[
                    "gov.hmrc.income_tax.allowances.personal_allowance.amount"
                ]
            ),
            "gov.hmrc.income_tax.rates.uk[1].threshold": (
                baseline["gov.hmrc.income_tax.rates.uk[1].threshold"]
            ),
        },
        parameter_changes={},
    )


# =============================================================================
# INCOME SOURCE TAX RATE INCREASES (from policyengine-uk PR #1395)
# =============================================================================
# These reforms compare the new Autumn Budget rates (baked into policyengine-uk)
# against the pre-budget baseline rates.
#
# Dividends: +2pp from April 2026 (basic 8.75%->10.75%, higher 33.75%->35.75%)
# Savings: +2pp from April 2027 (basic 20%->22%, higher 40%->42%, add 45%->47%)
# Property: +2pp from April 2027 (basic 20%->22%, higher 40%->42%, add 45%->47%)


def _set_pre_budget_dividend_rates(sim):
    """Set pre-budget dividend rates in the baseline simulation.

    Reverts the Autumn Budget 2025 changes:
    - Basic rate: 10.75% -> 8.75%
    - Higher rate: 35.75% -> 33.75%

    Uses simulation_modifier because dividend rates are stored in a
    ParameterScale which requires direct bracket access. Modifies
    values_list directly to replace the Autumn Budget rate change.
    """
    div = sim.tax_benefit_system.parameters.gov.hmrc.income_tax.rates.dividends
    # Revert basic rate (bracket 0) to pre-budget 8.75%
    # Directly modify the 2026-04-06 entry in values_list
    div.brackets[0].rate.values_list[0].value = 0.0875
    # Revert higher rate (bracket 1) to pre-budget 33.75%
    div.brackets[1].rate.values_list[0].value = 0.3375
    return sim


def _create_dividend_tax_increase() -> Reform:
    """Create the dividend tax increase reform.

    Increases dividend tax rates by 2pp from April 2026:
    - Basic rate: 8.75% -> 10.75%
    - Higher rate: 33.75% -> 35.75%
    - Additional rate: unchanged at 39.35%

    OBR fiscal impact (Table 3.5):
    - 2026-27: £0.3bn
    - 2027-28: £1.0bn
    - 2028-29: £1.0bn
    - 2029-30: £1.0bn
    """
    # Uses baseline_simulation_modifier because dividend rates are stored
    # in a ParameterScale which requires direct bracket modification
    return Reform(
        id="dividend_tax_increase_2pp",
        name="Dividend tax increase (+2pp)",
        description=(
            "Increases dividend tax rates by 2 percentage points from April "
            "2026. Basic rate: 8.75% → 10.75%, Higher rate: 33.75% → 35.75%. "
            "OBR estimates £1.0-1.1bn annual yield from 2027-28."
        ),
        baseline_simulation_modifier=_set_pre_budget_dividend_rates,
        parameter_changes={},  # Uses new rates from policyengine-uk
    )


def _create_savings_tax_increase() -> Reform:
    """Create the savings income tax increase reform.

    Increases savings income tax rates by 2pp from April 2027:
    - Basic rate: 20% -> 22%
    - Higher rate: 40% -> 42%
    - Additional rate: 45% -> 47%

    OBR fiscal impact (Table 3.5):
    - 2027-28: £0.0bn (starts April 2027)
    - 2028-29: £0.5bn
    - 2029-30: £0.5bn
    """
    return Reform(
        id="savings_tax_increase_2pp",
        name="Savings income tax increase (+2pp)",
        description=(
            "Increases savings income tax rates by 2 percentage points from "
            "April 2027. Basic: 20% → 22%, Higher: 40% → 42%, Additional: "
            "45% → 47%. OBR estimates £0.5bn annual yield from 2028-29."
        ),
        baseline_parameter_changes={
            # Pre-budget rates (20% basic, 40% higher, 45% additional)
            "gov.hmrc.income_tax.rates.savings.basic": {
                "2027": 0.20,
                "2028": 0.20,
                "2029": 0.20,
            },
            "gov.hmrc.income_tax.rates.savings.higher": {
                "2027": 0.40,
                "2028": 0.40,
                "2029": 0.40,
            },
            "gov.hmrc.income_tax.rates.savings.additional": {
                "2027": 0.45,
                "2028": 0.45,
                "2029": 0.45,
            },
        },
        parameter_changes={},  # Uses new rates from policyengine-uk v2.60+
    )


def _create_property_tax_increase() -> Reform:
    """Create the property income tax increase reform.

    Increases property income tax rates by 2pp from April 2027:
    - Basic rate: 20% -> 22%
    - Higher rate: 40% -> 42%
    - Additional rate: 45% -> 47%

    OBR fiscal impact (Table 3.5):
    - 2027-28: £0.0bn (starts April 2027)
    - 2028-29: £0.6bn
    - 2029-30: £0.4bn
    """
    return Reform(
        id="property_tax_increase_2pp",
        name="Property income tax increase (+2pp)",
        description=(
            "Increases property income tax rates by 2 percentage points from "
            "April 2027. Basic: 20% → 22%, Higher: 40% → 42%, Additional: "
            "45% → 47%. OBR estimates £0.4-0.6bn annual yield from 2028-29."
        ),
        baseline_parameter_changes={
            # Pre-budget rates (20% basic, 40% higher, 45% additional)
            "gov.hmrc.income_tax.rates.property.basic": {
                "2027": 0.20,
                "2028": 0.20,
                "2029": 0.20,
            },
            "gov.hmrc.income_tax.rates.property.higher": {
                "2027": 0.40,
                "2028": 0.40,
                "2029": 0.40,
            },
            "gov.hmrc.income_tax.rates.property.additional": {
                "2027": 0.45,
                "2028": 0.45,
                "2029": 0.45,
            },
        },
        parameter_changes={},  # Uses new rates from policyengine-uk v2.60+
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


def _slr_model(freeze_plan_2_threshold: bool = False):
    """
    Add student loan repayment model to simulation.

    Args:
        freeze_plan_2_threshold: If True, freeze Plan 2 threshold at 2025 levels
    """

    def modify(sim: Microsimulation):
        class student_loan_plan(Variable):
            value_type = str
            entity = Person
            label = "Student Loan Plan"
            definition_period = YEAR

            def formula(person, period, parameters):
                has_slr_reported = person("student_loan_repayments", 2026) > 0
                age = person("age", 2026)
                time_attended_university = period.start.year - age + 18
                return select(
                    [
                        ~has_slr_reported,
                        time_attended_university < 2012,
                        time_attended_university < 2023,
                        True,
                    ],
                    [
                        "NONE",
                        "PLAN_1",
                        "PLAN_2",
                        "PLAN_5",
                    ],
                    default="NONE",
                )

        class student_loan_repayments_modelled(Variable):
            value_type = float
            entity = Person
            label = "Student Loan Debt"
            definition_period = YEAR

            def formula(person, period, parameters):
                plan = person("student_loan_plan", period)
                rpi = parameters.gov.economic_assumptions.indices.obr.rpi
                parameter_uprating = rpi(period) / rpi(2025)
                threshold = select(
                    [
                        plan == "PLAN_1",
                        plan == "PLAN_2",
                        plan == "PLAN_4",
                        plan == "PLAN_5",
                        True,
                    ],
                    [
                        26065 * parameter_uprating,
                        28470
                        * (
                            parameter_uprating
                            if not freeze_plan_2_threshold
                            else 1
                        ),
                        32745 * parameter_uprating,
                        25000 * parameter_uprating,
                        np.inf,
                    ],
                )
                income = person("adjusted_net_income", period)

                repayment_rate = 0.09
                repayment = repayment_rate * max_(0, income - threshold)
                return repayment

        sim.tax_benefit_system.update_variable(student_loan_plan)
        sim.tax_benefit_system.add_variable(student_loan_repayments_modelled)
        sim.tax_benefit_system.variables[
            "hbai_household_net_income"
        ].subtracts.append("student_loan_repayments_modelled")
        sim.tax_benefit_system.variables[
            "hbai_household_net_income"
        ].adds.append("student_loan_repayments")

    return modify


FREEZE_STUDENT_LOAN_THRESHOLDS = Reform(
    id="freeze_student_loan_thresholds",
    name="Freeze student loan repayment thresholds",
    description=(
        "Freezes Plan 2 student loan repayment thresholds for three years "
        "from April 2027. Baseline assumes thresholds remain frozen at 2025 "
        "levels; reform allows RPI uprating, reducing repayments. OBR costing: "
        "+£255-380m annual cost (2027-2030)."
    ),
    simulation_modifier=_slr_model(
        freeze_plan_2_threshold=False
    ),  # Reform: allow uprating (reduces repayments)
    baseline_simulation_modifier=_slr_model(
        freeze_plan_2_threshold=True
    ),  # Baseline: frozen (more repayments)
)


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
# COMBINED AUTUMN BUDGET REFORM
# =============================================================================


def _create_combined_autumn_budget_reform() -> Reform:
    """Create a combined reform with all Autumn Budget 2025 provisions.

    This reform combines:
    - Two-child limit repeal (spending)
    - Fuel duty freeze extension (spending)
    - Threshold freeze extension (revenue)
    - Dividend tax increase +2pp (revenue)
    - Savings tax increase +2pp (revenue)
    - Property tax increase +2pp (revenue)

    Note: Zero-rate VAT on energy is NOT included as it was not in the budget.
    """
    baseline = get_pre_autumn_budget_baseline()

    # Combine all baseline parameter changes
    combined_baseline_params = {
        # Fuel duty baseline (pre-budget rates)
        "gov.hmrc.fuel_duty.petrol_and_diesel": baseline[
            "gov.hmrc.fuel_duty.petrol_and_diesel"
        ],
        # Threshold baseline (CPI-indexed from 2028)
        "gov.hmrc.income_tax.allowances.personal_allowance.amount": baseline[
            "gov.hmrc.income_tax.allowances.personal_allowance.amount"
        ],
        "gov.hmrc.income_tax.rates.uk[1].threshold": baseline[
            "gov.hmrc.income_tax.rates.uk[1].threshold"
        ],
        # Savings tax baseline (pre-budget rates)
        "gov.hmrc.income_tax.rates.savings.basic": {
            "2027": 0.20,
            "2028": 0.20,
            "2029": 0.20,
        },
        "gov.hmrc.income_tax.rates.savings.higher": {
            "2027": 0.40,
            "2028": 0.40,
            "2029": 0.40,
        },
        "gov.hmrc.income_tax.rates.savings.additional": {
            "2027": 0.45,
            "2028": 0.45,
            "2029": 0.45,
        },
        # Property tax baseline (pre-budget rates)
        "gov.hmrc.income_tax.rates.property.basic": {
            "2027": 0.20,
            "2028": 0.20,
            "2029": 0.20,
        },
        "gov.hmrc.income_tax.rates.property.higher": {
            "2027": 0.40,
            "2028": 0.40,
            "2029": 0.40,
        },
        "gov.hmrc.income_tax.rates.property.additional": {
            "2027": 0.45,
            "2028": 0.45,
            "2029": 0.45,
        },
    }

    # Combined baseline simulation modifier for dividend rates
    def combined_baseline_modifier(sim):
        """Apply pre-budget dividend rates to baseline simulation."""
        _set_pre_budget_dividend_rates(sim)
        _slr_model(False)(sim)
        return sim

    # Reform parameter changes (two-child limit repeal)
    reform_params = {
        "gov.dwp.tax_credits.child_tax_credit.limit.child_count": _years_dict(
            np.inf
        ),
        "gov.dwp.universal_credit.elements.child.limit.child_count": (
            _years_dict(np.inf)
        ),
    }

    return Reform(
        id="autumn_budget_2025_combined",
        name="Autumn Budget 2025 (combined)",
        description=(
            "All Autumn Budget 2025 provisions combined: two-child limit "
            "repeal, fuel duty freeze extension, threshold freeze extension, "
            "and tax rate increases on dividends (+2pp), savings (+2pp), and "
            "property income (+2pp). Shows full budget impact with interactions."
        ),
        baseline_parameter_changes=combined_baseline_params,
        baseline_simulation_modifier=combined_baseline_modifier,
        simulation_modifier=_slr_model(True),
        parameter_changes=reform_params,
    )


# =============================================================================
# REFORM COLLECTIONS (lazy-loaded to avoid import-time Microsimulation)
# =============================================================================

# Cache for lazy-loaded reforms
_AUTUMN_BUDGET_2025_REFORMS_CACHE: list[Reform] | None = None
_ALL_REFORMS_CACHE: list[Reform] | None = None
_REFORM_LOOKUP_CACHE: dict[str, Reform] | None = None


def _get_autumn_budget_2025_reforms() -> list[Reform]:
    """Get the main Autumn Budget 2025 reforms (lazy-loaded)."""
    global _AUTUMN_BUDGET_2025_REFORMS_CACHE
    if _AUTUMN_BUDGET_2025_REFORMS_CACHE is None:
        _AUTUMN_BUDGET_2025_REFORMS_CACHE = [
            _create_combined_autumn_budget_reform(),  # Combined first
            _create_two_child_limit_repeal(),
            _create_fuel_duty_freeze(),
            _create_threshold_freeze_extension(),
            _create_dividend_tax_increase(),
            _create_savings_tax_increase(),
            _create_property_tax_increase(),
            FREEZE_STUDENT_LOAN_THRESHOLDS,
            ZERO_VAT_ENERGY,
        ]
    return _AUTUMN_BUDGET_2025_REFORMS_CACHE


def _get_all_reforms() -> list[Reform]:
    """Get all available reforms (lazy-loaded)."""
    global _ALL_REFORMS_CACHE
    if _ALL_REFORMS_CACHE is None:
        _ALL_REFORMS_CACHE = _get_autumn_budget_2025_reforms() + [
            create_salary_sacrifice_cap_reform(),
        ]
    return _ALL_REFORMS_CACHE


def _get_reform_lookup() -> dict[str, Reform]:
    """Get the reform lookup dictionary (lazy-loaded)."""
    global _REFORM_LOOKUP_CACHE
    if _REFORM_LOOKUP_CACHE is None:
        _REFORM_LOOKUP_CACHE = {r.id: r for r in _get_all_reforms()}
    return _REFORM_LOOKUP_CACHE


# Public getter functions for backwards compatibility
def get_autumn_budget_2025_reforms() -> list[Reform]:
    """Get the main Autumn Budget 2025 reforms.

    Returns a list of Reform objects for all policies in the November 2025
    Autumn Budget. Lazy-loaded to avoid import-time initialization.
    """
    return _get_autumn_budget_2025_reforms()


def get_all_reforms() -> list[Reform]:
    """Get all available reforms including experimental ones.

    Returns a list of all Reform objects, including both Autumn Budget
    reforms and experimental reforms like salary sacrifice cap.
    """
    return _get_all_reforms()


# Module-level aliases that are lazy-loaded on first access
# Note: These are initially None and populated on first use via get_reform()
# For most use cases, prefer using get_reform(id) or get_autumn_budget_2025_reforms()
AUTUMN_BUDGET_2025_REFORMS: list[Reform] | None = None
ALL_REFORMS: list[Reform] | None = None


def get_reform(reform_id: str) -> Optional[Reform]:
    """Get a reform by its ID.

    Args:
        reform_id: The unique identifier of the reform.

    Returns:
        The Reform object, or None if not found.
    """
    return _get_reform_lookup().get(reform_id)


def list_reform_ids() -> list[str]:
    """Get a list of all available reform IDs."""
    return list(_get_reform_lookup().keys())
