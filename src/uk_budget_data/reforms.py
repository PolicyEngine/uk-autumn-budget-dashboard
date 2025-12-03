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

from uk_budget_data.models import Reform

# Default years for parameter changes
DEFAULT_YEARS = [2026, 2027, 2028, 2029, 2030]


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
    cpi_2030 = cpi_index("2030-04-01")

    # Fuel duty - 5p cut would end March 2026, then RPI uprating
    fuel_duty_base = 0.5795  # Rate after 5p cut ends (per Spring Budget 2025)
    rpi_2026 = rpi_index("2026-04-01")
    rpi_2027 = rpi_index("2027-04-01")
    rpi_2028 = rpi_index("2028-04-01")
    rpi_2029 = rpi_index("2029-04-01")
    rpi_2030 = rpi_index("2030-04-01")

    return {
        # Income tax thresholds - CPI indexed from April 2028
        "gov.hmrc.income_tax.allowances.personal_allowance.amount": {
            "2028": round(pa_2027 * cpi_2028 / cpi_2027),
            "2029": round(pa_2027 * cpi_2029 / cpi_2027),
            "2030": round(pa_2027 * cpi_2030 / cpi_2027),
        },
        "gov.hmrc.income_tax.rates.uk[1].threshold": {
            "2028": round(threshold_2027 * cpi_2028 / cpi_2027),
            "2029": round(threshold_2027 * cpi_2029 / cpi_2027),
            "2030": round(threshold_2027 * cpi_2030 / cpi_2027),
        },
        # Fuel duty - 5p cut ends March 2026, then RPI uprating
        "gov.hmrc.fuel_duty.petrol_and_diesel": {
            "2026-03-22": fuel_duty_base,  # 5p cut ends
            "2027-04-01": round(fuel_duty_base * rpi_2027 / rpi_2026, 4),
            "2028-04-01": round(fuel_duty_base * rpi_2028 / rpi_2026, 4),
            "2029-04-01": round(fuel_duty_base * rpi_2029 / rpi_2026, 4),
            "2030-04-01": round(fuel_duty_base * rpi_2030 / rpi_2026, 4),
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
    """Create the two-child limit repeal reform.

    policyengine-uk (post PR #1432) has the two-child limit repeal baked in
    as current law from April 2026. This reform compares:
    - Baseline: Pre-budget policy (limit of 2 children)
    - Reform: policyengine-uk defaults (limit removed, infinity from Apr 2026)

    OBR costing: £2.1-2.8bn annually (static)
    """
    return Reform(
        id="two_child_limit",
        name="2 child limit repeal",
        description=(
            "Removes the two-child limit on benefits from April 2026. The limit "
            "restricts child-related payments in Universal Credit and Tax Credits "
            "to the first two children in a family. Compares Autumn Budget policy "
            "(limit removed) against pre-budget baseline (limit of 2)."
        ),
        # Baseline: Pre-budget policy (limit of 2 children)
        baseline_parameter_changes={
            "gov.dwp.tax_credits.child_tax_credit.limit.child_count": (
                _years_dict(2)
            ),
            "gov.dwp.universal_credit.elements.child.limit.child_count": (
                _years_dict(2)
            ),
        },
        # Reform: Use policyengine-uk defaults (infinity from April 2026)
        parameter_changes={},
    )


def _create_fuel_duty_freeze() -> Reform:
    """Create the fuel duty freeze extension reform.

    Compares Autumn Budget policy against pre-budget baseline:
    - Baseline: 5p cut ends March 2026, then RPI uprating
    - Reform: Current law (policyengine-uk 2.60.0+) with freeze until Sept 2026,
      staggered reversal (+1p Sep, +2p Dec, +2p Mar), then RPI uprating

    Note: We hardcode the baseline because policyengine-uk 2.60.0+ has
    post-budget values baked in. The baseline represents what would have
    happened without the Autumn Budget (5p cut ending, then RPI).

    See https://policyengine.org/uk/research/fuel-duty-freeze-2025
    """
    # Baseline: What would have happened without Autumn Budget
    # 5p cut ends March 2026 → 57.95p, then RPI uprating
    # Uses same methodology as blog post policy 95147
    baseline_rates = {
        "2026": 0.58,  # 5p cut ends, returns to 57.95p rounded
        "2027": 0.61,  # RPI uprating
        "2028": 0.63,
        "2029": 0.64,
        "2030": 0.66,  # Continued RPI uprating
    }

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
            "gov.hmrc.fuel_duty.petrol_and_diesel": baseline_rates
        },
        parameter_changes={},  # Use current law (policyengine-uk 2.60.0+)
    )


# =============================================================================
# TAX MEASURES (revenue raisers)
# =============================================================================


def _create_threshold_freeze_extension() -> Reform:
    """Create the threshold freeze extension reform.

    policyengine-uk 2.60.0+ has frozen thresholds (Autumn Budget policy).
    This reform compares against the pre-budget baseline (CPI uprating).
    - Baseline: CPI-indexed from 2028 (pre-budget)
    - Reform: Frozen at £12,570 PA and £37,700 threshold (policyengine-uk default)
    """
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
                "2030": 0.20,
            },
            "gov.hmrc.income_tax.rates.savings.higher": {
                "2027": 0.40,
                "2028": 0.40,
                "2029": 0.40,
                "2030": 0.40,
            },
            "gov.hmrc.income_tax.rates.savings.additional": {
                "2027": 0.45,
                "2028": 0.45,
                "2029": 0.45,
                "2030": 0.45,
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
                "2030": 0.20,
            },
            "gov.hmrc.income_tax.rates.property.higher": {
                "2027": 0.40,
                "2028": 0.40,
                "2029": 0.40,
                "2030": 0.40,
            },
            "gov.hmrc.income_tax.rates.property.additional": {
                "2027": 0.45,
                "2028": 0.45,
                "2029": 0.45,
                "2030": 0.45,
            },
        },
        parameter_changes={},  # Uses new rates from policyengine-uk v2.60+
    )


# =============================================================================
# STRUCTURAL REFORMS (using simulation modifiers)
# =============================================================================


def _connect_student_loan_variables(sim: Simulation) -> Simulation:
    """Connect policyengine-uk's modelled student loan repayments to revenue.

    The microdata (policyengine-uk-data) now includes student_loan_plan imputed
    based on age and reported repayments. This modifier just connects the
    policyengine-uk student_loan_repayment variable to the tax/revenue totals.

    Note: Requires policyengine-uk-data with student_loan_plan imputation.
    """
    # Connect policyengine-uk's modelled repayments to government revenue
    # Replace reported repayments with modelled repayments
    sim.tax_benefit_system.variables["gov_tax"].adds.remove(
        "student_loan_repayments"
    )
    sim.tax_benefit_system.variables["gov_tax"].adds.append(
        "student_loan_repayment"
    )

    sim.tax_benefit_system.variables["household_tax"].adds.remove(
        "student_loan_repayments"
    )
    sim.tax_benefit_system.variables["household_tax"].adds.append(
        "student_loan_repayment"
    )

    # Update HBAI household income
    sim.tax_benefit_system.variables[
        "hbai_household_net_income"
    ].subtracts.append("student_loan_repayment")
    sim.tax_benefit_system.variables["hbai_household_net_income"].adds.append(
        "student_loan_repayments"
    )
    return sim


def _calculate_pre_freeze_thresholds() -> dict:
    """Calculate what Plan 2 thresholds would be without the freeze.

    Returns baseline (counterfactual) thresholds assuming RPI uprating
    continued from 2027 instead of the Autumn Budget freeze.

    Current law (policyengine-uk):
    - 2026: £29,385
    - 2027-2029: £29,385 (frozen)
    - 2030+: RPI uprating

    Baseline counterfactual:
    - 2026: £29,385
    - 2027-2029: RPI uprating (not frozen)
    - 2030+: RPI uprating
    """
    from policyengine_uk.system import system

    params = system.parameters
    rpi_index = params.gov.economic_assumptions.indices.obr.rpi

    # Base threshold for 2026 is £29,385 (uprated from £28,470)
    base_2026 = 29385

    rpi_2026 = rpi_index("2026-04-06")
    rpi_2027 = rpi_index("2027-04-06")
    rpi_2028 = rpi_index("2028-04-06")
    rpi_2029 = rpi_index("2029-04-06")
    rpi_2030 = rpi_index("2030-04-06")

    return {
        # Baseline: Continue RPI uprating from 2027 (no freeze)
        # Use January 1 dates since calculations use period.start.year
        "gov.hmrc.student_loans.thresholds.plan_2": {
            "2027-01-01": round(base_2026 * rpi_2027 / rpi_2026),
            "2028-01-01": round(base_2026 * rpi_2028 / rpi_2026),
            "2029-01-01": round(base_2026 * rpi_2029 / rpi_2026),
            "2030-01-01": round(base_2026 * rpi_2030 / rpi_2026),
        },
    }


def _create_student_loan_freeze() -> Reform:
    """Create the student loan threshold freeze reform.

    Uses policyengine-uk's student_loan_repayment variable with:
    - Reform: Current law (frozen thresholds from policyengine-uk)
    - Baseline: RPI uprating counterfactual

    The freeze saves the government money (more repayments) as graduates
    pay back more when thresholds don't rise with inflation.

    HMT fiscal impact:
    - 2026-27: +£5.9bn (one-off revaluation of student loan book)
    - 2027-28: +£0.3bn
    - 2028-29: +£0.3bn
    - 2029-30: +£0.4bn
    """
    baseline_thresholds = _calculate_pre_freeze_thresholds()

    return Reform(
        id="freeze_student_loan_thresholds",
        name="Freeze student loan repayment thresholds",
        description=(
            "Freezes Plan 2 student loan repayment thresholds for 3 years "
            "from 6 April 2027 through April 2029. Threshold is £29,385 in "
            "2026, then frozen at that level for 3 years, resuming RPI "
            "uprating from 2030. In 2026, the government revalued the student "
            "loan book resulting in a one-off £5.9bn fiscal impact. Ongoing "
            "annual revenue of ~£0.3bn/year from 2027-2029 as graduates repay "
            "more when thresholds don't rise with inflation. Reform uses "
            "current law (frozen thresholds); baseline assumes RPI uprating "
            "would have continued. HMT costing: +£5.9bn (2026), +£0.3bn/year "
            "thereafter."
        ),
        # Reform: Current law (frozen) - use policyengine-uk default
        simulation_modifier=_connect_student_loan_variables,
        # Baseline: RPI uprating counterfactual
        baseline_parameter_changes=baseline_thresholds,
        baseline_simulation_modifier=_connect_student_loan_variables,
    )


# Lazy-loaded reform instance
_FREEZE_STUDENT_LOAN_THRESHOLDS_CACHE: Reform | None = None


def get_freeze_student_loan_thresholds() -> Reform:
    """Get the student loan threshold freeze reform (lazy-loaded)."""
    global _FREEZE_STUDENT_LOAN_THRESHOLDS_CACHE
    if _FREEZE_STUDENT_LOAN_THRESHOLDS_CACHE is None:
        _FREEZE_STUDENT_LOAN_THRESHOLDS_CACHE = _create_student_loan_freeze()
    return _FREEZE_STUDENT_LOAN_THRESHOLDS_CACHE


# Backwards-compatible alias
FREEZE_STUDENT_LOAN_THRESHOLDS = None  # Set lazily via get function


def _get_prior_law_fare_index() -> dict:
    """Get the prior law fare index values (counterfactual without freeze).

    policyengine-uk includes both:
    - fare_index: current law with 2026 freeze baked in
    - prior_law_fare_index: what fares would be without the freeze (5.8% increase)

    Returns the prior_law_fare_index values for use as baseline.
    """
    from policyengine_uk.system import system

    params = system.parameters
    prior_law = params.gov.dft.rail.prior_law_fare_index

    return {
        "2026": prior_law("2026-04-01"),
        "2027": prior_law("2027-04-01"),
        "2028": prior_law("2028-04-01"),
        "2029": prior_law("2029-04-01"),
        "2030": prior_law("2030-04-01"),
    }


def _create_rail_fares_freeze() -> Reform:
    """Create the rail fares freeze reform.

    Freezes regulated rail fares for one year from March 2026 - the first
    freeze in 30 years. Saves passengers an estimated £600 million in
    2026-27 (per government estimates).

    policyengine-uk includes:
    - fare_index: current law (with freeze baked in from 2026)
    - prior_law_fare_index: counterfactual (5.8% increase in 2026 under RPI)

    This reform uses:
    - Baseline: prior_law_fare_index (what would have happened without freeze)
    - Reform: pe-uk defaults (fare_index with freeze)

    OBR fiscal impact (Table 3.5):
    - 2026-27: -£0.1bn (cost)
    - 2027-28: -£0.2bn (cost)
    - 2028-29: -£0.2bn (cost)
    - 2029-30: -£0.2bn (cost)
    - 2030-31: -£0.2bn (cost)
    """
    prior_law_fares = _get_prior_law_fare_index()

    return Reform(
        id="rail_fares_freeze",
        name="Rail fares freeze",
        description=(
            "Freezes regulated rail fares for one year from March 2026. "
            "Without the freeze, fares would have increased by 5.8% under the "
            "RPI formula. Saves commuters on expensive routes over £300/year. "
            "See https://policyengine.org/uk/research/rail-fares-freeze-2025"
        ),
        baseline_parameter_changes={
            "gov.dft.rail.fare_index": prior_law_fares,
        },
        parameter_changes={},  # Use pe-uk defaults (fare_index with freeze)
    )


def create_salary_sacrifice_cap_reform(
    cap_amount: float = 2000,
    employer_response_haircut: float = 0.13,
) -> Reform:
    """Create a salary sacrifice cap reform with configurable parameters.

    policyengine-uk (post PR #1432) has the salary sacrifice cap baked in
    as current law from April 2029. This reform compares:
    - Baseline: Pre-budget policy (no cap, infinity)
    - Reform: policyengine-uk defaults (£2,000 cap from April 2029)

    The simulation_modifier applies behavioural responses:
    - Employees redirect excess contributions to regular pension
    - Employers spread increased NI costs across workers (haircut)

    Args:
        cap_amount: Annual cap on NI-free salary sacrifice in GBP.
        employer_response_haircut: Proportion of excess that employers retain.

    Returns:
        Reform object configured with the specified parameters.

    OBR costing: £4.9bn in 2029-30 (static)
    """

    def modifier(sim: Simulation) -> Simulation:
        # Policy takes effect from April 2029 (fiscal year 2029-30)
        for year in range(2029, 2031):
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
        name="Salary sacrifice cap",
        description=(
            f"Caps salary sacrifice pension contributions at £{cap_amount:,.0f} "
            f"per year from April 2029. Contributions above the cap become "
            f"subject to employee and employer NICs. Compares Autumn Budget "
            f"policy (£2,000 cap) against pre-budget baseline (no cap). "
            f"Assumes employees redirect excess to regular pension contributions "
            f"and employers spread increased NI costs ({employer_response_haircut:.0%} haircut)."
        ),
        # Baseline: Pre-budget policy (no cap)
        baseline_parameter_changes={
            "gov.hmrc.national_insurance.salary_sacrifice_pension_cap": {
                "2029": np.inf,
                "2030": np.inf,
            }
        },
        # Reform: Use policyengine-uk defaults (£2,000 cap from April 2029)
        # plus behavioural response modifier
        parameter_changes={},
        simulation_modifier=modifier,
    )


# =============================================================================
# COMBINED AUTUMN BUDGET REFORM
# =============================================================================


def _create_combined_autumn_budget_reform() -> Reform:
    """Create a combined reform with all Autumn Budget 2025 provisions.

    policyengine-uk (post PR #1432) has the following baked in as current law:
    - Two-child limit repeal (from April 2026)
    - Salary sacrifice cap £2,000 (from April 2029)

    This reform combines all Autumn Budget provisions:
    - Two-child limit repeal (spending)
    - Salary sacrifice cap (revenue)
    - Fuel duty freeze extension (spending)
    - Threshold freeze extension (revenue)
    - Student loan threshold freeze (revenue)
    - Dividend tax increase +2pp (revenue)
    - Savings tax increase +2pp (revenue)
    - Property tax increase +2pp (revenue)

    Note: Zero-rate VAT on energy is NOT included as it was not in the budget.
    """
    baseline = get_pre_autumn_budget_baseline()

    # Fuel duty baseline: 5p cut ends March 2026, then RPI uprating
    # (hardcoded because policyengine-uk 2.60.0+ has post-budget values)
    fuel_duty_baseline = {
        "2026": 0.58,
        "2027": 0.61,
        "2028": 0.63,
        "2029": 0.64,
        "2030": 0.66,
    }

    # Combine all baseline parameter changes
    combined_baseline_params = {
        # Two-child limit baseline (pre-budget: limit of 2)
        "gov.dwp.tax_credits.child_tax_credit.limit.child_count": (
            _years_dict(2)
        ),
        "gov.dwp.universal_credit.elements.child.limit.child_count": (
            _years_dict(2)
        ),
        # Salary sacrifice cap baseline (pre-budget: no cap)
        "gov.hmrc.national_insurance.salary_sacrifice_pension_cap": {
            "2029": np.inf,
            "2030": np.inf,
        },
        # Fuel duty baseline (pre-budget rates - hardcoded)
        "gov.hmrc.fuel_duty.petrol_and_diesel": fuel_duty_baseline,
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
            "2030": 0.20,
        },
        "gov.hmrc.income_tax.rates.savings.higher": {
            "2027": 0.40,
            "2028": 0.40,
            "2029": 0.40,
            "2030": 0.40,
        },
        "gov.hmrc.income_tax.rates.savings.additional": {
            "2027": 0.45,
            "2028": 0.45,
            "2029": 0.45,
            "2030": 0.45,
        },
        # Property tax baseline (pre-budget rates)
        "gov.hmrc.income_tax.rates.property.basic": {
            "2027": 0.20,
            "2028": 0.20,
            "2029": 0.20,
            "2030": 0.20,
        },
        "gov.hmrc.income_tax.rates.property.higher": {
            "2027": 0.40,
            "2028": 0.40,
            "2029": 0.40,
            "2030": 0.40,
        },
        "gov.hmrc.income_tax.rates.property.additional": {
            "2027": 0.45,
            "2028": 0.45,
            "2029": 0.45,
            "2030": 0.45,
        },
    }

    # Combined baseline simulation modifier for dividend rates and student loans
    def combined_baseline_modifier(sim):
        """Apply pre-budget dividend rates and connect student loan variables."""
        _set_pre_budget_dividend_rates(sim)
        _connect_student_loan_variables(sim)
        return sim

    # Combined reform simulation modifier
    def combined_reform_modifier(sim):
        """Connect student loan variables for reform."""
        _connect_student_loan_variables(sim)
        return sim

    # Add student loan baseline thresholds (RPI uprating counterfactual)
    slr_baseline = _calculate_pre_freeze_thresholds()
    combined_baseline_params.update(slr_baseline)

    # Reform: Use policyengine-uk defaults (all budget policies baked in)
    reform_params = {}

    return Reform(
        id="autumn_budget_2025_combined",
        name="Autumn Budget 2025 (combined)",
        description=(
            "All Autumn Budget 2025 provisions combined: two-child limit "
            "repeal, salary sacrifice cap, fuel duty freeze extension, "
            "threshold freeze extension, student loan threshold freeze, and "
            "tax rate increases on dividends (+2pp), savings (+2pp), and "
            "property income (+2pp). Shows full budget impact with interactions."
        ),
        baseline_parameter_changes=combined_baseline_params,
        baseline_simulation_modifier=combined_baseline_modifier,
        simulation_modifier=combined_reform_modifier,
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
            _create_rail_fares_freeze(),
            _create_threshold_freeze_extension(),
            _create_dividend_tax_increase(),
            _create_savings_tax_increase(),
            _create_property_tax_increase(),
            get_freeze_student_loan_thresholds(),
            create_salary_sacrifice_cap_reform(),
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
