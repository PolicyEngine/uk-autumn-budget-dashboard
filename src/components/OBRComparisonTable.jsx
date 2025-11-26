import React, { useState, useEffect } from "react";
import "./OBRComparisonTable.css";

function OBRComparisonTable({ selectedPolicies }) {
  const [comparisonData, setComparisonData] = useState(null);

  useEffect(() => {
    fetch("/data/obr_comparison.csv")
      .then((res) => res.text())
      .then((csvText) => {
        const lines = csvText.trim().split("\n");
        const data = [];
        for (let i = 1; i < lines.length; i++) {
          const values = lines[i].split(",");
          data.push({
            reform_id: values[0],
            reform_name: values[1],
            year: parseInt(values[2]),
            policyengine_value: parseFloat(values[3]),
            obr_value: parseFloat(values[4]),
          });
        }
        setComparisonData(data);
      })
      .catch((err) => console.error("Error loading OBR comparison data:", err));
  }, []);

  if (!comparisonData || selectedPolicies.length === 0) return null;

  // Filter to selected policies
  const filteredData = comparisonData.filter((row) =>
    selectedPolicies.includes(row.reform_id),
  );

  if (filteredData.length === 0) return null;

  // Group by policy
  const policiesMap = {};
  filteredData.forEach((row) => {
    if (!policiesMap[row.reform_id]) {
      policiesMap[row.reform_id] = {
        name: row.reform_name,
        years: {},
      };
    }
    policiesMap[row.reform_id].years[row.year] = {
      policyengine: row.policyengine_value,
      obr: row.obr_value,
    };
  });

  const years = [2026, 2027, 2028, 2029];
  const policies = Object.entries(policiesMap);

  const formatValue = (value) => {
    if (value === null || value === undefined || isNaN(value)) return "—";
    const sign = value >= 0 ? "" : "-";
    return `${sign}£${Math.abs(value).toFixed(1)}bn`;
  };

  const getDifferenceClass = (pe, obr) => {
    if (pe === null || obr === null || isNaN(pe) || isNaN(obr)) return "";
    const diff = Math.abs(pe - obr);
    if (diff < 0.5) return "diff-small";
    if (diff < 2) return "diff-medium";
    return "diff-large";
  };

  return (
    <div className="obr-comparison-section">
      <h2>PolicyEngine vs OBR comparison</h2>
      <p className="comparison-description">
        This table compares PolicyEngine's microsimulation estimates with the
        OBR's official costings from the November 2025 Economic and Fiscal
        Outlook. Values show annual budgetary impact in billions of pounds.
        Positive values indicate revenue for the Government; negative values
        indicate costs. Differences may arise from methodological approaches,
        behavioural assumptions, and data sources.
      </p>

      <div className="comparison-table-wrapper">
        <table className="comparison-table">
          <thead>
            <tr>
              <th rowSpan="2">Policy</th>
              {years.map((year) => (
                <th key={year} colSpan="2" className="year-header">
                  {year}-{(year + 1).toString().slice(-2)}
                </th>
              ))}
            </tr>
            <tr>
              {years.map((year) => (
                <React.Fragment key={year}>
                  <th className="source-header pe">PE</th>
                  <th className="source-header obr">OBR</th>
                </React.Fragment>
              ))}
            </tr>
          </thead>
          <tbody>
            {policies.map(([policyId, policy]) => (
              <tr key={policyId}>
                <td className="policy-name-cell">{policy.name}</td>
                {years.map((year) => {
                  const yearData = policy.years[year] || {};
                  const pe = yearData.policyengine;
                  const obr = yearData.obr;
                  return (
                    <React.Fragment key={year}>
                      <td
                        className={`value-cell pe ${getDifferenceClass(pe, obr)}`}
                      >
                        {formatValue(pe)}
                      </td>
                      <td
                        className={`value-cell obr ${getDifferenceClass(pe, obr)}`}
                      >
                        {formatValue(obr)}
                      </td>
                    </React.Fragment>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="comparison-legend">
        <span className="legend-item">
          <span className="legend-dot diff-small"></span>
          Difference &lt; £0.5bn
        </span>
        <span className="legend-item">
          <span className="legend-dot diff-medium"></span>
          Difference £0.5-2bn
        </span>
        <span className="legend-item">
          <span className="legend-dot diff-large"></span>
          Difference &gt; £2bn
        </span>
      </div>

      <p className="comparison-note">
        <strong>Note:</strong> OBR costings include behavioural responses and
        indirect effects that may not be fully captured in PolicyEngine's
        static microsimulation. The OBR's salary sacrifice cap costing shows
        £4.7bn in 2029-30 due to a one-off timing effect from relief-at-source
        pension scheme switching. See{" "}
        <a
          href="https://obr.uk/efo/economic-and-fiscal-outlook-november-2025/"
          target="_blank"
          rel="noopener noreferrer"
        >
          OBR EFO November 2025
        </a>{" "}
        for full methodology.
      </p>
    </div>
  );
}

export default OBRComparisonTable;
