import { useState, useEffect } from "react";
import "./FiscalHeadroom.css";

function FiscalHeadroom() {
  const [headroom, setHeadroom] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Load budgetary impact data from CSV
    fetch("/data/reform-results.csv")
      .then((response) => response.text())
      .then((csvText) => {
        const lines = csvText.trim().split("\n");
        const headers = lines[0].split(",");

        console.log("[FiscalHeadroom] CSV Headers:", headers);

        // Find budgetary impact for 2029
        let impact2029 = null;
        let budgetaryRows = [];

        for (let i = 1; i < lines.length; i++) {
          const values = lines[i].split(",");
          const row = {};
          headers.forEach((header, index) => {
            row[header.trim()] = values[index] ? values[index].trim() : "";
          });

          // Log only budgetary_impact rows
          if (row.metric_type === "budgetary_impact") {
            budgetaryRows.push({ year: row.year, value: row.value });

            if (row.reform_id === "two_child_limit" && row.year === "2029") {
              impact2029 = parseFloat(row.value);
              console.log("[FiscalHeadroom] Found 2029 impact:", impact2029);
              break;
            }
          }
        }

        console.log(
          "[FiscalHeadroom] All budgetary_impact rows:",
          budgetaryRows,
        );

        if (impact2029 === null) {
          console.error("[FiscalHeadroom] No 2029 budgetary impact found");
          console.error(
            "[FiscalHeadroom] Available years:",
            budgetaryRows.map((r) => r.year),
          );
          setLoading(false);
          return;
        }

        // OBR baseline headroom for 2029/30
        const obrHeadroom = 9.9; // £9.9 billion

        // Calculate new headroom
        // Note: budgetary_impact is negative when it costs money (increases spending)
        // If impact is -3.37 (costs £3.37bn), headroom decreases: 9.9 + (-3.37) = 6.53
        const newHeadroom = obrHeadroom + impact2029;

        console.log("Headroom calculation:", {
          obrHeadroom,
          impact2029,
          newHeadroom,
        });

        setHeadroom({
          obr: obrHeadroom,
          impact: impact2029,
          new: newHeadroom,
        });
        setLoading(false);
      })
      .catch((error) => {
        console.error("Error loading fiscal headroom data:", error);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <div className="fiscal-headroom">
        <h2>Fiscal headroom</h2>
        <p className="fiscal-description">
          Impact on OBR fiscal headroom for 2029/30
        </p>
        <div className="headroom-loading">Loading...</div>
      </div>
    );
  }

  if (!headroom) {
    return (
      <div className="fiscal-headroom">
        <h2>Fiscal headroom</h2>
        <p className="fiscal-description">
          Impact on OBR fiscal headroom for 2029/30
        </p>
        <div className="headroom-error">
          No data available. Please check the browser console for details.
        </div>
      </div>
    );
  }

  const formatBillion = (value) => {
    return `£${Math.abs(value).toFixed(2)}bn`;
  };

  return (
    <div className="fiscal-headroom">
      <h2>Fiscal headroom</h2>
      <p className="fiscal-description">
        Impact on OBR fiscal headroom for 2029/30
      </p>

      <div className="headroom-container">
        <div className="headroom-item">
          <div className="headroom-label">OBR baseline (2029/30)</div>
          <div className="headroom-value baseline">
            {formatBillion(headroom.obr)}
          </div>
        </div>

        <div className="headroom-operator">
          <span>+</span>
        </div>

        <div className="headroom-item">
          <div className="headroom-label">Reform budgetary impact (2029)</div>
          <div
            className={`headroom-value ${headroom.impact < 0 ? "negative" : "positive"}`}
          >
            {headroom.impact < 0 ? "−" : "+"}
            {formatBillion(headroom.impact)}
          </div>
        </div>

        <div className="headroom-operator">
          <span>=</span>
        </div>

        <div className="headroom-item result">
          <div className="headroom-label">New fiscal headroom</div>
          <div
            className={`headroom-value ${headroom.new < headroom.obr ? "decreased" : "increased"}`}
          >
            {formatBillion(headroom.new)}
          </div>
          <div className="headroom-percentage">
            ({(headroom.new / 300).toFixed(1)}% of GDP)
          </div>
        </div>
      </div>

      <div className="headroom-note">
        The fiscal headroom measures the amount of room the Government has under
        its fiscal rules. The OBR baseline is £9.9 billion (0.3% of GDP). This
        reform {headroom.impact < 0 ? "reduces" : "increases"}
        headroom by {formatBillion(Math.abs(headroom.impact))} to{" "}
        {formatBillion(headroom.new)}.
      </div>
    </div>
  );
}

export default FiscalHeadroom;
