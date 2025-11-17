import { useState, useEffect, useMemo } from 'react'
import PolicySelector from './components/PolicySelector'
import MetricsBar from './components/MetricsBar'
import HouseholdChart from './components/HouseholdChart'
import BudgetaryImpactChart from './components/BudgetaryImpactChart'
import DistributionalChart from './components/DistributionalChart'
import WaterfallChart from './components/WaterfallChart'
import ConstituencyMap from './components/ConstituencyMap'
import './App.css'

// Policy definitions
const DEFAULT_POLICIES = [
  {
    id: 'two_child_limit',
    name: '2 child limit reforms',
    description: 'Reform the two-child limit on benefits'
  },
  {
    id: 'vat_changes',
    name: 'VAT changes',
    description: 'Adjust VAT rates and exemptions'
  },
  {
    id: 'freezing_thresholds',
    name: 'Freezing thresholds',
    description: 'Freeze income tax and National Insurance thresholds'
  },
  {
    id: 'fuel_duty',
    name: 'Raising fuel duty',
    description: 'Increase fuel duty rates'
  },
  {
    id: 'ni_rates',
    name: 'Adjusting NI rates',
    description: 'Change National Insurance contribution rates'
  },
  {
    id: 'income_tax_rates',
    name: 'Adjusting income tax rates',
    description: 'Modify income tax rate bands'
  }
]

// Policy colors for charts
const POLICY_COLORS = ['#319795', '#5A8FB8', '#B8875A', '#5FB88A', '#4A7BA7', '#C59A5A']

function App() {
  const [selectedPolicies, setSelectedPolicies] = useState([])
  const [results, setResults] = useState(null)
  const [behavioralResponses, setBehavioralResponses] = useState(false)

  // Initialize from URL or select all policies by default
  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const policiesParam = params.get('policies')

    if (policiesParam) {
      const policies = policiesParam.split(',')
      setSelectedPolicies(policies)
    } else {
      // Select all policies by default
      const allPolicyIds = DEFAULT_POLICIES.map(p => p.id)
      setSelectedPolicies(allPolicyIds)
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
      fiscalHeadroom2029: 15.3 - (numPolicies * 1.2), // Fiscal headroom in 2029/30
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
            <h1>UK Autumn Budget 2025 analysis</h1>
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
                {/* Introduction Section */}
                <div className="intro-section">
                  <h2>Highlights and introduction</h2>
                </div>

                {/* Key Metrics Row */}
                <div className="key-metrics-row">
                  <div className="key-metric highlighted">
                    <div className="metric-label-small">Fiscal headroom in 2029/30</div>
                    <div className="metric-number">£{results.metrics.fiscalHeadroom2029.toFixed(1)}bn</div>
                  </div>
                  <div className="key-metric">
                    <div className="metric-label-small">Budgetary impact in 2026</div>
                    <div className="metric-number">£{results.metrics.budgetaryImpact2026.toFixed(2)}bn</div>
                  </div>
                  <div className="key-metric">
                    <div className="metric-number">{results.metrics.percentAffected.toFixed(1)}%</div>
                    <div className="metric-text">of people affected</div>
                  </div>
                  <div className="key-metric">
                    <div className="metric-number">{results.metrics.giniChange.toFixed(2)}</div>
                    <div className="metric-text">change in inequality (Gini)</div>
                  </div>
                  <div className="key-metric">
                    <div className="metric-number">{results.metrics.povertyRateChange.toFixed(2)}</div>
                    <div className="metric-text">change in poverty rate</div>
                  </div>
                </div>

                {/* Summary Paragraph */}
                <div className="summary-paragraph">
                  <p>
                    Use the policy selector in the top left to choose which budget reforms to analyse.
                    This dashboard provides a comprehensive analysis of the selected policy reforms.
                    The metrics below show the immediate fiscal impact and long-term effects on government finances,
                    alongside distributional outcomes including changes to inequality and poverty rates.
                    Use the visualisations to explore how these policies affect different households across
                    income levels, regions, and demographic groups.
                  </p>
                </div>

                {/* Section: Who is affected */}
                <div className="section-header">
                  <h2>Household and fiscal impacts</h2>
                  <p>How selected policies affect individual households and government revenues over time</p>
                </div>
                <div className="primary-charts">
                  <HouseholdChart data={results.householdData} />
                  <BudgetaryImpactChart data={results.budgetData} policyColors={POLICY_COLORS} />
                </div>

                {/* Section: Impact over time and distribution */}
                <div className="section-header">
                  <h2>Distributional analysis</h2>
                  <p>Income changes across deciles and the proportion of winners and losers from policy reforms</p>
                </div>
                <div className="secondary-charts">
                  <DistributionalChart data={results.distributionalData} />
                  <WaterfallChart data={results.waterfallData} />
                </div>

                {/* Section: Breakdown of the effects */}
                <div className="section-header">
                  <h2>Geographic and demographic breakdown</h2>
                  <p>Regional variation in policy impacts across Parliamentary constituencies and demographic groups</p>
                </div>
                <div className="secondary-charts">
                  <ConstituencyMap />
                  <div className="constituency-placeholder"></div>
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
