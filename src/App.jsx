import { useState, useEffect } from "react";
import PolicySelector from "./components/PolicySelector";
import BudgetaryImpactChart from "./components/BudgetaryImpactChart";
import DistributionalChart from "./components/DistributionalChart";
import WaterfallChart from "./components/WaterfallChart";
import ConstituencyMap from "./components/ConstituencyMap";
import EmploymentIncomeChart from "./components/EmploymentIncomeChart";
import EmploymentIncomeDiffChart from "./components/EmploymentIncomeDiffChart";
import HouseholdChart from "./components/HouseholdChart";
import "./App.css";

// Policy definitions
const DEFAULT_POLICIES = [
  {
    id: "two_child_limit",
    name: "2 child limit repeal",
    description: "Repeal the two-child limit on benefits",
    explanation:
      "The two-child limit restricts Universal Credit and Child Tax Credit payments to a maximum number of children per family. Removing this limit would allow families to claim child-related benefit payments for all children without a cap.",
  },
  {
    id: "income_tax_increase_2pp",
    name: "Income tax increase (basic and higher +2pp)",
    description: "Raise basic and higher rates by 2 pp",
    explanation:
      "This policy increases the basic income tax rate from 20% to 22% and the higher rate from 40% to 42%. Income tax applies to taxable income after pension contributions and other deductions.",
  },
  {
    id: "threshold_freeze_extension",
    name: "Threshold freeze extension",
    description: "Extend the freeze on income tax thresholds",
    explanation:
      "This policy extends the freeze on income tax thresholds to 2029-30. Current law already freezes the personal allowance and higher rate threshold until 2027-28. This policy would maintain these thresholds at their current nominal levels for an additional two years.",
  },
  {
    id: "ni_rate_reduction",
    name: "National Insurance rate reduction",
    description: "Reduce the main NI rate for employees",
    explanation:
      "This policy reduces the main employee National Insurance contribution rate from 8% to 6%. National Insurance applies to gross earnings before pension contributions, unlike income tax which applies after deductions.",
  },
  {
    id: "zero_vat_energy",
    name: "Zero-rate VAT on domestic energy",
    description: "Remove 5% VAT from energy bills",
    explanation:
      "This policy removes the 5% VAT currently charged on domestic energy bills. Currently, UK households pay VAT at a reduced rate of 5% on electricity and gas consumption.",
  },
  {
    id: "salary_sacrifice_cap",
    name: "Salary sacrifice cap",
    description: "Cap salary sacrifice at £2,000/year",
    explanation:
      "This policy limits the amount that employees can sacrifice from their salaries into pension contributions without paying national insurance to £2,000 per year. Contributions above this cap would be subject to national insurance.",
  },
  {
    id: "fuel_duty_freeze",
    name: "Fuel duty freeze",
    description: "Extend fuel duty freeze for two years",
    explanation:
      "This policy extends the fuel duty freeze to maintain the rate at 52.95p per litre for petrol and diesel through 2027-28. Current law includes a temporary 5p cut introduced in 2022. This policy continues that reduced rate for an additional two years before it would revert to the standard rate.",
  },
];

// Preset policy combinations
const PRESETS = [
  {
    id: "revenue-neutral",
    name: "Revenue-neutral",
    policies: ["ni_rate_reduction", "income_tax_increase_2pp"],
  },
  {
    id: "progressive",
    name: "Progressive",
    policies: [
      "two_child_limit",
      "income_tax_increase_2pp",
      "threshold_freeze_extension",
    ],
  },
  {
    id: "all",
    name: "All policies",
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
  const [selectedPolicies, setSelectedPolicies] = useState([]);
  const [selectedYear, setSelectedYear] = useState(2026);
  const [results, setResults] = useState(null);
  const [showPolicyDetails, setShowPolicyDetails] = useState(false);

  // Initialize from URL
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const policiesParam = params.get("policies");

    if (policiesParam) {
      const policies = policiesParam.split(",");
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

      // Calculate fiscal headroom for 2029/30
      const budgetaryImpact2029 = filteredBudgetary
        .filter((row) => parseInt(row.year) === 2029)
        .reduce((sum, row) => sum + parseFloat(row.value), 0);
      const obrBaselineHeadroom = 9.9;
      const fiscalHeadroom2029 = obrBaselineHeadroom + budgetaryImpact2029;

      // Calculate total revenue over budget window (2026-2029)
      const budgetWindowRevenue = filteredBudgetary.reduce(
        (sum, row) => sum + parseFloat(row.value),
        0,
      );

      setResults({
        metrics: {
          fiscalHeadroom2029,
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
          household incomes, and inequality across income groups.
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
                {/* Key Metrics Row - Above Hero Chart */}
                <div className="key-metrics-row">
                  <div className="key-metric highlighted">
                    <div className="metric-label">
                      Fiscal headroom 2029-30
                      <span className="info-icon-wrapper">
                        <svg
                          className="info-icon"
                          width="14"
                          height="14"
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
                        <span className="info-tooltip">
                          The gap between forecast fiscal position and the
                          Government's fiscal rule breach point. Based on OBR
                          baseline of £9.9bn.
                        </span>
                      </span>
                    </div>
                    <div className="metric-number">
                      {results.metrics.fiscalHeadroom2029 !== null
                        ? `£${results.metrics.fiscalHeadroom2029.toFixed(1)}bn`
                        : "—"}
                    </div>
                  </div>
                  <div className="key-metric">
                    <div className="metric-label">
                      Budget window revenue
                      <span className="info-icon-wrapper">
                        <svg
                          className="info-icon"
                          width="14"
                          height="14"
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
                        <span className="info-tooltip">
                          Total net revenue impact over the four-year budget
                          window (2026-2029). Positive values indicate net
                          revenue raised; negative values indicate net cost to
                          the Exchequer.
                        </span>
                      </span>
                    </div>
                    <div className="metric-number">
                      {results.metrics.budgetWindowRevenue !== null
                        ? `${results.metrics.budgetWindowRevenue >= 0 ? "" : "-"}£${Math.abs(results.metrics.budgetWindowRevenue).toFixed(1)}bn`
                        : "—"}
                    </div>
                  </div>
                </div>

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

                {/* Policy Details Footer */}
                <div className="policy-details-footer">
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
                          <strong>{policy.name}:</strong> {policy.explanation}
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
