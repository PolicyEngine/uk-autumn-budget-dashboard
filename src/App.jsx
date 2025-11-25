import { useState, useEffect } from 'react'
import PolicySelector from './components/PolicySelector'
import YearSelector from './components/YearSelector'
import BudgetaryImpactChart from './components/BudgetaryImpactChart'
import DistributionalChart from './components/DistributionalChart'
import WaterfallChart from './components/WaterfallChart'
import ConstituencyMap from './components/ConstituencyMap'
import EmploymentIncomeChart from './components/EmploymentIncomeChart'
import HouseholdChart from './components/HouseholdChart'
import './App.css'

// Policy definitions
const DEFAULT_POLICIES = [
  {
    id: 'two_child_limit',
    name: '2 child limit repeal',
    description: 'Repeal the two-child limit on benefits',
    explanation: 'The two-child limit restricts Universal Credit and Child Tax Credit payments to a maximum number of children per family. Removing this limit would allow families to claim child-related benefit payments for all children without a cap.'
  },
  {
    id: 'basic_rate_increase_1p',
    name: 'Basic rate increase by 1 percentage point',
    description: 'Increase the basic rate of income tax by 1 percentage point',
    explanation: 'This policy increases the basic rate of income tax. The basic rate applies to income between the personal allowance and the higher rate threshold.'
  },
  {
    id: 'threshold_freeze_extension',
    name: 'Threshold freeze extension',
    description: 'Extend the freeze on income tax thresholds',
    explanation: 'Income tax thresholds include the personal allowance and the higher rate threshold. Under current law, these thresholds are frozen until a certain date. This policy extends that freeze beyond the current end date, keeping the thresholds at their current levels rather than increasing them with inflation.'
  },
  {
    id: 'ni_rate_reduction',
    name: 'National Insurance rate reduction',
    description: 'Reduce the main National Insurance rate for employees',
    explanation: 'This policy reduces the main employee National Insurance contribution rate from 8% to 6%. National Insurance is a tax on earnings paid by employees and employers, which funds state benefits including the state pension and NHS.'
  }
]

function parseCSV(csvText) {
  const lines = csvText.trim().split('\n')
  const headers = lines[0].split(',')
  const data = []
  for (let i = 1; i < lines.length; i++) {
    const values = lines[i].split(',')
    const row = {}
    headers.forEach((header, idx) => {
      row[header] = values[idx]
    })
    data.push(row)
  }
  return data
}

function App() {
  const [selectedPolicies, setSelectedPolicies] = useState([])
  const [selectedYear, setSelectedYear] = useState(2026)
  const [results, setResults] = useState(null)

  // Initialize from URL or select all policies by default
  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const policiesParam = params.get('policies')
    const yearParam = params.get('year')

    if (policiesParam) {
      const policies = policiesParam.split(',')
      setSelectedPolicies(policies)
    } else {
      // Select only two_child_limit by default (only policy with data)
      setSelectedPolicies(['two_child_limit'])
    }

    if (yearParam) {
      const year = parseInt(yearParam)
      if ([2026, 2027, 2028, 2029].includes(year)) {
        setSelectedYear(year)
      }
    }
  }, [])

  // Update URL when policies or year change
  useEffect(() => {
    if (selectedPolicies.length === 0) {
      window.history.replaceState({}, '', window.location.pathname)
    } else {
      const params = new URLSearchParams()
      params.set('policies', selectedPolicies.join(','))
      params.set('year', selectedYear)
      window.history.replaceState({}, '', `?${params.toString()}`)
    }
  }, [selectedPolicies, selectedYear])

  // Run analysis when policies or year change
  useEffect(() => {
    if (selectedPolicies.length === 0) {
      setResults(null)
      return
    }

    runAnalysis()
  }, [selectedPolicies, selectedYear])

  const runAnalysis = async () => {
    try {
      // Fetch all CSVs in parallel
      const [
        budgetaryRes,
        distributionalRes,
        winnersLosersRes,
        metricsRes,
        householdScatterRes
      ] = await Promise.all([
        fetch('/data/budgetary_impact.csv'),
        fetch('/data/distributional_impact.csv'),
        fetch('/data/winners_losers.csv'),
        fetch('/data/metrics.csv'),
        fetch('/data/household_scatter.csv')
      ])

      const budgetaryData = parseCSV(await budgetaryRes.text())
      const distributionalData = parseCSV(await distributionalRes.text())
      const winnersLosersData = parseCSV(await winnersLosersRes.text())
      const metricsData = parseCSV(await metricsRes.text())
      const householdScatterData = parseCSV(await householdScatterRes.text())

      // Filter data for selected policies
      const filteredBudgetary = budgetaryData.filter(row =>
        selectedPolicies.includes(row.reform_id)
      )
      const filteredDistributional = distributionalData.filter(row =>
        selectedPolicies.includes(row.reform_id)
      )
      const filteredWinnersLosers = winnersLosersData.filter(row =>
        selectedPolicies.includes(row.reform_id)
      )
      const filteredMetrics = metricsData.filter(row =>
        selectedPolicies.includes(row.reform_id)
      )
      const filteredHouseholdScatter = householdScatterData
        .filter(row => selectedPolicies.includes(row.reform_id) && parseInt(row.year) === selectedYear)
        .map(row => ({
          baseline_income: parseFloat(row.baseline_income),
          income_change: parseFloat(row.income_change),
          household_weight: parseFloat(row.household_weight)
        }))

      // Build budgetary impact data for chart (2026-2029)
      // Always include all policy keys for smooth animations
      const years = [2026, 2027, 2028, 2029]
      const budgetData = years.map(year => {
        const dataPoint = { year }
        let netImpact = 0
        DEFAULT_POLICIES.forEach(policy => {
          const isSelected = selectedPolicies.includes(policy.id)
          const dataRow = budgetaryData.find(row =>
            row.reform_id === policy.id && parseInt(row.year) === year
          )
          const value = isSelected && dataRow ? parseFloat(dataRow.value) : 0
          dataPoint[policy.name] = value
          netImpact += value
        })
        dataPoint.netImpact = netImpact
        return dataPoint
      })

      // Calculate budgetary impact for selected year
      const budgetaryImpactSelectedYear = filteredBudgetary
        .filter(row => parseInt(row.year) === selectedYear)
        .reduce((sum, row) => sum + parseFloat(row.value), 0)

      // Build distributional data (grouped by decile with policy breakdown)
      // Always include all policy keys for smooth animations
      const decileOrder = ['1st', '2nd', '3rd', '4th', '5th', '6th', '7th', '8th', '9th', '10th']
      const distributionalSelectedYear = distributionalData.filter(row => parseInt(row.year) === selectedYear)
      const distributionalChartData = decileOrder.map(decile => {
        const dataPoint = { decile }
        let netChange = 0
        DEFAULT_POLICIES.forEach(policy => {
          const isSelected = selectedPolicies.includes(policy.id)
          const dataRow = distributionalSelectedYear.find(row =>
            row.reform_id === policy.id && row.decile === decile
          )
          const value = isSelected && dataRow ? parseFloat(dataRow.value) : 0
          dataPoint[policy.name] = value
          netChange += value
        })
        dataPoint.netChange = netChange
        return dataPoint
      })

      // Build waterfall data (grouped by decile with policy breakdown)
      // Always include all policy keys for smooth animations
      const waterfallSelectedYear = winnersLosersData.filter(row => parseInt(row.year) === selectedYear && row.decile !== 'all')
      const waterfallDeciles = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10']
      const waterfallData = waterfallDeciles.map(decile => {
        const dataPoint = { decile }
        let netChange = 0
        DEFAULT_POLICIES.forEach(policy => {
          const isSelected = selectedPolicies.includes(policy.id)
          const dataRow = waterfallSelectedYear.find(row =>
            row.reform_id === policy.id && row.decile === decile
          )
          const value = isSelected && dataRow ? parseFloat(dataRow.avg_change) : 0
          dataPoint[policy.name] = value
          netChange += value
        })
        dataPoint.netChange = netChange
        return dataPoint
      })

      // Extract metrics
      const metricsSelectedYear = filteredMetrics.find(row => parseInt(row.year) === selectedYear)
      const percentAffected = metricsSelectedYear ? parseFloat(metricsSelectedYear.people_affected) : null
      const giniChange = metricsSelectedYear ? parseFloat(metricsSelectedYear.gini_change) : null
      const povertyRateChange = metricsSelectedYear ? parseFloat(metricsSelectedYear.poverty_change_pp) : null

      // Calculate fiscal headroom for 2029/30
      const budgetaryImpact2029 = filteredBudgetary
        .filter(row => parseInt(row.year) === 2029)
        .reduce((sum, row) => sum + parseFloat(row.value), 0)
      const obrBaselineHeadroom = 9.9
      const fiscalHeadroom2029 = obrBaselineHeadroom + budgetaryImpact2029

      setResults({
        metrics: {
          fiscalHeadroom2029,
          budgetaryImpactSelectedYear,
          percentAffected,
          giniChange,
          povertyRateChange
        },
        budgetData,
        distributionalData: distributionalChartData.length > 0 ? distributionalChartData : null,
        waterfallData: waterfallData.length > 0 ? waterfallData : null,
        householdScatterData: filteredHouseholdScatter.length > 0 ? filteredHouseholdScatter : null
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
            <YearSelector
              selectedYear={selectedYear}
              onYearChange={setSelectedYear}
            />
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
                    <div className="metric-label-small">
                      Fiscal headroom in 2029-30
                      <span className="info-icon-wrapper">
                        <svg className="info-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <circle cx="12" cy="12" r="10"></circle>
                          <line x1="12" y1="16" x2="12" y2="12"></line>
                          <line x1="12" y1="8" x2="12.01" y2="8"></line>
                        </svg>
                        <span className="info-tooltip">Fiscal headroom is the gap between the forecast fiscal position and the point at which the Government would breach its fiscal rule. The budgetary impact of each reform is applied directly to the OBR's forecast current budget balance in 2029-30 to produce the updated headroom.</span>
                      </span>
                    </div>
                    <div className="metric-number">
                      {results.metrics.fiscalHeadroom2029 !== null
                        ? `£${results.metrics.fiscalHeadroom2029.toFixed(1)}bn`
                        : 'No data'}
                    </div>
                  </div>
                  <div className="key-metric">
                    <div className="metric-label-small">Revenue impact in {selectedYear}-{(selectedYear + 1).toString().slice(-2)}</div>
                    <div className="metric-number">
                      {results.metrics.budgetaryImpactSelectedYear !== null
                        ? `£${results.metrics.budgetaryImpactSelectedYear.toFixed(1)}bn`
                        : 'No data'}
                    </div>
                  </div>
                  <div className="key-metric">
                    <div className="metric-text">Share of people affected</div>
                    <div className="metric-number">
                      {results.metrics.percentAffected !== null
                        ? `${results.metrics.percentAffected.toFixed(1)}%`
                        : 'No data'}
                    </div>
                  </div>
                  <div className="key-metric">
                    <div className="metric-text">Change in inequality (Gini coefficient)</div>
                    <div className="metric-number">
                      {results.metrics.giniChange !== null
                        ? `${(results.metrics.giniChange * 100).toFixed(1)}%`
                        : 'No data'}
                    </div>
                  </div>
                  <div className="key-metric">
                    <div className="metric-text">
                      Change in poverty rate (absolute BHC)
                      <span className="info-icon-wrapper">
                        <svg className="info-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <circle cx="12" cy="12" r="10"></circle>
                          <line x1="12" y1="16" x2="12" y2="12"></line>
                          <line x1="12" y1="8" x2="12.01" y2="8"></line>
                        </svg>
                        <span className="info-tooltip">BHC stands for Before Housing Costs. This measures poverty based on household income before deducting housing costs such as rent, mortgage payments, and other housing expenses. Absolute poverty is measured against a fixed threshold that doesn't change with median incomes.</span>
                      </span>
                    </div>
                    <div className="metric-number">
                      {results.metrics.povertyRateChange !== null
                        ? `${results.metrics.povertyRateChange.toFixed(1)}pp`
                        : 'No data'}
                    </div>
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

                  {/* Selected Policies Explanations */}
                  {selectedPolicies.length > 0 && (
                    <div className="policy-explanations-section">
                      <h3>Selected {selectedPolicies.length === 1 ? 'policy' : 'policies'}</h3>
                      {selectedPolicies.map(policyId => {
                        const policy = DEFAULT_POLICIES.find(p => p.id === policyId)
                        if (!policy) return null
                        return (
                          <p key={policyId}>
                            <strong>{policy.name}:</strong> {policy.explanation}
                          </p>
                        )
                      })}
                    </div>
                  )}
                </div>

                {/* Section: Who is affected */}
                <div className="section-header">
                  <h2>Household and fiscal impacts</h2>
                  <p>How selected policies affect individual households and government revenues over time</p>
                </div>
                <div className="primary-charts">
                  <EmploymentIncomeChart selectedPolicies={selectedPolicies} selectedYear={selectedYear} />
                  <BudgetaryImpactChart data={results.budgetData} />
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
                  <ConstituencyMap selectedPolicies={selectedPolicies} selectedYear={selectedYear} />
                  {results.householdScatterData && (
                    <HouseholdChart data={results.householdScatterData} />
                  )}
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
