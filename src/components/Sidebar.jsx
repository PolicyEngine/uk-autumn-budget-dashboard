import { useState, useEffect } from "react";
import "./Sidebar.css";

function Sidebar({
  policies,
  selectedPolicies,
  policyParams,
  onPolicyToggle,
  onParamChange,
  isCollapsed,
  onToggleCollapse,
}) {
  const [expandedPolicy, setExpandedPolicy] = useState(null);

  useEffect(() => {
    const handleToggle = () => {
      if (isCollapsed) {
        onToggleCollapse();
      }
    };

    window.addEventListener("toggleSidebar", handleToggle);
    return () => window.removeEventListener("toggleSidebar", handleToggle);
  }, [isCollapsed, onToggleCollapse]);

  return (
    <>
      <aside className={`sidebar ${isCollapsed ? "collapsed" : ""}`}>
        <div className="sidebar-content">
          <div className="sidebar-logo">
            <img src="/white.png" alt="PolicyEngine" className="logo" />
          </div>

          <div className="sidebar-section">
            <h2>Policy options</h2>
          </div>

          <div className="policy-list">
            {policies.map((policy) => (
              <div key={policy.id} className="policy-item">
                <label className="policy-checkbox">
                  <input
                    type="checkbox"
                    checked={selectedPolicies.includes(policy.id)}
                    onChange={() => onPolicyToggle(policy.id)}
                  />
                  <div className="policy-info">
                    <span className="policy-name">{policy.name}</span>
                    <span className="policy-description">
                      {policy.description}
                    </span>
                  </div>
                </label>

                {selectedPolicies.includes(policy.id) && policy.hasParams && (
                  <div className="policy-params">
                    {Object.entries(policy.params).map(
                      ([paramKey, paramConfig]) => (
                        <div key={paramKey} className="param-control">
                          <label htmlFor={`${policy.id}-${paramKey}`}>
                            {paramConfig.label}
                          </label>
                          <div className="param-input-group">
                            <input
                              type="range"
                              id={`${policy.id}-${paramKey}`}
                              min={paramConfig.min}
                              max={paramConfig.max}
                              step={paramConfig.step || 1}
                              value={
                                policyParams[policy.id]?.[paramKey] ||
                                paramConfig.default
                              }
                              onChange={(e) =>
                                onParamChange(
                                  policy.id,
                                  paramKey,
                                  parseFloat(e.target.value),
                                )
                              }
                              className="param-slider"
                            />
                            <input
                              type="number"
                              min={paramConfig.min}
                              max={paramConfig.max}
                              step={paramConfig.step || 1}
                              value={
                                policyParams[policy.id]?.[paramKey] ||
                                paramConfig.default
                              }
                              onChange={(e) =>
                                onParamChange(
                                  policy.id,
                                  paramKey,
                                  parseFloat(e.target.value),
                                )
                              }
                              className="param-number"
                            />
                          </div>
                        </div>
                      ),
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </aside>

      <button
        className={`sidebar-toggle ${isCollapsed ? "collapsed" : ""}`}
        onClick={onToggleCollapse}
        aria-label={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
      >
        <div className="toggle-content">
          <svg
            className="toggle-icon-svg"
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            {isCollapsed ? (
              <path d="M9 18l6-6-6-6" />
            ) : (
              <path d="M15 18l-6-6 6-6" />
            )}
          </svg>
          <span className="toggle-text">
            <span className="toggle-line">Policy</span>
            <span className="toggle-line">options</span>
          </span>
        </div>
      </button>
    </>
  );
}

export default Sidebar;
