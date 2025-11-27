import React, { useState, useEffect } from "react";
import "./OBRComparisonTable.css";

function OBRComparisonTable({ selectedPolicies }) {
  const [comparisonData, setComparisonData] = useState(null);

  useEffect(() => {
    // Fetch both OBR comparison data and PolicyEngine budgetary impact data
    Promise.all([
      fetch("/data/obr_comparison.csv").then((res) => res.text()),
      fetch("/data/budgetary_impact.csv").then((res) => res.text()),
    ])
      .then(([obrCsvText, peCsvText]) => {
        // Parse OBR data
        const obrLines = obrCsvText.trim().split("\n");
        const obrData = {};
        for (let i = 1; i < obrLines.length; i++) {
          const values = obrLines[i].split(",");
          const reform_id = values[0];
          const year = parseInt(values[2]);
          const obr_value = parseFloat(values[5]); // Post-behavioural OBR values
          const key = `${reform_id}_${year}`;
          obrData[key] = {
            reform_id,
            reform_name: values[1],
            year,
            obr_value,
          };
        }

        // Parse PolicyEngine budgetary impact data
        const peLines = peCsvText.trim().split("\n");
        const peHeaders = peLines[0].split(",");
        const reformIdIdx = peHeaders.indexOf("reform_id");
        const reformNameIdx = peHeaders.indexOf("reform_name");
        const yearIdx = peHeaders.indexOf("year");
        const valueIdx = peHeaders.indexOf("value");

        for (let i = 1; i < peLines.length; i++) {
          const values = peLines[i].split(",");
          const reform_id = values[reformIdIdx];
          const year = parseInt(values[yearIdx]);
          const pe_value = parseFloat(values[valueIdx]);
          const key = `${reform_id}_${year}`;

          if (obrData[key]) {
            obrData[key].policyengine_value = pe_value;
          }
        }

        // Convert to array
        const data = Object.values(obrData);
        setComparisonData(data);
      })
      .catch((err) => console.error("Error loading comparison data:", err));
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
