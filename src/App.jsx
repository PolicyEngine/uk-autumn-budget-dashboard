import { useState, useEffect, useMemo } from 'react'
import PolicySelector from './components/PolicySelector'
import MetricsBar from './components/MetricsBar'
import HouseholdChart from './components/HouseholdChart'
import BudgetaryImpactChart from './components/BudgetaryImpactChart'
import DistributionalChart from './components/DistributionalChart'
import WaterfallChart from './components/WaterfallChart'
import ConstituencyMap from './components/ConstituencyMap'
import EmploymentIncomeChart from './components/EmploymentIncomeChart'
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

  // Run analysis when policies change
  useEffect(() => {
    if (selectedPolicies.length === 0) {
      setResults(null)
      return
    }

    runAnalysis()
  }, [selectedPolicies])

  const runAnalysis = async () => {
    try {
      // Fetch real data from CSV
      const response = await fetch('/data/reform-results.csv')
      const csvText = await response.text()

      // Parse CSV
      const lines = csvText.trim().split('\n')
      const headers = lines[0].split(',')

      const csvData = []
      for (let i = 1; i < lines.length; i++) {
        const values = lines[i].split(',')
        const row = {}
        headers.forEach((header, idx) => {
          row[header] = values[idx]
        })
        csvData.push(row)
      }

      // Filter data for selected policies
      const filteredData = csvData.filter(row =>
        selectedPolicies.includes(row.reform_id)
      )

      // Build budgetary impact data for chart (2026-2029)
      const years = [2026, 2027, 2028, 2029]
      const budgetData = years.map(year => {
        const dataPoint = { year }
        selectedPolicies.forEach(policyId => {
          const policy = DEFAULT_POLICIES.find(p => p.id === policyId)
          const dataRow = filteredData.find(row =>
            row.reform_id === policyId &&
            row.metric_type === 'budgetary_impact' &&
            parseInt(row.year) === year
          )
          // Convert to absolute value and billions (data is already in billions)
          // Negative values mean it costs money (reduces gov balance)
          dataPoint[policy.name] = dataRow ? Math.abs(parseFloat(dataRow.value)) : 0
        })
        return dataPoint
      })

      // Calculate metrics based on available data
      const budgetaryImpact2026Data = filteredData.filter(row =>
        row.metric_type === 'budgetary_impact' && parseInt(row.year) === 2026
      )
      const budgetaryImpact2026 = budgetaryImpact2026Data.reduce((sum, row) =>
        sum + Math.abs(parseFloat(row.value)), 0
      )

      // Build distributional data (by income decile)
      const distributional2026Data = filteredData.filter(row =>
        row.metric_type === 'distributional_impact' && parseInt(row.year) === 2026
      )

      let distributionalData = null
      if (distributional2026Data.length > 0) {
        // Sort by decile order
        const decileOrder = ['1st', '2nd', '3rd', '4th', '5th', '6th', '7th', '8th', '9th', '10th']
        distributionalData = distributional2026Data
          .map(row => ({
            decile: row.decile,
            percentChange: parseFloat(row.value)
          }))
          .sort((a, b) => decileOrder.indexOf(a.decile) - decileOrder.indexOf(b.decile))
      }

      // Build winners and losers data by decile (waterfall chart)
      const winnersLosers2026Data = filteredData.filter(row =>
        row.metric_type === 'winners_losers' && parseInt(row.year) === 2026
      )

      let waterfallData = null
      if (winnersLosers2026Data.length > 0) {
        // Transform data into format needed for stacked bar chart
        // Group by decile, with each category as a separate field
        const decileMap = {}

        winnersLosers2026Data.forEach(row => {
          const decile = row.decile
          if (!decileMap[decile]) {
            decileMap[decile] = { category: decile.toString() }
          }
          // Use category name as key, convert percentage to decimal for stacked chart
          decileMap[decile][row.category] = parseFloat(row.value) / 100
        })

        // Convert to array and sort: "All" first, then deciles 1-10
        waterfallData = Object.values(decileMap).sort((a, b) => {
          if (a.category === 'All') return -1
          if (b.category === 'All') return 1
          const aNum = parseInt(a.category)
          const bNum = parseInt(b.category)
          return aNum - bNum
        })
      }

      // For now, show null for metrics we don't have yet
      const metrics = {
        fiscalHeadroom2029: null, // Not yet available
        budgetaryImpact2026: budgetaryImpact2026,
        percentAffected: null, // Not yet available
        giniChange: null, // Not yet available
        povertyRateChange: null // Not yet available
      }

      setResults({
        metrics,
        budgetData,
        distributionalData,
        householdData: null, // Not yet available
        waterfallData
      })
    } catch (error) {
      console.error('Error loading results:', error)
      setResults(null)
    }
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
                    <div className="metric-number">
                      {results.metrics.fiscalHeadroom2029 !== null
                        ? `£${results.metrics.fiscalHeadroom2029.toFixed(1)}bn`
                        : 'No data'}
                    </div>
                  </div>
                  <div className="key-metric">
                    <div className="metric-label-small">Budgetary impact in 2026</div>
                    <div className="metric-number">
                      {results.metrics.budgetaryImpact2026 !== null
                        ? `£${results.metrics.budgetaryImpact2026.toFixed(2)}bn`
                        : 'No data'}
                    </div>
                  </div>
                  <div className="key-metric">
                    <div className="metric-number">
                      {results.metrics.percentAffected !== null
                        ? `${results.metrics.percentAffected.toFixed(1)}%`
                        : 'No data'}
                    </div>
                    <div className="metric-text">of people affected</div>
                  </div>
                  <div className="key-metric">
                    <div className="metric-number">
                      {results.metrics.giniChange !== null
                        ? results.metrics.giniChange.toFixed(2)
                        : 'No data'}
                    </div>
                    <div className="metric-text">change in inequality (Gini)</div>
                  </div>
                  <div className="key-metric">
                    <div className="metric-number">
                      {results.metrics.povertyRateChange !== null
                        ? results.metrics.povertyRateChange.toFixed(2)
                        : 'No data'}
                    </div>
                    <div className="metric-text">change in poverty rate (relative AHC)</div>
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
                  <EmploymentIncomeChart />
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
