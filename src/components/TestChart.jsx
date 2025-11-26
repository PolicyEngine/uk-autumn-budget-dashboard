import { useRef } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Customized,
} from "recharts";
import { exportChartAsSvg } from "../utils/exportChartAsSvg";
import "./TestChart.css";

import { PolicyEngineLogo, CHART_LOGO } from "../utils/chartLogo";

// Sample data for the test chart
const sampleData = [
  { year: 2025, revenue: 2.3, expenditure: 1.8 },
  { year: 2026, revenue: 3.1, expenditure: 2.4 },
  { year: 2027, revenue: 3.8, expenditure: 2.9 },
  { year: 2028, revenue: 4.2, expenditure: 3.2 },
  { year: 2029, revenue: 4.7, expenditure: 3.6 },
];

// Chart metadata for export
const CHART_TITLE = "Test chart for SVG export";
const CHART_DESCRIPTION =
  "This is a sample chart to demonstrate SVG export functionality. The exported SVG includes the title, description, legend, and all chart styling.";

// Legend items matching the Bar components below
const LEGEND_ITEMS = [
  { color: "#319795", label: "Revenue", type: "rect" },
  { color: "#5A8FB8", label: "Expenditure", type: "rect" },
];

function TestChart() {
  const chartRef = useRef(null);

  const handleExportSvg = async () => {
    const success = await exportChartAsSvg(chartRef, "test-chart-export", {
      title: CHART_TITLE,
      description: CHART_DESCRIPTION,
      legendItems: LEGEND_ITEMS,
      logo: CHART_LOGO,
    });
    if (!success) {
      console.error("Failed to export chart as SVG");
    }
  };

  const formatCurrency = (value) => `£${value.toFixed(1)}bn`;

  return (
    <div className="test-chart">
      <div className="test-chart-header">
        <div>
          <h2>{CHART_TITLE}</h2>
          <p className="chart-description">{CHART_DESCRIPTION}</p>
        </div>
        <button
          className="export-svg-button"
          onClick={handleExportSvg}
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
          Download SVG
        </button>
      </div>

      <div ref={chartRef}>
        <ResponsiveContainer width="100%" height={350}>
          <BarChart
            data={sampleData}
            margin={{ top: 20, right: 30, left: 90, bottom: 20 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
            <XAxis dataKey="year" tick={{ fontSize: 11, fill: "#666" }} />
            <YAxis
              label={{
                value: "Impact (£bn)",
                angle: -90,
                position: "insideLeft",
                dx: -30,
                style: {
                  textAnchor: "middle",
                  fill: "#374151",
                  fontSize: 12,
                  fontWeight: 500,
                },
              }}
              tickFormatter={formatCurrency}
              tick={{ fontSize: 11, fill: "#666" }}
            />
            <Tooltip
              formatter={(value) => formatCurrency(value)}
              labelFormatter={(label) => `Year: ${label}`}
              contentStyle={{
                background: "white",
                border: "1px solid #e5e7eb",
                borderRadius: "6px",
              }}
            />
            <Legend wrapperStyle={{ paddingTop: "20px" }} />
            <Bar dataKey="revenue" fill="#319795" name="Revenue" />
            <Bar dataKey="expenditure" fill="#5A8FB8" name="Expenditure" />
            <Customized component={PolicyEngineLogo} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export default TestChart;
