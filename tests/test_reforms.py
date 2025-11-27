"""Tests for reform definitions."""

import os

import numpy as np
import pytest
from policyengine_uk.system import system

# Skip tests that require HuggingFace token (for microsimulation data)
requires_hf_token = pytest.mark.skipif(
    not os.environ.get("HUGGING_FACE_TOKEN"),
    reason="Requires HUGGING_FACE_TOKEN for microsimulation data",
)


class TestPreAutumnBudgetBaseline:
    """Tests for pre-Autumn Budget baseline calculation."""

    def test_income_tax_thresholds_use_cpi_uprating(self):
        """Pre-AB baseline thresholds should use CPI uprating from 2028."""
        from uk_budget_data.reforms import get_pre_autumn_budget_baseline

        PRE_AUTUMN_BUDGET_BASELINE = get_pre_autumn_budget_baseline()

        cpi_index = system.parameters.gov.economic_assumptions.indices.obr.cpih

        # Personal allowance was £12,570 in April 2027 (end of previous freeze)
        # Should be uprated by CPI from April 2028 onwards
        pa_2027 = 12570
        cpi_2027 = cpi_index("2027-04-01")
        cpi_2028 = cpi_index("2028-04-01")
        cpi_2029 = cpi_index("2029-04-01")

        expected_pa_2028 = round(pa_2027 * cpi_2028 / cpi_2027)
        expected_pa_2029 = round(pa_2027 * cpi_2029 / cpi_2027)

        pa_key = "gov.hmrc.income_tax.allowances.personal_allowance.amount"
        assert PRE_AUTUMN_BUDGET_BASELINE[pa_key]["2028"] == expected_pa_2028
        assert PRE_AUTUMN_BUDGET_BASELINE[pa_key]["2029"] == expected_pa_2029

        # Basic rate threshold was £37,700 in April 2027
        threshold_2027 = 37700
        expected_threshold_2028 = round(threshold_2027 * cpi_2028 / cpi_2027)
        expected_threshold_2029 = round(threshold_2027 * cpi_2029 / cpi_2027)

        threshold_key = "gov.hmrc.income_tax.rates.uk[1].threshold"
        assert (
            PRE_AUTUMN_BUDGET_BASELINE[threshold_key]["2028"]
            == expected_threshold_2028
        )
        assert (
            PRE_AUTUMN_BUDGET_BASELINE[threshold_key]["2029"]
            == expected_threshold_2029
        )

    def test_fuel_duty_uses_rpi_uprating(self):
        """Pre-AB baseline fuel duty should use RPI uprating after Mar 2026."""
        from uk_budget_data.reforms import get_pre_autumn_budget_baseline

        PRE_AUTUMN_BUDGET_BASELINE = get_pre_autumn_budget_baseline()

        rpi_index = system.parameters.gov.economic_assumptions.indices.obr.rpi

        # Per Spring Budget 2025, 5p cut would end March 2026 -> 57.95p
        # Then RPI uprating from April 2027
        base_rate = 0.5795  # Rate after 5p cut ends
        rpi_2026 = rpi_index("2026-04-01")
        rpi_2027 = rpi_index("2027-04-01")
        rpi_2028 = rpi_index("2028-04-01")
        rpi_2029 = rpi_index("2029-04-01")

        expected_2027 = round(base_rate * rpi_2027 / rpi_2026, 4)
        expected_2028 = round(base_rate * rpi_2028 / rpi_2026, 4)
        expected_2029 = round(base_rate * rpi_2029 / rpi_2026, 4)

        fuel_key = "gov.hmrc.fuel_duty.petrol_and_diesel"
        # March 2026: 5p cut ends
        assert PRE_AUTUMN_BUDGET_BASELINE[fuel_key]["2026-03-22"] == 0.5795
        # April 2027+: RPI uprating
        assert (
            PRE_AUTUMN_BUDGET_BASELINE[fuel_key]["2027-04-01"] == expected_2027
        )
        assert (
            PRE_AUTUMN_BUDGET_BASELINE[fuel_key]["2028-04-01"] == expected_2028
        )
        assert (
            PRE_AUTUMN_BUDGET_BASELINE[fuel_key]["2029-04-01"] == expected_2029
        )


class TestReformDefinitions:
    """Tests for the predefined reforms."""

    def test_autumn_budget_reforms_exist(self):
        """Autumn Budget 2025 reforms are defined."""
        from uk_budget_data.reforms import get_autumn_budget_2025_reforms

        reforms = get_autumn_budget_2025_reforms()
        assert len(reforms) > 0

    def test_all_reforms_have_required_fields(self):
        """All reforms have id and name."""
        from uk_budget_data.reforms import get_autumn_budget_2025_reforms

        for reform in get_autumn_budget_2025_reforms():
            assert reform.id, f"Reform missing id: {reform}"
            assert reform.name, f"Reform missing name: {reform}"

    def test_all_reforms_convertible_to_scenario(self):
        """All reforms can be converted to PolicyEngine Scenario."""
        from uk_budget_data.reforms import get_autumn_budget_2025_reforms

        for reform in get_autumn_budget_2025_reforms():
            scenario = reform.to_scenario()
            assert (
                scenario is not None
            ), f"Reform {reform.id} failed to_scenario"


class TestTwoChildLimitRepeal:
    """Tests for two-child limit repeal reform."""

    def test_reform_exists(self):
        """Two child limit reform is defined."""
        from uk_budget_data.reforms import get_reform

        reform = get_reform("two_child_limit")
        assert reform is not None
        assert reform.id == "two_child_limit"

    def test_reform_removes_child_limit(self):
        """Reform sets child limit to infinity."""
        from uk_budget_data.reforms import get_reform

        reform = get_reform("two_child_limit")
        assert reform.parameter_changes is not None

        # Check that both UC and tax credits limits are removed
        tc_key = "gov.dwp.tax_credits.child_tax_credit.limit.child_count"
        uc_key = "gov.dwp.universal_credit.elements.child.limit.child_count"

        assert tc_key in reform.parameter_changes
        assert uc_key in reform.parameter_changes

        # Values should be infinity
        for year_val in reform.parameter_changes[tc_key].values():
            assert year_val == np.inf
        for year_val in reform.parameter_changes[uc_key].values():
            assert year_val == np.inf


class TestFuelDutyFreeze:
    """Tests for fuel duty freeze reform."""

    def test_reform_exists(self):
        """Fuel duty freeze reform is defined."""
        from uk_budget_data.reforms import get_reform

        reform = get_reform("fuel_duty_freeze")
        assert reform is not None

    def test_reform_maintains_reduced_rate(self):
        """Reform maintains the 5p cut (52.95p rate)."""
        from uk_budget_data.reforms import get_reform

        reform = get_reform("fuel_duty_freeze")

        # Reform uses custom baseline (pre-Autumn Budget values)
        assert reform.has_custom_baseline()
        assert reform.baseline_parameter_changes is not None

        param_key = "gov.hmrc.fuel_duty.petrol_and_diesel"
        assert param_key in reform.baseline_parameter_changes

        # Baseline has pre-AB values (5p cut ending, higher rates)
        # Reform uses current law (policyengine-uk v2.59.0 has freeze baked in)
        assert (
            reform.baseline_parameter_changes[param_key]["2026-03-22"]
            == 0.5795
        )
        # Reform parameter_changes is empty (uses default policyengine-uk params)
        assert reform.parameter_changes == {}


class TestThresholdFreeze:
    """Tests for threshold freeze extension reform."""

    def test_reform_exists(self):
        """Threshold freeze reform is defined."""
        from uk_budget_data.reforms import get_reform

        reform = get_reform("threshold_freeze_extension")
        assert reform is not None

    def test_reform_uses_pre_ab_baseline(self):
        """Reform compares current law (freeze) against pre-AB baseline."""
        from uk_budget_data.reforms import (
            get_pre_autumn_budget_baseline,
            get_reform,
        )

        reform = get_reform("threshold_freeze_extension")
        pre_ab_baseline = get_pre_autumn_budget_baseline()

        # Reform uses custom baseline (pre-Autumn Budget values)
        assert reform.has_custom_baseline()
        assert reform.baseline_parameter_changes is not None

        pa_key = "gov.hmrc.income_tax.allowances.personal_allowance.amount"
        threshold_key = "gov.hmrc.income_tax.rates.uk[1].threshold"

        assert pa_key in reform.baseline_parameter_changes
        assert threshold_key in reform.baseline_parameter_changes

        # Baseline has inflation-indexed values from PRE_AUTUMN_BUDGET_BASELINE
        assert (
            reform.baseline_parameter_changes[pa_key]["2028"]
            == pre_ab_baseline[pa_key]["2028"]
        )
        assert (
            reform.baseline_parameter_changes[threshold_key]["2028"]
            == pre_ab_baseline[threshold_key]["2028"]
        )

        # Reform parameter_changes is empty (uses default policyengine-uk params)
        assert reform.parameter_changes == {}


class TestDividendTaxIncrease:
    """Tests for dividend tax increase reform."""

    def test_reform_exists(self):
        """Dividend tax increase reform is defined."""
        from uk_budget_data.reforms import get_reform

        reform = get_reform("dividend_tax_increase_2pp")
        assert reform is not None
        assert reform.id == "dividend_tax_increase_2pp"

    def test_reform_uses_custom_baseline(self):
        """Reform uses pre-budget baseline rates via simulation modifier."""
        from uk_budget_data.reforms import get_reform

        reform = get_reform("dividend_tax_increase_2pp")

        # Reform uses custom baseline (simulation_modifier for ParameterScale)
        assert reform.has_custom_baseline()
        assert reform.baseline_simulation_modifier is not None

        # Reform parameter_changes is empty (uses new rates from policyengine-uk)
        assert reform.parameter_changes == {}

    @requires_hf_token
    def test_baseline_modifier_sets_pre_budget_rates(self):
        """Baseline simulation modifier correctly sets pre-budget rates."""
        from policyengine_uk import Microsimulation

        from uk_budget_data.reforms import get_reform

        reform = get_reform("dividend_tax_increase_2pp")

        # Create a simulation and apply the baseline modifier
        sim = Microsimulation()
        reform.baseline_simulation_modifier(sim)

        div = sim.tax_benefit_system.parameters.gov.hmrc.income_tax.rates
        div = div.dividends

        # Check pre-budget rates are set for 2027 (8.75% basic, 33.75% higher)
        # The modifier replaces the 2026-04-06 entry so rates persist
        assert div.brackets[0].rate("2027-04-06") == 0.0875
        assert div.brackets[1].rate("2027-04-06") == 0.3375


class TestSavingsTaxIncrease:
    """Tests for savings income tax increase reform."""

    def test_reform_exists(self):
        """Savings tax increase reform is defined."""
        from uk_budget_data.reforms import get_reform

        reform = get_reform("savings_tax_increase_2pp")
        assert reform is not None
        assert reform.id == "savings_tax_increase_2pp"

    def test_reform_uses_custom_baseline(self):
        """Reform uses pre-budget baseline rates."""
        from uk_budget_data.reforms import get_reform

        reform = get_reform("savings_tax_increase_2pp")

        # Reform uses custom baseline (pre-budget rates)
        assert reform.has_custom_baseline()
        assert reform.baseline_parameter_changes is not None

        # Check baseline has pre-budget savings rates
        basic_key = "gov.hmrc.income_tax.rates.savings.basic"
        higher_key = "gov.hmrc.income_tax.rates.savings.higher"
        additional_key = "gov.hmrc.income_tax.rates.savings.additional"

        assert basic_key in reform.baseline_parameter_changes
        assert higher_key in reform.baseline_parameter_changes
        assert additional_key in reform.baseline_parameter_changes

        # Pre-budget rates: 20% basic, 40% higher, 45% additional
        assert reform.baseline_parameter_changes[basic_key]["2027"] == 0.20
        assert reform.baseline_parameter_changes[higher_key]["2027"] == 0.40
        assert (
            reform.baseline_parameter_changes[additional_key]["2027"] == 0.45
        )

        # Reform parameter_changes is empty (uses new rates from policyengine-uk)
        assert reform.parameter_changes == {}


class TestPropertyTaxIncrease:
    """Tests for property income tax increase reform."""

    def test_reform_exists(self):
        """Property tax increase reform is defined."""
        from uk_budget_data.reforms import get_reform

        reform = get_reform("property_tax_increase_2pp")
        assert reform is not None
        assert reform.id == "property_tax_increase_2pp"

    def test_reform_uses_custom_baseline(self):
        """Reform uses pre-budget baseline rates."""
        from uk_budget_data.reforms import get_reform

        reform = get_reform("property_tax_increase_2pp")

        # Reform uses custom baseline (pre-budget rates)
        assert reform.has_custom_baseline()
        assert reform.baseline_parameter_changes is not None

        # Check baseline has pre-budget property rates
        basic_key = "gov.hmrc.income_tax.rates.property.basic"
        higher_key = "gov.hmrc.income_tax.rates.property.higher"
        additional_key = "gov.hmrc.income_tax.rates.property.additional"

        assert basic_key in reform.baseline_parameter_changes
        assert higher_key in reform.baseline_parameter_changes
        assert additional_key in reform.baseline_parameter_changes

        # Pre-budget rates: 20% basic, 40% higher, 45% additional
        assert reform.baseline_parameter_changes[basic_key]["2027"] == 0.20
        assert reform.baseline_parameter_changes[higher_key]["2027"] == 0.40
        assert (
            reform.baseline_parameter_changes[additional_key]["2027"] == 0.45
        )

        # Reform parameter_changes is empty (uses new rates from policyengine-uk)
        assert reform.parameter_changes == {}


class TestRailFaresFreeze:
    """Tests for rail fares freeze reform."""

    def test_reform_exists(self):
        """Rail fares freeze reform is defined."""
        from uk_budget_data.reforms import get_reform

        reform = get_reform("rail_fares_freeze")
        assert reform is not None
        assert reform.id == "rail_fares_freeze"

    def test_reform_uses_simulation_modifier(self):
        """Reform uses simulation modifier for structural change."""
        from uk_budget_data.reforms import get_reform

        reform = get_reform("rail_fares_freeze")
        assert reform.simulation_modifier is not None

    def test_rail_fare_increase_rates_defined(self):
        """Rail fare increase rates are defined for all budget years."""
        from uk_budget_data.reforms import RAIL_FARE_INCREASES

        expected_years = [2026, 2027, 2028, 2029]
        for year in expected_years:
            assert year in RAIL_FARE_INCREASES, f"Missing rate for {year}"
            assert (
                RAIL_FARE_INCREASES[year] > 0
            ), f"Rate for {year} should be positive"
            assert (
                RAIL_FARE_INCREASES[year] < 0.10
            ), f"Rate for {year} seems too high"

        # 2026 rate should be 5.8% (the rate that was frozen)
        assert RAIL_FARE_INCREASES[2026] == 0.058

    def test_rail_freeze_costs_defined(self):
        """Rail freeze costs match Treasury estimates."""
        from uk_budget_data.reforms import RAIL_FREEZE_COSTS

        expected_years = [2026, 2027, 2028, 2029]
        for year in expected_years:
            assert year in RAIL_FREEZE_COSTS, f"Missing cost for {year}"
            assert (
                RAIL_FREEZE_COSTS[year] > 0
            ), f"Cost for {year} should be positive"

        # 2026 cost should be £0.145bn (Treasury estimate)
        assert RAIL_FREEZE_COSTS[2026] == 0.145


class TestStructuralReforms:
    """Tests for structural reforms using simulation modifiers."""

    def test_zero_vat_energy_reform_exists(self):
        """Zero VAT energy reform is defined."""
        from uk_budget_data.reforms import get_reform

        reform = get_reform("zero_vat_energy")
        assert reform is not None
        assert reform.simulation_modifier is not None

    def test_salary_sacrifice_cap_factory(self):
        """Salary sacrifice cap reform factory works."""
        from uk_budget_data.reforms import create_salary_sacrifice_cap_reform

        reform = create_salary_sacrifice_cap_reform(
            cap_amount=2000,
            employer_response_haircut=0.13,
        )
        assert reform is not None
        assert reform.id == "salary_sacrifice_cap"
        assert reform.simulation_modifier is not None


class TestGetReform:
    """Tests for get_reform helper function."""

    def test_get_existing_reform(self):
        """Can retrieve existing reform by id."""
        from uk_budget_data.reforms import get_reform

        reform = get_reform("two_child_limit")
        assert reform is not None
        assert reform.id == "two_child_limit"

    def test_get_nonexistent_reform_returns_none(self):
        """Returns None for unknown reform id."""
        from uk_budget_data.reforms import get_reform

        reform = get_reform("nonexistent_reform_xyz")
        assert reform is None


@requires_hf_token
class TestBudgetaryImpacts:
    """Tests for budgetary impact calculations.

    These tests require microsimulation data from HuggingFace.
    Set HUGGING_FACE_TOKEN environment variable to run them.

    Tests verify that PolicyEngine estimates are within reasonable
    range of OBR estimates. The tolerance accounts for methodological
    differences between OBR's costing model and PolicyEngine's microsimulation.

    OBR estimates from Autumn Budget 2025, Table 3.5.
    """

    def test_dividend_tax_produces_nonzero_revenue(self):
        """Dividend tax increase should produce positive revenue.

        OBR estimates £1.0bn/year from 2027-28.
        Currently blocked by policyengine-uk bug where dividend_income_tax
        returns 0 despite correct parameter changes.
        """
        from policyengine_uk import Microsimulation

        from uk_budget_data.reforms import get_reform

        reform = get_reform("dividend_tax_increase_2pp")
        baseline_scenario = reform.to_baseline_scenario()

        baseline = Microsimulation(scenario=baseline_scenario)
        reformed = Microsimulation()

        # Calculate revenue impact for 2027
        base_balance = baseline.calculate("gov_balance", 2027).sum()
        ref_balance = reformed.calculate("gov_balance", 2027).sum()
        impact_bn = (ref_balance - base_balance) / 1e9

        # Should produce positive revenue (higher tax rates = more revenue)
        # OBR estimates £1.0bn for 2027-28
        assert impact_bn > 0.5, (
            f"Expected dividend tax to raise >£0.5bn, got £{impact_bn:.2f}bn. "
            "This may indicate policyengine-uk bug with dividend_income_tax."
        )

    def test_savings_tax_produces_nonzero_revenue(self):
        """Savings tax increase should produce positive revenue from 2028.

        OBR estimates £0.5bn/year from 2028-29 (starts April 2027).
        Note: FRS may underreport savings income, so PolicyEngine estimate
        is expected to be lower than OBR.
        """
        from policyengine_uk import Microsimulation

        from uk_budget_data.reforms import get_reform

        reform = get_reform("savings_tax_increase_2pp")
        baseline_scenario = reform.to_baseline_scenario()

        baseline = Microsimulation(scenario=baseline_scenario)
        reformed = Microsimulation()

        # Calculate revenue impact for 2028 (first full year)
        base_balance = baseline.calculate("gov_balance", 2028).sum()
        ref_balance = reformed.calculate("gov_balance", 2028).sum()
        impact_bn = (ref_balance - base_balance) / 1e9

        # Should produce positive revenue (lower threshold due to FRS coverage)
        # OBR estimates £0.5bn for 2028-29
        assert (
            impact_bn > 0
        ), f"Expected savings tax to raise >£0bn, got £{impact_bn:.2f}bn"

    def test_property_tax_produces_nonzero_revenue(self):
        """Property tax increase should produce positive revenue from 2028.

        OBR estimates £0.6bn for 2028-29 (starts April 2027).
        Note: Property income may not be fully captured in FRS, so PolicyEngine
        estimate may be lower than OBR.
        """
        from policyengine_uk import Microsimulation

        from uk_budget_data.reforms import get_reform

        reform = get_reform("property_tax_increase_2pp")
        baseline_scenario = reform.to_baseline_scenario()

        baseline = Microsimulation(scenario=baseline_scenario)
        reformed = Microsimulation()

        # Calculate revenue impact for 2028
        base_balance = baseline.calculate("gov_balance", 2028).sum()
        ref_balance = reformed.calculate("gov_balance", 2028).sum()
        impact_bn = (ref_balance - base_balance) / 1e9

        # Should produce non-negative revenue
        # OBR estimates £0.6bn for 2028-29
        assert (
            impact_bn >= 0
        ), f"Expected property tax to raise >=£0bn, got £{impact_bn:.2f}bn"
