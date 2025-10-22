import { useState, useEffect, useMemo } from 'react'
import PolicySelector from './components/PolicySelector'
import MetricsBar from './components/MetricsBar'
import HouseholdChart from './components/HouseholdChart'
import BudgetaryImpactChart from './components/BudgetaryImpactChart'
import DistributionalChart from './components/DistributionalChart'
import WaterfallChart from './components/WaterfallChart'
import './App.css'

// Policy definitions
const DEFAULT_POLICIES = [
  {
    id: 'income_tax_threshold',
    name: 'Personal allowance freeze extension',
    description: 'Extend the freeze on income tax thresholds beyond 2028'
  },
  {
    id: 'ni_rates',
    name: 'National Insurance rate changes',
    description: 'Adjust National Insurance contribution rates'
  },
  {
    id: 'vat_standard',
    name: 'VAT rate adjustment',
    description: 'Change the standard rate of VAT'
  },
  {
    id: 'corp_tax',
    name: 'Corporation tax changes',
    description: 'Adjust the main rate of corporation tax'
  },
  {
    id: 'fuel_duty',
    name: 'Fuel duty changes',
    description: 'End or modify the fuel duty freeze'
  },
  {
    id: 'pension_relief',
    name: 'Pension tax relief reform',
    description: 'Modify the rate of pension contribution tax relief'
  }
]

// Policy colors for charts
const POLICY_COLORS = ['#319795', '#5A8FB8', '#B8875A', '#5FB88A', '#4A7BA7', '#C59A5A']

function App() {
  const [selectedPolicies, setSelectedPolicies] = useState([])
  const [results, setResults] = useState(null)
  const [behavioralResponses, setBehavioralResponses] = useState(false)

  // Initialize from URL
  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const policiesParam = params.get('policies')

    if (policiesParam) {
      const policies = policiesParam.split(',')
      setSelectedPolicies(policies)
    }
  }, [])

  // Update URL when policies change
  useEffect(() => {
    if (selectedPolicies.length === 0) {
      window.history.replaceState({}, '', window.location.pathname)
    } else {
      const params = new URLSearchParams()
      params.set('policies', selectedPolicies.join(','))
      window.history.replaceState({}, '', `?${params.toString()}`)
    }
  }, [selectedPolicies])

  // Run analysis when policies or behavioral responses change
  useEffect(() => {
    if (selectedPolicies.length === 0) {
      setResults(null)
      return
    }

    runAnalysis()
  }, [selectedPolicies, behavioralResponses])

  const runAnalysis = async () => {
    // Simulate API call - in production, this would call PolicyEngine
    await new Promise(resolve => setTimeout(resolve, 500))

    // Generate mock data based on selected policies
    const numPolicies = selectedPolicies.length

    // Mock metrics for 2026
    const mockMetrics = {
      budgetaryImpact2026: 2.5 + (numPolicies * 0.8),
      percentAffected: 35.2 + (numPolicies * 5.3),
      giniChange: -0.15 - (numPolicies * 0.05),
      povertyRateChange: -0.42 - (numPolicies * 0.12)
    }

    // Mock budgetary impact data (only 2026-2029)
    const years = [2026, 2027, 2028, 2029]
    const budgetData = years.map((year, idx) => {
      const dataPoint = { year }
      selectedPolicies.forEach((policyId, pIdx) => {
        const policy = DEFAULT_POLICIES.find(p => p.id === policyId)
        dataPoint[policy.name] = 2.1 + (pIdx * 0.5) + (idx * 0.3)
      })
      return dataPoint
    })

    // Mock distributional data (percentage changes)
    const distributionalData = [
      { decile: '1st', percentChange: 2.1 + (numPolicies * 0.3) },
      { decile: '2nd', percentChange: 1.8 + (numPolicies * 0.25) },
      { decile: '3rd', percentChange: 1.5 + (numPolicies * 0.2) },
      { decile: '4th', percentChange: 1.2 + (numPolicies * 0.15) },
      { decile: '5th', percentChange: 0.9 + (numPolicies * 0.1) },
      { decile: '6th', percentChange: 0.6 + (numPolicies * 0.05) },
      { decile: '7th', percentChange: 0.3 },
      { decile: '8th', percentChange: 0.0 - (numPolicies * 0.05) },
      { decile: '9th', percentChange: -0.3 - (numPolicies * 0.1) },
      { decile: '10th', percentChange: -0.6 - (numPolicies * 0.15) }
    ]

    // Mock household scatter data
    const householdData = []
    for (let i = 0; i < 500; i++) {
      const income = Math.exp(Math.random() * 5.5 + 9.5) // Log-normal distribution
      const impact = (Math.random() - 0.5) * 8000 + (numPolicies * 200)
      householdData.push({ x: impact, y: income })
    }

    // Mock waterfall data (income change distribution)
    const waterfallData = [
      { category: 'All', value: 4, percentLabel: '96%' },
      { category: '10', value: 100, percentLabel: '100%' },
      { category: '9', value: 100, percentLabel: '100%' },
      { category: '8', value: 100, percentLabel: '100%' },
      { category: '7', value: 100, percentLabel: '100%' },
      { category: '6', value: 99, percentLabel: '99%' },
      { category: '5', value: 99, percentLabel: '99%' },
      { category: '4', value: 93, percentLabel: '93%' },
      { category: '3', value: 92, percentLabel: '92%' },
      { category: '2', value: 84, percentLabel: '84%' },
      { category: '1', value: 89, percentLabel: '89%' }
    ]

    setResults({
      metrics: mockMetrics,
      budgetData,
      distributionalData,
      householdData,
      waterfallData
    })
  }

  const handlePolicyToggle = (policyId) => {
    setSelectedPolicies(prev => {
      if (prev.includes(policyId)) {
        return prev.filter(id => id !== policyId)
      } else {
        return [...prev, policyId]
      }
    })
  }

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-content">
          <div className="header-left">
            <PolicySelector
              policies={DEFAULT_POLICIES}
              selectedPolicies={selectedPolicies}
              onPolicyToggle={handlePolicyToggle}
            />
            <div className="behavioral-switch-container">
              <label className="switch-label">
                <span className="switch-text">Behavioral responses</span>
                <button
                  className={`switch ${behavioralResponses ? 'active' : ''}`}
                  onClick={() => setBehavioralResponses(!behavioralResponses)}
                  role="switch"
                  aria-checked={behavioralResponses}
                  aria-label="Toggle behavioral responses"
                >
                  <span className="switch-slider"></span>
                </button>
              </label>
            </div>
          </div>
          <div className="header-center">
            <h1>UK Autumn Budget 2025</h1>
          </div>
          <div className="header-right">
            <img src="/white.png" alt="PolicyEngine" className="policyengine-logo" />
          </div>
        </div>
      </header>

      <main className="main-content">
        {selectedPolicies.length === 0 ? (
          <div className="empty-state">
            <h2>Welcome to the UK Autumn Budget 2025 dashboard</h2>
            <p>
              Select one or more policies from the dropdown above to analyse their potential impacts on UK households and public finances.
            </p>
            <p className="help-text">
              This dashboard is powered by{' '}
              <a href="https://policyengine.org/uk" target="_blank" rel="noopener noreferrer">
                PolicyEngine UK
              </a>
              , a free, open-source tool for computing the impact of public policy.
            </p>
          </div>
        ) : (
          <div className="results-container">
            {results && (
              <>
                {/* Key Metrics Row */}
                <div className="key-metrics-row">
                  <div className="key-metric highlighted">
                    <div className="metric-label-small">2026 budgetary impact</div>
                    <div className="metric-number">£{results.metrics.budgetaryImpact2026.toFixed(2)}bn</div>
                  </div>
                  <div className="key-metric">
                    <div className="metric-number">{results.metrics.percentAffected.toFixed(1)}%</div>
                    <div className="metric-text">of people affected</div>
                  </div>
                  <div className="key-metric">
                    <div className="metric-number">{results.metrics.giniChange.toFixed(2)}pp</div>
                    <div className="metric-text">change in inequality (Gini)</div>
                  </div>
                  <div className="key-metric">
                    <div className="metric-number">{results.metrics.povertyRateChange.toFixed(2)}pp</div>
                    <div className="metric-text">change in poverty rate</div>
                  </div>
                </div>

                {/* Section: Who is affected */}
                <div className="section-header">
                  <h2>Who is affected</h2>
                  <p>Understanding which households experience gains or losses across the income distribution</p>
                </div>
                <div className="primary-charts">
                  <HouseholdChart data={results.householdData} />
                  <BudgetaryImpactChart data={results.budgetData} policyColors={POLICY_COLORS} />
                </div>

                {/* Section: Impact over time and distribution */}
                <div className="section-header">
                  <h2>Fiscal and distributional impact</h2>
                  <p>Budget projections through 2029 and percentage change in net income by decile</p>
                </div>
                <div className="secondary-charts">
                  <DistributionalChart data={results.distributionalData} />
                  <WaterfallChart data={results.waterfallData} />
                </div>
              </>
            )}
          </div>
        )}
      </main>
    </div>
  )
}

export default App
