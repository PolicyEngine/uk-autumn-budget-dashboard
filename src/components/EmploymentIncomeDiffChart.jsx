import { useState, useEffect, useRef } from "react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
  Customized,
} from "recharts";
import { PolicyEngineLogo, CHART_LOGO } from "../utils/chartLogo";
import { exportChartAsSvg } from "../utils/exportChartAsSvg";
import "./EmploymentIncomeDiffChart.css";
import "./ChartExport.css";

// Chart metadata for export
const CHART_TITLE = "Net income change";
const CHART_DESCRIPTION =
  "This chart shows the change in household net income (reform minus baseline) for the same household scenario. Green indicates gains, red indicates losses.";

// Legend items for export
const LEGEND_ITEMS = [
  { color: "#319795", label: "Gain", type: "rect" },
  { color: "#E53E3E", label: "Loss", type: "rect" },
];

function EmploymentIncomeDiffChart({ selectedPolicies, selectedYear = 2026 }) {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const chartRef = useRef(null);

  const handleExportSvg = async () => {
    await exportChartAsSvg(chartRef, "net-income-change", {
      title: CHART_TITLE,
      description: CHART_DESCRIPTION,
      legendItems: LEGEND_ITEMS,
      logo: CHART_LOGO,
    });
  };

  useEffect(() => {
    // Load income curve data from CSV
    fetch("/data/income_curve.csv")
      .then((response) => response.text())
      .then((csvText) => {
        const lines = csvText.trim().split("\n");
        const headers = lines[0].split(",");

        // Parse all income curve data
        const allData = [];
        for (let i = 1; i < lines.length; i++) {
          const values = lines[i].split(",");
          const row = {};
          headers.forEach((header, index) => {
            row[header] = values[index];
          });
          allData.push(row);
        }

        // Filter by selected year
        const yearFilteredData = allData.filter(
          (row) => parseInt(row.year) === selectedYear,
        );

        // Get unique employment income values (up to 100k)
        const employmentIncomes = [
          ...new Set(
            yearFilteredData
              .filter((row) => parseFloat(row.employment_income) <= 100000)
              .map((row) => parseFloat(row.employment_income)),
          ),
        ].sort((a, b) => a - b);

        // Build chart data: for each employment income, compute the difference
        const chartData = employmentIncomes.map((income) => {
          // Get baseline from any row (it's the same across reforms)
          const baselineRow = yearFilteredData.find(
            (row) => parseFloat(row.employment_income) === income,
          );
          const baseline = baselineRow
            ? parseFloat(baselineRow.baseline_net_income)
            : 0;

          // Sum up the income changes from each selected policy
          let totalIncomeChange = 0;
          selectedPolicies.forEach((policyId) => {
            const policyRow = yearFilteredData.find(
              (row) =>
                row.reform_id === policyId &&
                parseFloat(row.employment_income) === income,
            );
            if (policyRow) {
              const reformIncome = parseFloat(policyRow.reform_net_income);
              const baselineIncome = parseFloat(policyRow.baseline_net_income);
              totalIncomeChange += reformIncome - baselineIncome;
            }
          });

          return {
            employment: income,
            difference: totalIncomeChange,
            positive: totalIncomeChange >= 0 ? totalIncomeChange : null,
            negative: totalIncomeChange <= 0 ? totalIncomeChange : null,
          };
        });

        setData(chartData);
        setLoading(false);
      })
      .catch((error) => {
        console.error("Error loading income curve data:", error);
        setLoading(false);
      });
  }, [selectedPolicies, selectedYear]);

  const formatCurrency = (value) => {
    const absVal = Math.abs(value);
    if (absVal >= 1000) {
      const formatted = `£${(absVal / 1000).toFixed(0)}k`;
      return value < 0 ? `-${formatted}` : formatted;
    }
    const formatted = `£${absVal.toFixed(0)}`;
    return value < 0 ? `-${formatted}` : formatted;
  };

  if (loading) {
    return (
      <div className="employment-income-diff-chart">
        <h2>Net income change</h2>
        <p className="chart-description">
          This chart shows the change in household net income under the reform.
        </p>
        <div style={{ textAlign: "center", padding: "40px", color: "#666" }}>
          Loading income curve data...
        </div>
      </div>
    );
  }

  // Calculate symmetric y-axis domain
  const maxAbs = Math.max(...data.map((d) => Math.abs(d.difference)));
  const yMax = Math.ceil(maxAbs / 1000) * 1000 || 1000;

  // Check if there are any gains or losses to determine what to show
  const hasGains = data.some((d) => d.positive !== null && d.positive > 0);
  const hasLosses = data.some((d) => d.negative !== null && d.negative < 0);

  // Legend always shows both items
  const legendPayload = [
    { value: "Gain", type: "square", color: "#319795" },
    { value: "Loss", type: "square", color: "#E53E3E" },
  ];

  return (
    <div className="employment-income-diff-chart">
      <div className="chart-header">
        <div>
          <h2>Net income change</h2>
          <p className="chart-description">
            This chart shows the change in household net income (reform minus
            baseline) for the same household scenario. Green indicates gains,
            red indicates losses.
          </p>
        </div>
        <button
          className="export-button"
          onClick={handleExportSvg}
          title="Download as SVG"
          aria-label="Download chart as SVG"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
            <polyline points="7 10 12 15 17 10" />
            <line x1="12" y1="15" x2="12" y2="3" />
          </svg>
        </button>
      </div>

      <div ref={chartRef}>
        <ResponsiveContainer width="100%" height={430}>
          <AreaChart
            data={data}
            margin={{ top: 25, right: 30, left: 20, bottom: 60 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis
              dataKey="employment"
              type="number"
              label={{
                value: "Household head employment income",
                position: "insideBottom",
                offset: -5,
                style: {
                  textAnchor: "middle",
                  fill: "#374151",
                  fontSize: 13,
                  fontWeight: 500,
                },
              }}
              tickFormatter={formatCurrency}
              tick={{ fontSize: 12, fill: "#6b7280" }}
              height={60}
              ticks={[0, 20000, 40000, 60000, 80000, 100000]}
              domain={[0, 100000]}
            />
            <YAxis
              label={{
                value: "Change in net income",
                angle: -90,
                position: "insideLeft",
                dx: 10,
                style: {
                  textAnchor: "middle",
                  fill: "#374151",
                  fontSize: 13,
                  fontWeight: 500,
                },
              }}
              tickFormatter={formatCurrency}
              tick={{ fontSize: 12, fill: "#6b7280" }}
              width={80}
              domain={[-yMax, yMax]}
            />
            <Tooltip
              formatter={(value, name) => [
                formatCurrency(value),
                "Income change",
              ]}
              labelFormatter={(label) =>
                `Employment income: ${formatCurrency(label)}`
              }
              contentStyle={{
                background: "white",
                border: "1px solid #d1d5db",
                borderRadius: "8px",
                padding: "12px",
                boxShadow: "0 4px 6px -1px rgba(0, 0, 0, 0.1)",
              }}
              labelStyle={{ fontWeight: 600, marginBottom: "4px" }}
            />
            <Legend
              wrapperStyle={{
                paddingTop: "15px",
                paddingBottom: "0px",
                paddingRight: "140px",
              }}
              iconType="square"
              iconSize={14}
              formatter={(value) => (
                <span
                  style={{
                    fontSize: "13px",
                    fontWeight: 500,
                    color: "#374151",
                  }}
                >
                  {value}
                </span>
              )}
              verticalAlign="bottom"
              align="center"
              payload={legendPayload}
            />
            <ReferenceLine y={0} stroke="#374151" strokeWidth={1} />
            {hasGains && (
              <Area
                type="monotone"
                dataKey="positive"
                stroke="#319795"
                strokeWidth={2}
                fill="#319795"
                fillOpacity={0.6}
                baseValue={0}
                connectNulls={false}
                animationDuration={500}
                animationBegin={0}
              />
            )}
            {hasLosses && (
              <Area
                type="monotone"
                dataKey="negative"
                stroke="#E53E3E"
                strokeWidth={2}
                fill="#E53E3E"
                fillOpacity={0.6}
                baseValue={0}
                connectNulls={false}
                animationDuration={500}
                animationBegin={0}
              />
            )}
            <Customized component={PolicyEngineLogo} />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export default EmploymentIncomeDiffChart;
