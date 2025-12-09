import { useState, useEffect, useRef, useCallback, useMemo } from "react";
import * as d3 from "d3";
import { LIFECYCLE_REFORMS } from "../utils/policyConfig";
import "./LifecycleCalculator.css";

// API URL - detect local vs production
const getApiUrl = () => {
  const isLocalhost =
    window.location.hostname === "localhost" ||
    window.location.hostname === "127.0.0.1";
  return isLocalhost
    ? "http://localhost:5001"
    : "https://uk-autumn-budget-lifecycle-578039519715.europe-west1.run.app";
};

// Use shared policy configuration
const REFORMS = LIFECYCLE_REFORMS;

// CPI forecasts for real terms conversion
const CPI_FORECASTS = {
  2024: 0.0233,
  2025: 0.0318,
  2026: 0.0193,
  2027: 0.02,
  2028: 0.02,
  2029: 0.02,
};
const CPI_LONG_TERM = 0.02;

// Default input values
const DEFAULT_INPUTS = {
  current_age: 22,
  current_salary: 30000,
  retirement_age: 67,
  life_expectancy: 85,
  student_loan_debt: 45000,
  salary_sacrifice_per_year: 2000,
  rail_spending_per_year: 2000,
  petrol_spending_per_year: 500,
  dividends_per_year: 500,
  savings_interest_per_year: 500,
  property_income_per_year: 0,
  children_ages: "",
};

// Slider configurations
const SLIDER_CONFIGS = [
  {
    id: "current_age",
    label: "Age",
    min: 18,
    max: 80,
    step: 1,
    format: (v) => v.toString(),
  },
  {
    id: "current_salary",
    label: "Salary",
    min: 0,
    max: 200000,
    step: 1000,
    format: (v) => `£${d3.format(",.0f")(v)}`,
    tooltip:
      "Starting salary in graduation year. Grows with age-based earnings trajectory.",
  },
  {
    id: "retirement_age",
    label: "Retirement age",
    min: 55,
    max: 100,
    step: 1,
    format: (v) => v.toString(),
  },
  {
    id: "life_expectancy",
    label: "Life expectancy",
    min: 60,
    max: 100,
    step: 1,
    format: (v) => v.toString(),
  },
  {
    id: "student_loan_debt",
    label: "Student loan debt",
    min: 0,
    max: 100000,
    step: 5000,
    format: (v) => `£${d3.format(",.0f")(v)}`,
    tooltip:
      "Initial debt at graduation. Evolves based on interest and repayments.",
  },
  {
    id: "salary_sacrifice_per_year",
    label: "Salary sacrifice",
    min: 0,
    max: 10000,
    step: 100,
    format: (v) => `£${d3.format(",.0f")(v)}`,
    tooltip:
      "Annual pension contribution via salary sacrifice. Grows with CPI. Cap of £2k from April 2029.",
  },
  {
    id: "rail_spending_per_year",
    label: "Rail spending",
    min: 0,
    max: 10000,
    step: 100,
    format: (v) => `£${d3.format(",.0f")(v)}`,
    tooltip:
      "Annual rail spending (fixed nominal). Policy impact uses RPI fare growth.",
  },
  {
    id: "petrol_spending_per_year",
    label: "Petrol spending",
    min: 0,
    max: 10000,
    step: 100,
    format: (v) => `£${d3.format(",.0f")(v)}`,
    tooltip:
      "Annual petrol spending (fixed nominal). Policy impact uses fuel duty changes.",
  },
  {
    id: "dividends_per_year",
    label: "Dividends",
    min: 0,
    max: 10000,
    step: 100,
    format: (v) => `£${d3.format(",.0f")(v)}`,
    tooltip: "Annual dividend income. Grows with CPI to maintain real value.",
  },
  {
    id: "savings_interest_per_year",
    label: "Savings interest",
    min: 0,
    max: 10000,
    step: 100,
    format: (v) => `£${d3.format(",.0f")(v)}`,
    tooltip:
      "Annual savings interest income. Grows with CPI to maintain real value.",
  },
  {
    id: "property_income_per_year",
    label: "Property income",
    min: 0,
    max: 10000,
    step: 100,
    format: (v) => `£${d3.format(",.0f")(v)}`,
    tooltip:
      "Annual rental/property income. Grows with CPI to maintain real value.",
  },
];

function LifecycleCalculator() {
  const [inputs, setInputs] = useState(DEFAULT_INPUTS);
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showRealTerms, setShowRealTerms] = useState(true);
  const chartRef = useRef(null);
  const tooltipRef = useRef(null);
  const previousDataRef = useRef([]);

  // Calculate cumulative inflation from 2025 to target year
  const getCumulativeInflation = useCallback((targetYear) => {
    if (targetYear <= 2025) return 1.0;
    let factor = 1.0;
    for (let y = 2025; y < targetYear; y++) {
      const rate = CPI_FORECASTS[y] || CPI_LONG_TERM;
      factor *= 1 + rate;
    }
    return factor;
  }, []);

  // Convert nominal value to 2025 real terms
  const toRealTerms = useCallback(
    (value, year) => {
      if (!showRealTerms) return value;
      const inflationFactor = getCumulativeInflation(year);
      return value / inflationFactor;
    },
    [showRealTerms, getCumulativeInflation],
  );

  // Get display data with real terms conversion
  const displayData = useMemo(() => {
    if (!showRealTerms) return data;
    return data.map((row) => {
      const deflator = getCumulativeInflation(row.year);
      const adjusted = { ...row };
      REFORMS.forEach((r) => {
        adjusted[r.key] = row[r.key] / deflator;
      });
      adjusted.gross_income = row.gross_income / deflator;
      adjusted.baseline_net_income = row.baseline_net_income / deflator;
      adjusted.income_tax = row.income_tax / deflator;
      adjusted.national_insurance = row.national_insurance / deflator;
      adjusted.student_loan_payment = row.student_loan_payment / deflator;
      adjusted.student_loan_debt_remaining =
        row.student_loan_debt_remaining / deflator;
      return adjusted;
    });
  }, [data, showRealTerms, getCumulativeInflation]);

  // Calculate summary stats
  const summaryStats = useMemo(() => {
    if (!displayData.length) return { netTotal: 0, avgPerYear: 0 };
    const netTotal = displayData.reduce((sum, row) => {
      return (
        sum + REFORMS.reduce((reformSum, r) => reformSum + (row[r.key] || 0), 0)
      );
    }, 0);
    return {
      netTotal,
      avgPerYear: netTotal / displayData.length,
    };
  }, [displayData]);

  // Parse children ages from string
  const parseChildrenAges = (value) => {
    if (!value || value.trim() === "") return [];
    return value
      .split(",")
      .map((s) => parseInt(s.trim()))
      .filter((n) => !isNaN(n) && n >= 0 && n < 20);
  };

  // Fetch data from API
  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const apiInputs = {
        ...inputs,
        children_ages: parseChildrenAges(inputs.children_ages),
      };

      const response = await fetch(`${getApiUrl()}/calculate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(apiInputs),
      });

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }

      const result = await response.json();
      previousDataRef.current = data;
      setData(result.data);
    } catch (err) {
      console.error("Error fetching data:", err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [inputs, data]);

  // Initial fetch and URL params
  useEffect(() => {
    fetchData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Debounced fetch on input change
  useEffect(() => {
    const timer = setTimeout(() => {
      fetchData();
    }, 150);
    return () => clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [inputs]);

  // Handle input change
  const handleInputChange = (id, value) => {
    setInputs((prev) => ({
      ...prev,
      [id]: id === "children_ages" ? value : parseFloat(value),
    }));
  };

  // Format signed currency
  const formatSignedCurrency = (v) => {
    const absVal = d3.format(",.0f")(Math.abs(v));
    return v >= 0 ? `+£${absVal}` : `-£${absVal}`;
  };

  // Render D3 chart
  useEffect(() => {
    if (!displayData.length || !chartRef.current) return;

    const container = chartRef.current;
    const margin = { top: 20, right: 20, bottom: 40, left: 60 };
    const width = container.clientWidth - margin.left - margin.right;
    const height = 400 - margin.top - margin.bottom;

    // Clear previous chart
    d3.select(container).selectAll("*").remove();

    // Prepare stacked data
    const stackedData = displayData.map((d) => {
      let posY = 0,
        negY = 0;
      const bars = REFORMS.map((r) => {
        const value = d[r.key] || 0;
        const bar = { key: r.key, value, age: d.age, year: d.year };
        if (value >= 0) {
          bar.y0 = posY;
          bar.y1 = posY + value;
          posY += value;
        } else {
          bar.y1 = negY;
          bar.y0 = negY + value;
          negY += value;
        }
        return bar;
      });
      const netImpact = posY + negY;
      return {
        age: d.age,
        year: d.year,
        bars,
        posTotal: posY,
        negTotal: negY,
        netImpact,
        gross_income: d.gross_income,
        income_tax: d.income_tax,
        national_insurance: d.national_insurance,
        student_loan_payment: d.student_loan_payment,
        student_loan_debt_remaining: d.student_loan_debt_remaining,
        baseline_net_income: d.baseline_net_income,
      };
    });

    const yMax = d3.max(stackedData, (d) => d.posTotal);
    const yMin = d3.min(stackedData, (d) => d.negTotal);
    const yExtent = Math.max(Math.abs(yMax), Math.abs(yMin)) * 1.1;

    const x = d3
      .scaleBand()
      .domain(displayData.map((d) => d.age))
      .range([0, width])
      .padding(0.15);

    const y = d3.scaleLinear().domain([-yExtent, yExtent]).range([height, 0]);

    const svg = d3
      .select(container)
      .append("svg")
      .attr("width", width + margin.left + margin.right)
      .attr("height", height + margin.top + margin.bottom);

    const chartG = svg
      .append("g")
      .attr("transform", `translate(${margin.left},${margin.top})`);

    // Grid
    chartG
      .append("g")
      .attr("class", "grid")
      .call(d3.axisLeft(y).tickSize(-width).tickFormat("").ticks(8));

    // Zero line
    chartG
      .append("line")
      .attr("class", "zero-line")
      .attr("x1", 0)
      .attr("x2", width)
      .attr("y1", y(0))
      .attr("y2", y(0))
      .attr("stroke", "#333")
      .attr("stroke-width", 2);

    // Age groups
    const ageGroups = chartG
      .selectAll(".age-group")
      .data(stackedData, (d) => d.age)
      .enter()
      .append("g")
      .attr("class", "age-group")
      .attr("transform", (d) => `translate(${x(d.age)},0)`);

    // Bars
    ageGroups
      .selectAll("rect")
      .data((d) => d.bars)
      .enter()
      .append("rect")
      .attr("x", 0)
      .attr("y", y(0))
      .attr("width", x.bandwidth())
      .attr("height", 0)
      .attr("fill", (d) => REFORMS.find((r) => r.key === d.key).color)
      .attr("rx", 1)
      .transition()
      .duration(400)
      .attr("y", (d) => y(Math.max(d.y0, d.y1)))
      .attr("height", (d) => Math.abs(y(d.y0) - y(d.y1)));

    // X-axis
    chartG
      .append("g")
      .attr("class", "axis x-axis")
      .attr("transform", `translate(0,${height})`)
      .call(
        d3
          .axisBottom(x)
          .tickValues(
            displayData.filter((d) => d.age % 5 === 0).map((d) => d.age),
          ),
      );

    // Y-axis
    chartG
      .append("g")
      .attr("class", "axis y-axis")
      .call(
        d3
          .axisLeft(y)
          .tickFormat((d) => formatSignedCurrency(d))
          .ticks(8),
      );

    // Net impact line
    const line = d3
      .line()
      .x((d) => x(d.age) + x.bandwidth() / 2)
      .y((d) => y(d.netImpact))
      .curve(d3.curveMonotoneX);

    chartG
      .append("path")
      .datum(stackedData)
      .attr("class", "net-line")
      .attr("fill", "none")
      .attr("stroke", "#000000")
      .attr("stroke-width", 2.5)
      .attr("d", line);

    // Tooltip interactions
    const tooltip = d3.select(tooltipRef.current);

    ageGroups
      .on("mouseover", function (event, d) {
        tooltip.style("opacity", 1);
        let html = `<div class="tooltip-title">Age ${d.age} (${d.year})</div>`;

        html += `<div class="tooltip-section">`;
        html += `<div class="tooltip-row"><span class="tooltip-label">Gross income</span><span class="tooltip-value">£${d3.format(",.0f")(d.gross_income)}</span></div>`;
        if (d.income_tax > 0) {
          html += `<div class="tooltip-row"><span class="tooltip-label">Income tax</span><span class="tooltip-value">-£${d3.format(",.0f")(d.income_tax)}</span></div>`;
        }
        if (d.national_insurance > 0) {
          html += `<div class="tooltip-row"><span class="tooltip-label">National insurance</span><span class="tooltip-value">-£${d3.format(",.0f")(d.national_insurance)}</span></div>`;
        }
        if (d.student_loan_payment > 0) {
          html += `<div class="tooltip-row"><span class="tooltip-label">Student loan</span><span class="tooltip-value">-£${d3.format(",.0f")(d.student_loan_payment)}</span></div>`;
        }
        html += `</div>`;

        const activeReforms = d.bars.filter((b) => b.value !== 0);
        if (activeReforms.length > 0) {
          html += `<div class="tooltip-section tooltip-reforms">`;
          activeReforms.forEach((bar) => {
            const reform = REFORMS.find((r) => r.key === bar.key);
            html += `<div class="tooltip-row">
              <span class="tooltip-label">${reform.label}</span>
              <span class="tooltip-value ${bar.value >= 0 ? "positive" : "negative"}">${formatSignedCurrency(bar.value)}</span>
            </div>`;
          });
          html += `</div>`;
        }

        const total = d3.sum(d.bars, (b) => b.value);
        html += `<div class="tooltip-row tooltip-total">
          <span>Net policy impact</span>
          <span class="tooltip-value ${total >= 0 ? "positive" : "negative"}">${formatSignedCurrency(total)}</span>
        </div>`;

        tooltip.html(html);
      })
      .on("mousemove", function (event) {
        tooltip
          .style("left", event.pageX + 10 + "px")
          .style("top", event.pageY - 10 + "px");
      })
      .on("mouseout", function () {
        tooltip.style("opacity", 0);
      });
  }, [displayData, formatSignedCurrency]);

  // Download CSV
  const downloadCSV = () => {
    if (!data.length) return;

    const headers = [
      "age",
      "year",
      "gross_income",
      "income_tax",
      "national_insurance",
      "student_loan_payment",
      "student_loan_debt_remaining",
      "baseline_net_income",
      "impact_rail_fare_freeze",
      "impact_fuel_duty_freeze",
      "impact_threshold_freeze",
      "impact_unearned_income_tax",
      "impact_salary_sacrifice_cap",
      "impact_sl_threshold_freeze",
      "impact_two_child_limit",
      "net_policy_impact",
    ];

    const rows = data.map((row) => {
      const netImpact = REFORMS.reduce((sum, r) => sum + (row[r.key] || 0), 0);
      return [
        row.age,
        row.year,
        row.gross_income,
        row.income_tax,
        row.national_insurance,
        row.student_loan_payment,
        row.student_loan_debt_remaining,
        row.baseline_net_income,
        row.impact_rail_fare_freeze,
        row.impact_fuel_duty_freeze,
        row.impact_threshold_freeze,
        row.impact_unearned_income_tax,
        row.impact_salary_sacrifice_cap,
        row.impact_sl_threshold_freeze,
        row.impact_two_child_limit,
        netImpact,
      ].join(",");
    });

    const csv = [headers.join(","), ...rows].join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);

    const a = document.createElement("a");
    a.href = url;
    a.download = "lifetime-policy-impact.csv";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const childrenCount = parseChildrenAges(inputs.children_ages).length;

  return (
    <div className="lifecycle-calculator">
      <div className="lifecycle-header">
        <div className="lifecycle-header-content">
          <h2>Lifetime policy impact</h2>
          <p className="lifecycle-subtitle">
            Model the impact of UK budget policy reforms over your lifetime
          </p>
        </div>
      </div>

      <div className="lifecycle-layout">
        {/* Controls sidebar */}
        <div className="lifecycle-controls">
          <h3>Household inputs (2025)</h3>

          {SLIDER_CONFIGS.map((config) => (
            <div className="control-group" key={config.id}>
              <label title={config.tooltip}>{config.label}</label>
              <div className="slider-container">
                <input
                  type="range"
                  value={inputs[config.id]}
                  min={config.min}
                  max={config.max}
                  step={config.step}
                  onChange={(e) => handleInputChange(config.id, e.target.value)}
                />
                <span className="slider-value">
                  {config.format(inputs[config.id])}
                </span>
              </div>
            </div>
          ))}

          {/* Children ages input */}
          <div className="control-group">
            <label title="Ages of children in 2025 (comma-separated). Impact from two-child limit abolition.">
              Children ages
            </label>
            <div className="slider-container">
              <input
                type="text"
                value={inputs.children_ages}
                placeholder="e.g. 5, 3, 1"
                className="text-input"
                onChange={(e) =>
                  handleInputChange("children_ages", e.target.value)
                }
              />
              <span className="slider-value children-count">
                {childrenCount === 0
                  ? "0 children"
                  : childrenCount === 1
                    ? "1 child"
                    : `${childrenCount} children`}
              </span>
            </div>
          </div>
        </div>

        {/* Main content */}
        <div className="lifecycle-main">
          {/* Real terms toggle */}
          <div className="toggle-row">
            <div className="toggle-container">
              <span
                className={`toggle-label nominal ${!showRealTerms ? "active" : ""}`}
              >
                Nominal
              </span>
              <label className="toggle-switch">
                <input
                  type="checkbox"
                  checked={showRealTerms}
                  onChange={(e) => setShowRealTerms(e.target.checked)}
                />
                <span className="toggle-slider"></span>
              </label>
              <span
                className={`toggle-label real ${showRealTerms ? "active" : ""}`}
              >
                2025 £
              </span>
            </div>
          </div>

          {/* Summary cards */}
          <div className="lifecycle-summary">
            <div className="summary-item highlighted">
              <div className="summary-label">
                Net lifetime impact{showRealTerms ? " (2025 £)" : ""}
              </div>
              <div className="summary-value">
                {formatSignedCurrency(summaryStats.netTotal)}
              </div>
            </div>
            <div className="summary-item">
              <div className="summary-label">
                Average per year{showRealTerms ? " (2025 £)" : ""}
              </div>
              <div
                className={`summary-value ${summaryStats.avgPerYear >= 0 ? "positive" : "negative"}`}
              >
                {formatSignedCurrency(summaryStats.avgPerYear)}
              </div>
            </div>
          </div>

          {/* Chart */}
          <div className="chart-container">
            {loading && <div className="loading">Loading...</div>}
            {error && <div className="error">Error: {error}</div>}
            <div ref={chartRef} className="chart"></div>

            {/* Legend */}
            <div className="legend">
              {REFORMS.map((r) => (
                <div className="legend-item" key={r.key}>
                  <div
                    className="legend-color"
                    style={{ background: r.color }}
                  ></div>
                  <span>{r.label}</span>
                </div>
              ))}
              <div className="legend-item">
                <div
                  className="legend-color"
                  style={{ background: "#000000" }}
                ></div>
                <span>Net impact</span>
              </div>
            </div>

            {/* Download buttons */}
            <div className="download-buttons">
              <button className="download-btn" onClick={downloadCSV}>
                Download CSV
              </button>
            </div>
          </div>

          {/* Methodology section */}
          <div className="methodology">
            <h3>About this model</h3>
            <p>
              This tool estimates the lifetime financial impact of recent UK
              budget policy changes on a graduate entering the workforce. It
              models how various reforms affect take-home pay from age 22 until
              retirement, accounting for earnings growth, tax thresholds, and
              student loan repayments.
            </p>

            <h4>Policy reforms modelled</h4>
            <ul>
              <li>
                <strong>Rail fare freeze</strong> — One-year freeze on rail
                fares in 2026, saving commuters the RPI increase they would
                otherwise have paid.
              </li>
              <li>
                <strong>Fuel duty reform</strong> — The 5p cut extended to
                August 2026, then phased increases.
              </li>
              <li>
                <strong>Income tax threshold freeze</strong> — Extension of the
                freeze on personal allowance (£12,570) and basic rate threshold
                (£50,270) until 2030.
              </li>
              <li>
                <strong>Unearned income tax increase</strong> — 5% increase in
                tax on dividends, savings interest, and property income.
              </li>
              <li>
                <strong>Salary sacrifice cap</strong> — £2,000 annual cap on
                salary sacrifice for pensions from April 2029.
              </li>
              <li>
                <strong>Student loan threshold freeze</strong> — Plan 2
                repayment threshold frozen at £27,295 from 2027-2030.
              </li>
              <li>
                <strong>Two-child limit abolition</strong> — Removal of the
                two-child benefit limit from April 2026.
              </li>
            </ul>

            <h4>Assumptions</h4>
            <ul>
              <li>
                Graduate starts work at age 22 with the specified starting
                salary.
              </li>
              <li>
                Earnings grow with age following typical career progression,
                plateauing at 2.2x starting salary from age 50.
              </li>
              <li>
                CPI inflation follows OBR forecasts then 2% long-term; RPI
                follows OBR forecasts then 2.39% long-term.
              </li>
              <li>
                Positive values (green) indicate the reform makes you better
                off; negative (red) means worse off.
              </li>
            </ul>
          </div>
        </div>
      </div>

      {/* Tooltip */}
      <div ref={tooltipRef} className="lifecycle-tooltip"></div>
    </div>
  );
}

export default LifecycleCalculator;
