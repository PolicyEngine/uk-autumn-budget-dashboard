import { useState, useEffect } from "react";
import PersonalImpactForm from "./PersonalImpactForm";
import PersonalImpactResults from "./PersonalImpactResults";
import "./PersonalImpactTab.css";

// API URL configuration
// Set VITE_PERSONAL_IMPACT_API_URL in Vercel to the Cloud Run URL
// e.g., https://uk-autumn-budget-dashboard-HASH-ew.a.run.app
// Falls back to localhost for local development
const API_BASE_URL =
  import.meta.env.VITE_PERSONAL_IMPACT_API_URL || "http://localhost:5001";
const API_URL = `${API_BASE_URL}/api/personal-impact`;

function PersonalImpactTab() {
  const [results, setResults] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  // Load saved inputs from URL on mount
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const savedInputs = params.get("personal");
    if (savedInputs) {
      try {
        const inputs = JSON.parse(atob(savedInputs));
        handleSubmit(inputs);
      } catch {
        // Invalid saved state, ignore
      }
    }
  }, []);

  const handleSubmit = async (formData) => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(API_URL, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || "Calculation failed");
      }

      const data = await response.json();
      setResults(data);

      // Save inputs to URL for sharing
      const encodedInputs = btoa(JSON.stringify(formData));
      const params = new URLSearchParams(window.location.search);
      params.set("personal", encodedInputs);
      window.history.replaceState({}, "", `?${params.toString()}`);
    } catch (err) {
      setError(err.message);
      setResults(null);
    } finally {
      setIsLoading(false);
    }
  };

  const handleReset = () => {
    setResults(null);
    setError(null);
    const params = new URLSearchParams(window.location.search);
    params.delete("personal");
    const newUrl = params.toString()
      ? `?${params.toString()}`
      : window.location.pathname;
    window.history.replaceState({}, "", newUrl);
  };

  return (
    <div className="personal-impact-tab">
      <div className="tab-header">
        <h2>Personal impact calculator</h2>
        <p>
          See how the Autumn Budget 2025 policies affect your household over the
          next five years. Enter your details below to get a personalised
          breakdown.
        </p>
      </div>

      {error && (
        <div className="error-banner">
          <svg
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="8" x2="12" y2="12" />
            <line x1="12" y1="16" x2="12.01" y2="16" />
          </svg>
          <span>{error}</span>
        </div>
      )}

      <div className="tab-content">
        <div className="form-column">
          <PersonalImpactForm onSubmit={handleSubmit} isLoading={isLoading} />
          {results && (
            <button className="reset-btn" onClick={handleReset}>
              Start over
            </button>
          )}
        </div>

        <div className="results-column">
          {isLoading ? (
            <div className="loading-state">
              <div className="spinner" />
              <p>Calculating your impact...</p>
              <span className="loading-hint">
                This may take a few seconds as we run multiple policy
                simulations.
              </span>
            </div>
          ) : results ? (
            <PersonalImpactResults results={results} />
          ) : (
            <div className="empty-state">
              <svg
                width="64"
                height="64"
                viewBox="0 0 24 24"
                fill="none"
                stroke="#d1d5db"
                strokeWidth="1.5"
              >
                <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
                <circle cx="9" cy="7" r="4" />
                <path d="M22 21v-2a4 4 0 0 0-3-3.87" />
                <path d="M16 3.13a4 4 0 0 1 0 7.75" />
              </svg>
              <h3>Enter your details</h3>
              <p>
                Fill out the form to see how the budget policies affect your
                specific situation.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default PersonalImpactTab;
