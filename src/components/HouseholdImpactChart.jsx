import { useState } from "react";
import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  ResponsiveContainer,
  ReferenceLine,
  Label,
} from "recharts";
import "./HouseholdImpactChart.css";

function HouseholdImpactChart({ selectedPolicy }) {
  // User selections
  const [income, setIncome] = useState("75k-100k");
  const [filingStatus, setFilingStatus] = useState("married");
  const [children, setChildren] = useState("2");
  const [standardDeduction, setStandardDeduction] = useState("yes");
  const [highTaxState, setHighTaxState] = useState("no");

  // Expandable state for each question
  const [expandedQuestion, setExpandedQuestion] = useState(null);

  // Placeholder: calculated impact based on user selections
  const calculatedImpact = 380; // This will be dynamic later

  // Income ranges
  const incomeRanges = [
    { value: "<25k", label: "Less than £25k" },
    { value: "25k-75k", label: "£25k to £75k" },
    { value: "75k-100k", label: "£75k to £100k" },
    { value: "100k-150k", label: "£100k to £150k" },
    { value: "150k-200k", label: "£150k to £200k" },
    { value: "200k-350k", label: "£200k to £350k" },
    { value: "350k-750k", label: "£350k to £750k" },
    { value: "750k+", label: "£750k+" },
  ];

  const toggleQuestion = (questionId) => {
    setExpandedQuestion(expandedQuestion === questionId ? null : questionId);
  };

  const getSelectedLabel = (type) => {
    switch (type) {
      case "income":
        return incomeRanges.find((r) => r.value === income)?.label || income;
      case "filing":
        return filingStatus === "single"
          ? "Single"
          : filingStatus === "head"
            ? "Head of household"
            : "Married";
      case "children":
        return children === "0"
          ? "No children"
          : children === "1"
            ? "1 child"
            : children === "2"
              ? "2 children"
              : "3+ children";
      case "deduction":
        return standardDeduction === "yes" ? "Yes" : "No";
      case "tax":
        return highTaxState === "yes" ? "Yes" : "No";
      default:
        return "";
    }
  };

  return (
    <div className="household-impact-chart">
      <div className="household-header">
        <div className="household-title">
          <h2>£{calculatedImpact} tax cut</h2>
          <p className="household-subtitle">
            (Between £0 and £1,300 for most households like these in 2025.)
          </p>
        </div>
      </div>

      {/* Chart Container */}
      <div className="household-chart-container">
        <div className="chart-labels-top">
          <span className="label-italic">
            Each dot represents one household
          </span>
        </div>

        <ResponsiveContainer width="100%" height={700}>
          <ScatterChart margin={{ top: 20, right: 80, left: 40, bottom: 60 }}>
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="#e0e0e0"
              vertical={true}
              horizontal={true}
            />

            {/* X-axis */}
            <XAxis
              type="number"
              dataKey="x"
              domain={[-10000, 10000]}
              ticks={[
                -10000, -8000, -6000, -4000, -2000, 0, 2000, 4000, 6000, 8000,
                10000,
              ]}
              tickFormatter={(value) => `£${Math.abs(value / 1000)}k`}
              tick={{ fontSize: 12, fill: "#666" }}
              axisLine={{ stroke: "#333", strokeWidth: 1 }}
            />

            {/* Y-axis */}
            <YAxis
              type="number"
              dataKey="y"
              scale="log"
              domain={[10000, 500000]}
              ticks={[
                10000, 20000, 30000, 40000, 50000, 60000, 70000, 80000, 90000,
                100000, 200000, 300000, 400000, 500000,
              ]}
              tickFormatter={(value) => {
                if (value >= 100000) return `£${value / 1000}k`;
                return `£${value.toLocaleString("en-GB")}`;
              }}
              orientation="right"
              tick={{ fontSize: 12, fill: "#666" }}
              width={70}
            />

            {/* Center line at x=0 */}
            <ReferenceLine x={0} stroke="#333" strokeWidth={2} />

            {/* Placeholder for dots - will be added later */}
            <Scatter
              name="Tax increases"
              data={[]}
              fill="rgba(184, 135, 90, 0.4)"
            />
            <Scatter name="Tax cuts" data={[]} fill="rgba(49, 151, 149, 0.4)" />
          </ScatterChart>
        </ResponsiveContainer>

        <div className="chart-labels-bottom">
          <div className="label-container">
            <span className="label-left">
              ← Households receiving tax increases
            </span>
            <span className="label-center">Tax change (£)</span>
            <span className="label-right">Households receiving tax cuts →</span>
          </div>
        </div>
      </div>

      {/* Expandable Questions Below Chart */}
      <div className="household-questions-expandable">
        {/* Question 1: Income */}
        <div className="expandable-question">
          <button
            className={`question-toggle ${expandedQuestion === "income" ? "expanded" : ""}`}
            onClick={() => toggleQuestion("income")}
          >
            <span className="question-title">How much money do you make?</span>
            <span className="selected-value">{getSelectedLabel("income")}</span>
            <span className="toggle-icon">
              {expandedQuestion === "income" ? "−" : "+"}
            </span>
          </button>
          {expandedQuestion === "income" && (
            <div className="question-content">
              <p className="question-help">
                Make your best guess at your adjusted gross income (A.G.I.).
                Include wage and salary income as well as taxable income from
                investments, rental properties, business ventures and other
                sources.
              </p>
              <div className="button-grid">
                {incomeRanges.map((range) => (
                  <button
                    key={range.value}
                    className={`option-button ${income === range.value ? "active" : ""}`}
                    onClick={() => setIncome(range.value)}
                  >
                    {range.label}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Question 2: Filing Status */}
        <div className="expandable-question">
          <button
            className={`question-toggle ${expandedQuestion === "filing" ? "expanded" : ""}`}
            onClick={() => toggleQuestion("filing")}
          >
            <span className="question-title">How do you file your taxes?</span>
            <span className="selected-value">{getSelectedLabel("filing")}</span>
            <span className="toggle-icon">
              {expandedQuestion === "filing" ? "−" : "+"}
            </span>
          </button>
          {expandedQuestion === "filing" && (
            <div className="question-content">
              <p className="question-help">
                There are other ways to file, but we'll keep it simple.
              </p>
              <div className="button-grid compact">
                <button
                  className={`option-button ${filingStatus === "single" ? "active" : ""}`}
                  onClick={() => setFilingStatus("single")}
                >
                  Single
                </button>
                <button
                  className={`option-button ${filingStatus === "head" ? "active" : ""}`}
                  onClick={() => setFilingStatus("head")}
                >
                  Head of household
                </button>
                <button
                  className={`option-button ${filingStatus === "married" ? "active" : ""}`}
                  onClick={() => setFilingStatus("married")}
                >
                  Married
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Question 3: Children */}
        <div className="expandable-question">
          <button
            className={`question-toggle ${expandedQuestion === "children" ? "expanded" : ""}`}
            onClick={() => toggleQuestion("children")}
          >
            <span className="question-title">
              Do you have children under age 17 living at home?
            </span>
            <span className="selected-value">
              {getSelectedLabel("children")}
            </span>
            <span className="toggle-icon">
              {expandedQuestion === "children" ? "−" : "+"}
            </span>
          </button>
          {expandedQuestion === "children" && (
            <div className="question-content">
              <p className="question-help">
                New provisions like the expanded child tax credit would lead to
                a bigger tax cut for many families.
              </p>
              <div className="button-grid compact">
                <button
                  className={`option-button ${children === "0" ? "active" : ""}`}
                  onClick={() => setChildren("0")}
                >
                  No children
                </button>
                <button
                  className={`option-button ${children === "1" ? "active" : ""}`}
                  onClick={() => setChildren("1")}
                >
                  1 child
                </button>
                <button
                  className={`option-button ${children === "2" ? "active" : ""}`}
                  onClick={() => setChildren("2")}
                >
                  2 children
                </button>
                <button
                  className={`option-button ${children === "3+" ? "active" : ""}`}
                  onClick={() => setChildren("3+")}
                >
                  3+ children
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Question 4: Standard Deduction */}
        <div className="expandable-question">
          <button
            className={`question-toggle ${expandedQuestion === "deduction" ? "expanded" : ""}`}
            onClick={() => toggleQuestion("deduction")}
          >
            <span className="question-title">
              Did you take the standard deduction this year?
            </span>
            <span className="selected-value">
              {getSelectedLabel("deduction")}
            </span>
            <span className="toggle-icon">
              {expandedQuestion === "deduction" ? "−" : "+"}
            </span>
          </button>
          {expandedQuestion === "deduction" && (
            <div className="question-content">
              <p className="question-help">
                The bill nearly doubles the standard deduction to £12,000 for
                individuals and £24,000 for families. Most people already take
                the standard deduction, but the expansion would lead more people
                to do so.
              </p>
              <div className="button-grid compact">
                <button
                  className={`option-button ${standardDeduction === "yes" ? "active" : ""}`}
                  onClick={() => setStandardDeduction("yes")}
                >
                  Yes
                </button>
                <button
                  className={`option-button ${standardDeduction === "no" ? "active" : ""}`}
                  onClick={() => setStandardDeduction("no")}
                >
                  No
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Question 5: High Tax State */}
        <div className="expandable-question">
          <button
            className={`question-toggle ${expandedQuestion === "tax" ? "expanded" : ""}`}
            onClick={() => toggleQuestion("tax")}
          >
            <span className="question-title">
              Do you live in a high-tax area?
            </span>
            <span className="selected-value">{getSelectedLabel("tax")}</span>
            <span className="toggle-icon">
              {expandedQuestion === "tax" ? "−" : "+"}
            </span>
          </button>
          {expandedQuestion === "tax" && (
            <div className="question-content">
              <p className="question-help">
                High-tax areas include London, South East England, and other
                regions with higher local taxes. The plan may affect these areas
                differently than others.
              </p>
              <div className="button-grid compact">
                <button
                  className={`option-button ${highTaxState === "yes" ? "active" : ""}`}
                  onClick={() => setHighTaxState("yes")}
                >
                  Yes
                </button>
                <button
                  className={`option-button ${highTaxState === "no" ? "active" : ""}`}
                  onClick={() => setHighTaxState("no")}
                >
                  No
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default HouseholdImpactChart;
