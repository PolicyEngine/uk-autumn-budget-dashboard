import { useState, useEffect, useRef } from 'react'
import {
  BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer
} from 'recharts'
import HouseholdImpactChart from './HouseholdImpactChart'
import './Results.css'

// Animated number component
function AnimatedNumber({ value, format = (v) => v, duration = 800 }) {
  const [displayValue, setDisplayValue] = useState(0)
  const rafRef = useRef(null)

  useEffect(() => {
    const startValue = displayValue
    const startTime = performance.now()

    const animate = (currentTime) => {
      const elapsed = currentTime - startTime
      const progress = Math.min(elapsed / duration, 1)

      // Ease-out cubic
      const eased = 1 - Math.pow(1 - progress, 3)
      const current = startValue + (value - startValue) * eased

      setDisplayValue(current)

      if (progress < 1) {
        rafRef.current = requestAnimationFrame(animate)
      }
    }

    rafRef.current = requestAnimationFrame(animate)

    return () => {
      if (rafRef.current) {
        cancelAnimationFrame(rafRef.current)
      }
    }
  }, [value])

  return <span>{format(displayValue)}</span>
}

function Results({ results, isLoading, selectedPolicies }) {
  const [showReduction, setShowReduction] = useState(true)

  // Download handlers
  const handleDownloadTxt = () => {
    if (!results) return

    const date = new Date().toISOString().split('T')[0]
    let content = `UK Autumn Budget 2025 Dashboard - Analysis Results\n`
    content += `Generated: ${new Date().toLocaleString('en-GB')}\n\n`
    content += `Selected Policies:\n`
    content += results.policies.map(p => `- ${p.name}`).join('\n')
    content += `\n\n`
    content += `Affected Households: ${results.affectedHouseholds.toLocaleString('en-GB')}\n`
    content += `Average Impact: £${results.averageImpact}\n`
    content += `Absolute Poverty Reduction: ${(results.povertyImpact.absolute.baseline - results.povertyImpact.absolute.withPolicies).toFixed(2)}pp\n`

    const blob = new Blob([content], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `uk-budget-analysis-${date}.txt`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  }

  const handleDownloadCsv = () => {
    if (!results) return

    const date = new Date().toISOString().split('T')[0]
    let content = `Metric,Value\n`
    content += `Affected Households,${results.affectedHouseholds}\n`
    content += `Average Impact,£${results.averageImpact}\n`
    content += `Baseline Absolute Poverty,${results.povertyImpact.absolute.baseline}%\n`
    content += `Reformed Absolute Poverty,${results.povertyImpact.absolute.withPolicies}%\n`
    content += `Baseline Relative Poverty,${results.povertyImpact.relative.baseline}%\n`
    content += `Reformed Relative Poverty,${results.povertyImpact.relative.withPolicies}%\n`

    const blob = new Blob([content], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `uk-budget-analysis-${date}.csv`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  }

  // Listen for download events
  useEffect(() => {
    const handleTxtEvent = () => handleDownloadTxt()
    const handleCsvEvent = () => handleDownloadCsv()

    window.addEventListener('downloadDataTxt', handleTxtEvent)
    window.addEventListener('downloadDataCsv', handleCsvEvent)

    return () => {
      window.removeEventListener('downloadDataTxt', handleTxtEvent)
      window.removeEventListener('downloadDataCsv', handleCsvEvent)
    }
  }, [results])

  if (selectedPolicies.length === 0) {
    return (
      <div className="results-empty">
        <div className="empty-state">
          <h2>No policies selected</h2>
          <p>Select one or more policies from the sidebar to see their projected impact on households and public finances.</p>
        </div>
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="results-loading">
        <div className="loading-spinner"></div>
        <p>Analysing policy impacts...</p>
      </div>
    )
  }

  if (!results) {
    return null
  }

  // Prepare chart data
  const budgetChartData = results.budgetaryImpact.years.map((year, idx) => {
    const dataPoint = { year }
    results.budgetaryImpact.data.forEach(policy => {
      dataPoint[policy.policy] = policy.values[idx]
    })
    return dataPoint
  })

  const povertyChartData = [
    {
      metric: 'Absolute poverty',
      Baseline: results.povertyImpact.absolute.baseline,
      'With policies': results.povertyImpact.absolute.withPolicies
    },
    {
      metric: 'Relative poverty',
      Baseline: results.povertyImpact.relative.baseline,
      'With policies': results.povertyImpact.relative.withPolicies
    }
  ]

  const policyColours = ['#319795', '#5A8FB8', '#B8875A', '#5FB88A', '#4A7BA7', '#C59A5A']

  const formatCurrency = (value) => `£${value.toFixed(2)}bn`
  const formatPercent = (value) => `${value.toFixed(1)}%`
  const formatNumber = (value) => value.toLocaleString('en-GB')

  return (
    <div className="results">
      <section className="results-intro">
        <h2>Analysis overview</h2>
        <p>
          This dashboard analyses the potential impacts of selected budget policies on UK households and public finances.
          The analysis is powered by{' '}
          <a href="https://policyengine.org/uk" target="_blank" rel="noopener noreferrer">
            PolicyEngine UK
          </a>
          , a free, open-source tool for computing the impact of public policy.
        </p>
      </section>

      {/* Household-level impact visualization */}
      <section className="household-impact-section">
        <HouseholdImpactChart
          selectedPolicy={selectedPolicies[0]}
        />
        <div className="household-explanation">
          <p className="explanation-text">
            Each dot represents one household. The chart shows how the selected policy would affect households across different income levels.
            Use the questions on the left to find households similar to yours and see how they would be affected.
          </p>
        </div>
      </section>

      <section className="results-section">
        <h2>Key impacts</h2>
        <div className="impact-cards">
          <div className="impact-card">
            <div className="impact-label">Affected households</div>
            <div className="impact-value">
              <AnimatedNumber
                value={results.affectedHouseholds}
                format={(v) => Math.round(v).toLocaleString('en-GB')}
              />
            </div>
          </div>
          <div className="impact-card">
            <div className="impact-label">Average impact</div>
            <div className="impact-value">
              £<AnimatedNumber
                value={results.averageImpact}
                format={(v) => Math.round(v).toLocaleString('en-GB')}
              />
            </div>
          </div>
          <div className="impact-card">
            <div className="impact-label">Absolute poverty reduction</div>
            <div className="impact-value">
              <AnimatedNumber
                value={results.povertyImpact.absolute.baseline - results.povertyImpact.absolute.withPolicies}
                format={(v) => `${v.toFixed(2)}pp`}
              />
            </div>
          </div>
        </div>
      </section>

      <section className="chart-section">
        <h2>Budgetary impact over time</h2>
        <p className="chart-description">
          Projected revenue or expenditure impact of selected policies from 2025 to 2030, measured in billions of pounds.
        </p>
        <ResponsiveContainer width="100%" height={350}>
          <BarChart
            data={budgetChartData}
            margin={{ top: 20, right: 30, left: 90, bottom: 20 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
            <XAxis dataKey="year" />
            <YAxis
              label={{
                value: 'Impact (£bn)',
                angle: -90,
                position: 'insideLeft',
                dx: -30,
                style: { textAnchor: 'middle' }
              }}
              tickFormatter={formatCurrency}
            />
            <Tooltip
              formatter={(value) => formatCurrency(value)}
              labelFormatter={(label) => `Year: ${label}`}
            />
            <Legend wrapperStyle={{ paddingTop: '20px' }} />
            {results.budgetaryImpact.data.map((policy, idx) => (
              <Bar
                key={policy.policy}
                dataKey={policy.policy}
                fill={policyColours[idx % policyColours.length]}
                name={policy.policy}
              />
            ))}
          </BarChart>
        </ResponsiveContainer>
      </section>

      <section className="chart-section">
        <div className="chart-header">
          <div>
            <h2>Poverty impact</h2>
            <p className="chart-description">
              Comparison of poverty rates before and after implementing selected policies.
            </p>
          </div>
        </div>
        <ResponsiveContainer width="100%" height={350}>
          <BarChart
            data={povertyChartData}
            margin={{ top: 20, right: 30, left: 90, bottom: 20 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
            <XAxis dataKey="metric" />
            <YAxis
              label={{
                value: 'Poverty rate (%)',
                angle: -90,
                position: 'insideLeft',
                dx: -30,
                style: { textAnchor: 'middle' }
              }}
              tickFormatter={formatPercent}
            />
            <Tooltip
              formatter={(value) => formatPercent(value)}
            />
            <Legend wrapperStyle={{ paddingTop: '20px' }} />
            <Bar dataKey="Baseline" fill="#9CA3AF" name="Baseline" />
            <Bar dataKey="With policies" fill="#319795" name="With policies" />
          </BarChart>
        </ResponsiveContainer>
      </section>
    </div>
  )
}

export default Results
