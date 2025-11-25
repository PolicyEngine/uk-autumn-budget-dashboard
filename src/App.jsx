import { useState, useEffect } from 'react'
import PolicySelector from './components/PolicySelector'
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
    id: 'income_tax_increase_2pp',
    name: 'Income tax increase (basic and higher +2pp)',
    description: 'Raise basic and higher rates by 2 percentage points',
    explanation: 'This policy increases the basic income tax rate from 20% to 22% and the higher rate from 40% to 42%. Income tax applies to taxable income after pension contributions and other deductions.'
  },
  {
    id: 'threshold_freeze_extension',
    name: 'Threshold freeze extension',
    description: 'Extend the freeze on income tax thresholds',
    explanation: 'This policy extends the income tax threshold freeze to 2029-30. Current law already freezes thresholds until 2027-28. Keeping the personal allowance and higher rate threshold at current levels means that as inflation increases nominal incomes, more income falls into higher tax brackets.'
  },
  {
    id: 'ni_rate_reduction',
    name: 'National Insurance rate reduction',
    description: 'Reduce the main National Insurance rate for employees',
    explanation: 'This policy reduces the main employee National Insurance contribution rate from 8% to 6%. National Insurance applies to gross earnings before pension contributions, unlike income tax which applies after deductions.'
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
      // Select all policies by default
      setSelectedPolicies(DEFAULT_POLICIES.map(p => p.id))
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
      // Keep raw household scatter data (filtering will be done by component)
      const filteredHouseholdScatter = householdScatterData.filter(row =>
        selectedPolicies.includes(row.reform_id)
      )

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

      // Calculate budgetary impact for 2026 (metrics always show 2026)
      const budgetaryImpact2026 = filteredBudgetary
        .filter(row => parseInt(row.year) === 2026)
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

      // Extract metrics for 2026 (metrics always show 2026)
      const metrics2026 = filteredMetrics.find(row => parseInt(row.year) === 2026)
      const percentAffected = metrics2026 ? parseFloat(metrics2026.people_affected) : null
      const giniChange = metrics2026 ? parseFloat(metrics2026.gini_change) : null
      const povertyRateChange = metrics2026 ? parseFloat(metrics2026.poverty_change_pp) : null

      // Calculate fiscal headroom for 2029/30
      const budgetaryImpact2029 = filteredBudgetary
        .filter(row => parseInt(row.year) === 2029)
        .reduce((sum, row) => sum + parseFloat(row.value), 0)
      const obrBaselineHeadroom = 9.9
      const fiscalHeadroom2029 = obrBaselineHeadroom + budgetaryImpact2029

      setResults({
        metrics: {
          fiscalHeadroom2029,
          budgetaryImpact2026,
          percentAffected,
          giniChange,
          povertyRateChange
        },
        budgetData,
        distributionalData: distributionalChartData.length > 0 ? distributionalChartData : null,
        waterfallData: waterfallData.length > 0 ? waterfallData : null,
        householdScatterData: filteredHouseholdScatter.length > 0 ? filteredHouseholdScatter : null,
        rawDistributional: filteredDistributional,
        rawWinnersLosers: filteredWinnersLosers,
        rawHouseholdScatter: filteredHouseholdScatter
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
                    <div className="metric-label-small">Revenue impact in 2026-27</div>
                    <div className="metric-number">
                      {results.metrics.budgetaryImpact2026 !== null
                        ? `£${results.metrics.budgetaryImpact2026.toFixed(1)}bn`
                        : 'No data'}
                    </div>
                  </div>
                  <div className="key-metric">
                    <div className="metric-text">Change in inequality (Gini coefficient) in 2026-27</div>
                    <div className="metric-number">
                      {results.metrics.giniChange !== null
                        ? `${(results.metrics.giniChange * 100).toFixed(1)}%`
                        : 'No data'}
                    </div>
                  </div>
                  <div className="key-metric">
                    <div className="metric-text">
                      Change in poverty rate (absolute BHC) in 2026-27
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
                    Use the policy selector in the top left to choose which budget reforms to analyse. This dashboard models the fiscal and distributional impacts of selected policies, showing their effects on Government revenues, household incomes, poverty rates, and inequality. Explore the visualisations below to understand how reforms affect different households across income levels, regions, and demographic groups.
                  </p>

                  {/* Selected Policies Explanations */}
                  {selectedPolicies.length > 0 && (
                    <div className="policy-explanations-section">
                      <h3>Selected {selectedPolicies.length === 1 ? 'policy' : 'policies'}</h3>
                      <p style={{ marginBottom: '12px' }}>
                        The following {selectedPolicies.length === 1 ? 'is the policy' : 'are the policies'} you have selected for analysis:
                      </p>
                      <ul style={{ marginLeft: '20px', lineHeight: '1.7' }}>
                        {selectedPolicies.map(policyId => {
                          const policy = DEFAULT_POLICIES.find(p => p.id === policyId)
                          if (!policy) return null
                          return (
                            <li key={policyId} style={{ marginBottom: '12px' }}>
                              <strong>{policy.name}:</strong> {policy.explanation}
                            </li>
                          )
                        })}
                      </ul>
                    </div>
                  )}
                </div>

                {/* Section: Who is affected */}
                <div className="section-header">
                  <h2>Household and revenue impacts</h2>
                  <p>This section shows how selected policies affect individual households across different income levels and demographic groups, alongside the projected impact on Government revenues and expenditure over the period from 2025 to 2030.</p>
                </div>
                <div className="primary-charts">
                  <EmploymentIncomeChart selectedPolicies={selectedPolicies} selectedYear={2026} />
                  <BudgetaryImpactChart data={results.budgetData} />
                </div>

                {/* Section: Impact over time and distribution */}
                <div className="section-header">
                  <h2>Distributional analysis</h2>
                  <p>This section examines how income changes are distributed across household income deciles, revealing the proportion of winners and losers from the proposed policy reforms and their effects on income inequality and poverty rates.</p>
                </div>
                <div className="secondary-charts">
                  <DistributionalChart rawData={results.rawDistributional} selectedPolicies={selectedPolicies} />
                  <WaterfallChart rawData={results.rawWinnersLosers} selectedPolicies={selectedPolicies} />
                </div>

                {/* Section: Breakdown of the effects */}
                <div className="section-header">
                  <h2>Regional and demographic analysis</h2>
                  <p>This section illustrates regional variation in policy impacts across all 650 UK Parliamentary constituencies and explores how different demographic groups and household types experience the effects of the selected reforms.</p>
                </div>
                <div className="secondary-charts">
                  <ConstituencyMap selectedPolicies={selectedPolicies} />
                  {results.rawHouseholdScatter && (
                    <HouseholdChart rawData={results.rawHouseholdScatter} selectedPolicies={selectedPolicies} />
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
