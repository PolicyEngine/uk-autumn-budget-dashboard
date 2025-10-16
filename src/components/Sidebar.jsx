import { useState } from 'react'
import './Sidebar.css'

function Sidebar({ policies, selectedPolicies, policyParams, onPolicyToggle, onParamChange }) {
  const [expandedPolicy, setExpandedPolicy] = useState(null)

  return (
    <aside className="sidebar">
      <div className="sidebar-content">
        <div className="sidebar-logo">
          <img src="/white.png" alt="PolicyEngine" className="logo" />
        </div>

        <div className="sidebar-section">
          <h2>Policy options</h2>
        </div>

        <div className="policy-list">
          {policies.map(policy => (
            <div key={policy.id} className="policy-item">
              <label className="policy-checkbox">
                <input
                  type="checkbox"
                  checked={selectedPolicies.includes(policy.id)}
                  onChange={() => onPolicyToggle(policy.id)}
                />
                <div className="policy-info">
                  <span className="policy-name">{policy.name}</span>
                  <span className="policy-description">{policy.description}</span>
                </div>
              </label>

              {selectedPolicies.includes(policy.id) && policy.hasParams && (
                <div className="policy-params">
                  {Object.entries(policy.params).map(([paramKey, paramConfig]) => (
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
                          value={policyParams[policy.id]?.[paramKey] || paramConfig.default}
                          onChange={(e) => onParamChange(policy.id, paramKey, parseFloat(e.target.value))}
                          className="param-slider"
                        />
                        <input
                          type="number"
                          min={paramConfig.min}
                          max={paramConfig.max}
                          step={paramConfig.step || 1}
                          value={policyParams[policy.id]?.[paramKey] || paramConfig.default}
                          onChange={(e) => onParamChange(policy.id, paramKey, parseFloat(e.target.value))}
                          className="param-number"
                        />
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </aside>
  )
}

export default Sidebar
