import { useState, useEffect } from "react";
import PolicySelector from "./components/PolicySelector";
import BudgetaryImpactChart from "./components/BudgetaryImpactChart";
import DistributionalChart from "./components/DistributionalChart";
import WaterfallChart from "./components/WaterfallChart";
import ConstituencyMap from "./components/ConstituencyMap";
import EmploymentIncomeChart from "./components/EmploymentIncomeChart";
import EmploymentIncomeDiffChart from "./components/EmploymentIncomeDiffChart";
import HouseholdChart from "./components/HouseholdChart";
import OBRComparisonTable from "./components/OBRComparisonTable";
import "./App.css";

// Policy definitions - only policies announced in the November 2025 Autumn Budget
// Note: NICs on salary-sacrificed pensions is excluded pending data calibration
// See: https://github.com/PolicyEngine/policyengine-uk-data/issues/215
const DEFAULT_POLICIES = [
  {
    id: "two_child_limit",
    name: "2 child limit repeal",
    description: "Repeal the two-child limit on benefits",
    explanation:
      "The two-child limit restricts Universal Credit and Child Tax Credit payments to a maximum number of children per family. Removing this limit allows families to claim child-related benefit payments for all children without a cap. The Government estimates this will reduce child poverty by 450,000 by 2029-30.",
  },
  {
    id: "threshold_freeze_extension",
    name: "Threshold freeze extension",
    description: "Extend the freeze on income tax thresholds to 2030-31",
    explanation:
      "This policy extends the freeze on income tax thresholds from 2027-28 to 2030-31. The personal allowance remains frozen at £12,570, the higher-rate threshold at £50,270, and the additional-rate threshold at £125,140. The NICs secondary threshold is also frozen. By 2030-31, the OBR estimates this will bring 5.2 million additional individuals into paying income tax.",
  },
  {
    id: "fuel_duty_freeze",
    name: "Fuel duty freeze extension",
    description: "Freeze fuel duty rates until September 2026",
    explanation:
      "The baseline assumes the 5p cut ends on 22 March 2026, returning the rate to 57.95p, followed by RPI uprating from April 2026. The announced policy (reform) maintains the freeze at 52.95p until September 2026, then implements a staggered reversal with increases of 1p, 2p, and 2p over three-month periods, reaching 57.95p by March 2027. Both then apply annual RPI uprating. See our <a href=\"https://policyengine.org/uk/research/fuel-duty-freeze-2025\" target=\"_blank\" rel=\"noopener noreferrer\">research report</a> for details.",
  },
];

// Preset policy combinations
const PRESETS = [
  {
    id: "autumn-budget",
    name: "Autumn Budget 2025",
    policies: DEFAULT_POLICIES.map((p) => p.id),
  },
];

function parseCSV(csvText) {
  const lines = csvText.trim().split("\n");
  const headers = lines[0].split(",");
  const data = [];
  for (let i = 1; i < lines.length; i++) {
    const values = lines[i].split(",");
    const row = {};
    headers.forEach((header, idx) => {
      row[header] = values[idx];
    });
    data.push(row);
  }
  return data;
}

function App() {
  const [selectedPolicies, setSelectedPolicies] = useState(
    DEFAULT_POLICIES.map((p) => p.id),
  );
  const [selectedYear, setSelectedYear] = useState(2026);
  const [results, setResults] = useState(null);
  const [showPolicyDetails, setShowPolicyDetails] = useState(false);

  // Valid policy IDs from DEFAULT_POLICIES
  const validPolicyIds = DEFAULT_POLICIES.map((p) => p.id);

  // Initialize from URL
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const policiesParam = params.get("policies");

    if (policiesParam) {
      // Filter to only include valid policy IDs
      const policies = policiesParam
        .split(",")
        .filter((id) => validPolicyIds.includes(id));
      setSelectedPolicies(policies);
    }
  }, []);

  // Update URL when policies change
  useEffect(() => {
    if (selectedPolicies.length === 0) {
      window.history.replaceState({}, "", window.location.pathname);
    } else {
      const params = new URLSearchParams();
      params.set("policies", selectedPolicies.join(","));
      window.history.replaceState({}, "", `?${params.toString()}`);
    }
  }, [selectedPolicies]);

  // Run analysis when policies or year change
  useEffect(() => {
    if (selectedPolicies.length === 0) {
      setResults(null);
      return;
    }

    runAnalysis();
  }, [selectedPolicies, selectedYear]);

  const runAnalysis = async () => {
    try {
      // Fetch all CSVs in parallel
      const [
        budgetaryRes,
        distributionalRes,
        winnersLosersRes,
        metricsRes,
        householdScatterRes,
      ] = await Promise.all([
        fetch("/data/budgetary_impact.csv"),
        fetch("/data/distributional_impact.csv"),
        fetch("/data/winners_losers.csv"),
        fetch("/data/metrics.csv"),
        fetch("/data/household_scatter.csv"),
      ]);

      const budgetaryData = parseCSV(await budgetaryRes.text());
      const distributionalData = parseCSV(await distributionalRes.text());
      const winnersLosersData = parseCSV(await winnersLosersRes.text());
      const metricsData = parseCSV(await metricsRes.text());
      const householdScatterData = parseCSV(await householdScatterRes.text());

      // Filter data for selected policies
      const filteredBudgetary = budgetaryData.filter((row) =>
        selectedPolicies.includes(row.reform_id),
      );
      const filteredDistributional = distributionalData.filter((row) =>
        selectedPolicies.includes(row.reform_id),
      );
      const filteredWinnersLosers = winnersLosersData.filter((row) =>
        selectedPolicies.includes(row.reform_id),
      );
      const filteredMetrics = metricsData.filter((row) =>
        selectedPolicies.includes(row.reform_id),
      );
      // Keep raw household scatter data (filtering will be done by component)
      const filteredHouseholdScatter = householdScatterData.filter((row) =>
        selectedPolicies.includes(row.reform_id),
      );

      // Build budgetary impact data for chart (2026-2029)
      // Always include all policy keys for smooth animations
      const years = [2026, 2027, 2028, 2029];
      const budgetData = years.map((year) => {
        const dataPoint = { year };
        let netImpact = 0;
        DEFAULT_POLICIES.forEach((policy) => {
          const isSelected = selectedPolicies.includes(policy.id);
          const dataRow = budgetaryData.find(
            (row) => row.reform_id === policy.id && parseInt(row.year) === year,
          );
          const value = isSelected && dataRow ? parseFloat(dataRow.value) : 0;
          dataPoint[policy.name] = value;
          netImpact += value;
        });
        dataPoint.netImpact = netImpact;
        return dataPoint;
      });

      // Calculate budgetary impact for 2026 (metrics always show 2026)
      const budgetaryImpact2026 = filteredBudgetary
        .filter((row) => parseInt(row.year) === 2026)
        .reduce((sum, row) => sum + parseFloat(row.value), 0);

      // Build distributional data (grouped by decile with policy breakdown)
      // Always include all policy keys for smooth animations
      const decileOrder = [
        "1st",
        "2nd",
        "3rd",
        "4th",
        "5th",
        "6th",
        "7th",
        "8th",
        "9th",
        "10th",
      ];
      const distributionalSelectedYear = distributionalData.filter(
        (row) => parseInt(row.year) === selectedYear,
      );
      const distributionalChartData = decileOrder.map((decile) => {
        const dataPoint = { decile };
        let netChange = 0;
        DEFAULT_POLICIES.forEach((policy) => {
          const isSelected = selectedPolicies.includes(policy.id);
          const dataRow = distributionalSelectedYear.find(
            (row) => row.reform_id === policy.id && row.decile === decile,
          );
          const value = isSelected && dataRow ? parseFloat(dataRow.value) : 0;
          dataPoint[policy.name] = value;
          netChange += value;
        });
        dataPoint.netChange = netChange;
        return dataPoint;
      });

      // Build waterfall data (grouped by decile with policy breakdown)
      // Always include all policy keys for smooth animations
      const waterfallSelectedYear = winnersLosersData.filter(
        (row) => parseInt(row.year) === selectedYear && row.decile !== "all",
      );
      const waterfallDeciles = [
        "1",
        "2",
        "3",
        "4",
        "5",
        "6",
        "7",
        "8",
        "9",
        "10",
      ];
      const waterfallData = waterfallDeciles.map((decile) => {
        const dataPoint = { decile };
        let netChange = 0;
        DEFAULT_POLICIES.forEach((policy) => {
          const isSelected = selectedPolicies.includes(policy.id);
          const dataRow = waterfallSelectedYear.find(
            (row) => row.reform_id === policy.id && row.decile === decile,
          );
          const value =
            isSelected && dataRow ? parseFloat(dataRow.avg_change) : 0;
          dataPoint[policy.name] = value;
          netChange += value;
        });
        dataPoint.netChange = netChange;
        return dataPoint;
      });

      // Extract metrics for 2026 (metrics always show 2026)
      const metrics2026 = filteredMetrics.find(
        (row) => parseInt(row.year) === 2026,
      );
      const percentAffected = metrics2026
        ? parseFloat(metrics2026.people_affected)
        : null;
      const giniChange = metrics2026
        ? parseFloat(metrics2026.gini_change)
        : null;
      const povertyRateChange = metrics2026
        ? parseFloat(metrics2026.poverty_change_pp)
        : null;

      // Calculate total revenue over budget window (2026-2029)
      const budgetWindowRevenue = filteredBudgetary.reduce(
        (sum, row) => sum + parseFloat(row.value),
        0,
      );

      setResults({
        metrics: {
          budgetaryImpact2026,
          budgetWindowRevenue,
          percentAffected,
          giniChange,
          povertyRateChange,
        },
        budgetData,
        distributionalData:
          distributionalChartData.length > 0 ? distributionalChartData : null,
        waterfallData: waterfallData.length > 0 ? waterfallData : null,
        householdScatterData:
          filteredHouseholdScatter.length > 0 ? filteredHouseholdScatter : null,
        rawDistributional: filteredDistributional,
        rawWinnersLosers: filteredWinnersLosers,
        rawHouseholdScatter: filteredHouseholdScatter,
      });
    } catch (error) {
      console.error("Error loading results:", error);
      setResults(null);
    }
  };

  const handlePolicyToggle = (policyId) => {
    setSelectedPolicies((prev) => {
      if (prev.includes(policyId)) {
        return prev.filter((id) => id !== policyId);
      } else {
        return [...prev, policyId];
      }
    });
  };

  const handlePresetClick = (presetPolicies) => {
    setSelectedPolicies(presetPolicies);
  };

  return (
    <div className="app">
      <main className="main-content">
        {/* Title row with controls */}
        <div className="title-row">
          <h1>UK Autumn Budget 2025</h1>
          <PolicySelector
            policies={DEFAULT_POLICIES}
            selectedPolicies={selectedPolicies}
            onPolicyToggle={handlePolicyToggle}
          />
        </div>

        {/* Dashboard description */}
        <p className="dashboard-intro">
          Explore the fiscal and distributional impacts of potential UK budget
          policies. Select policies to see how they affect government revenue,
          household incomes, and inequality across income groups.{" "}
          {selectedPolicies.length > 0 && (
            <a
              href="#policy-details"
              onClick={(e) => {
                e.preventDefault();
                setShowPolicyDetails(true);
                document
                  .getElementById("policy-details")
                  ?.scrollIntoView({ behavior: "smooth" });
              }}
            >
              See policy descriptions below.
            </a>
          )}
        </p>

        {selectedPolicies.length === 0 ? (
          <div className="empty-state">
            <p>
              Select policies to analyse their impact on government revenue and
              household incomes.
            </p>
            <div className="preset-buttons">
              {PRESETS.map((preset) => (
                <button
                  key={preset.id}
                  className="preset-button"
                  onClick={() => handlePresetClick(preset.policies)}
                >
                  {preset.name}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="results-container">
            {results && (
              <>
                {/* Hero Chart: Revenue Impact */}
                <div className="hero-chart">
                  <BudgetaryImpactChart data={results.budgetData} />
                </div>

                {/* Row 1: Absolute and Relative Impact */}
                <div className="charts-grid">
                  <WaterfallChart
                    rawData={results.rawWinnersLosers}
                    selectedPolicies={selectedPolicies}
                  />
                  <DistributionalChart
                    rawData={results.rawDistributional}
                    selectedPolicies={selectedPolicies}
                  />
                </div>

                {/* Row 2: Constituency Map and Scatter */}
                <div className="charts-grid charts-row-2">
                  <ConstituencyMap selectedPolicies={selectedPolicies} />
                  {results.rawHouseholdScatter && (
                    <HouseholdChart
                      rawData={results.rawHouseholdScatter}
                      selectedPolicies={selectedPolicies}
                    />
                  )}
                </div>

                {/* Row 3: Net Income Analysis Charts */}
                <div className="charts-grid charts-row-3">
                  <EmploymentIncomeChart
                    selectedPolicies={selectedPolicies}
                    selectedYear={2026}
                  />
                  <EmploymentIncomeDiffChart
                    selectedPolicies={selectedPolicies}
                    selectedYear={2026}
                  />
                </div>

                {/* OBR Comparison Table */}
                <OBRComparisonTable selectedPolicies={selectedPolicies} />

                {/* Policy Details Footer */}
                <div id="policy-details" className="policy-details-footer">
                  <button
                    className="policy-details-toggle"
                    onClick={() => setShowPolicyDetails(!showPolicyDetails)}
                  >
                    <svg
                      width="16"
                      height="16"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    >
                      <circle cx="12" cy="12" r="10"></circle>
                      <line x1="12" y1="16" x2="12" y2="12"></line>
                      <line x1="12" y1="8" x2="12.01" y2="8"></line>
                    </svg>
                    About selected policies
                    <svg
                      width="16"
                      height="16"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      style={{
                        transform: showPolicyDetails
                          ? "rotate(180deg)"
                          : "rotate(0deg)",
                        transition: "transform 0.2s",
                      }}
                    >
                      <polyline points="6 9 12 15 18 9"></polyline>
                    </svg>
                  </button>
                  {showPolicyDetails && (
                    <div className="policy-details-content">
                      {DEFAULT_POLICIES.filter((policy) =>
                        selectedPolicies.includes(policy.id),
                      ).map((policy) => (
                        <div key={policy.id} className="policy-detail">
                          <strong>{policy.name}:</strong>{" "}
                          <span
                            dangerouslySetInnerHTML={{
                              __html: policy.explanation,
                            }}
                          />
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </>
            )}
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
