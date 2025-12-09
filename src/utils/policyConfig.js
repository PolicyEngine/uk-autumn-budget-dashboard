/**
 * Shared policy configuration for colors and labels across all charts.
 *
 * Color scheme:
 * - Teal/green spectrum: policies that are GOOD for households (costs to treasury)
 * - Amber/orange spectrum: policies that are BAD for households (revenue raisers)
 */

// Policy colors by display name (used in population impact charts)
// Includes all name variations used across different charts
export const POLICY_COLORS = {
  // COSTS to treasury (good for households - teal/green spectrum)
  "2 child limit repeal": "#0D9488", // Teal
  "Fuel duty freeze extension": "#5EEAD4", // Light teal
  "Rail fares freeze": "#10B981", // Emerald
  "Zero-rate VAT on energy": "#14B8A6", // Teal 500

  // REVENUE raisers (bad for households - amber/orange spectrum)
  "Threshold freeze extension": "#D97706", // Amber
  "Dividend tax increase (+2pp)": "#F59E0B", // Yellow-amber
  "Savings income tax increase (+2pp)": "#FBBF24", // Yellow
  "Property income tax increase (+2pp)": "#FCD34D", // Light yellow
  "Salary sacrifice cap": "#B45309", // Dark amber
  "NICs on salary sacrifice (>£2k)": "#B45309", // Alternate name
  "Freeze student loan repayment thresholds": "#92400E", // Amber 800
};

// Policy colors by API key (used in lifecycle calculator and personal impact)
export const POLICY_COLORS_BY_KEY = {
  // COSTS to treasury (good for households - teal/green spectrum)
  two_child_limit: "#0D9488", // Teal
  impact_two_child_limit: "#0D9488",
  fuel_duty_freeze: "#5EEAD4", // Light teal
  impact_fuel_duty_freeze: "#5EEAD4",
  rail_fares_freeze: "#10B981", // Emerald
  impact_rail_fare_freeze: "#10B981",

  // REVENUE raisers (bad for households - amber/orange spectrum)
  threshold_freeze_extension: "#D97706", // Amber
  impact_threshold_freeze: "#D97706",
  dividend_tax_increase_2pp: "#F59E0B", // Yellow-amber
  savings_tax_increase_2pp: "#FBBF24", // Yellow
  property_tax_increase_2pp: "#FCD34D", // Light yellow
  impact_unearned_income_tax: "#F59E0B", // Combines dividend/savings/property
  salary_sacrifice_cap: "#B45309", // Dark amber
  impact_salary_sacrifice_cap: "#B45309",
  freeze_student_loan_thresholds: "#92400E", // Amber 800
  impact_sl_threshold_freeze: "#92400E",
};

// Order: revenue raisers first (positive for gov), then costs (negative for gov)
export const ALL_POLICY_NAMES = [
  // Revenue raisers (positive for gov)
  "Threshold freeze extension",
  "Dividend tax increase (+2pp)",
  "Savings income tax increase (+2pp)",
  "Property income tax increase (+2pp)",
  "Salary sacrifice cap",
  "Freeze student loan repayment thresholds",
  // Costs to treasury (negative for gov)
  "2 child limit repeal",
  "Fuel duty freeze extension",
  "Rail fares freeze",
  "Zero-rate VAT on energy",
];

// Lifecycle calculator reform configuration
// Note: In lifecycle view, we show impact FROM HOUSEHOLD PERSPECTIVE
// (positive = good for household, negative = bad)
export const LIFECYCLE_REFORMS = [
  {
    key: "impact_rail_fare_freeze",
    label: "Rail fare freeze",
    color: POLICY_COLORS_BY_KEY.impact_rail_fare_freeze,
  },
  {
    key: "impact_fuel_duty_freeze",
    label: "Fuel duty freeze",
    color: POLICY_COLORS_BY_KEY.impact_fuel_duty_freeze,
  },
  {
    key: "impact_threshold_freeze",
    label: "Threshold freeze",
    color: POLICY_COLORS_BY_KEY.impact_threshold_freeze,
  },
  {
    key: "impact_unearned_income_tax",
    label: "Unearned income tax",
    color: POLICY_COLORS_BY_KEY.impact_unearned_income_tax,
  },
  {
    key: "impact_salary_sacrifice_cap",
    label: "Salary sacrifice cap",
    color: POLICY_COLORS_BY_KEY.impact_salary_sacrifice_cap,
  },
  {
    key: "impact_sl_threshold_freeze",
    label: "SL threshold freeze",
    color: POLICY_COLORS_BY_KEY.impact_sl_threshold_freeze,
  },
  {
    key: "impact_two_child_limit",
    label: "Two-child limit end",
    color: POLICY_COLORS_BY_KEY.impact_two_child_limit,
  },
];

// Personal impact policy order and colors
export const PERSONAL_IMPACT_POLICY_ORDER = [
  "two_child_limit",
  "fuel_duty_freeze",
  "rail_fares_freeze",
  "threshold_freeze_extension",
  "dividend_tax_increase_2pp",
  "savings_tax_increase_2pp",
  "property_tax_increase_2pp",
  "salary_sacrifice_cap",
];

// Helper to get color by policy key
export function getPolicyColor(key) {
  return POLICY_COLORS_BY_KEY[key] || POLICY_COLORS[key] || "#9CA3AF";
}
