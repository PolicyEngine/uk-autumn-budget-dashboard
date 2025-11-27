"""Tests for reform definitions."""

import numpy as np
from policyengine_uk.system import system


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
