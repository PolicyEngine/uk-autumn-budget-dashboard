import { useState, useEffect } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import './EmploymentIncomeChart.css'

function EmploymentIncomeChart({ selectedPolicies, selectedYear = 2026 }) {
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Load income curve data from CSV
    fetch('/data/income_curve.csv')
      .then(response => response.text())
      .then(csvText => {
        const lines = csvText.trim().split('\n')
        const headers = lines[0].split(',')

        // Parse all income curve data
        const allData = []
        for (let i = 1; i < lines.length; i++) {
          const values = lines[i].split(',')
          const row = {}
          headers.forEach((header, index) => {
            row[header] = values[index]
          })
          allData.push(row)
        }

        // Filter by selected year
        const yearFilteredData = allData.filter(row => parseInt(row.year) === selectedYear)

        // Get unique employment income values (up to 100k)
        const employmentIncomes = [...new Set(
          yearFilteredData
            .filter(row => parseFloat(row.employment_income) <= 100000)
            .map(row => parseFloat(row.employment_income))
        )].sort((a, b) => a - b)

        // Build chart data: for each employment income, compute baseline and combined reform
        const chartData = employmentIncomes.map(income => {
          // Get baseline from any row (it's the same across reforms)
          const baselineRow = yearFilteredData.find(row =>
            parseFloat(row.employment_income) === income
          )
          const baseline = baselineRow ? parseFloat(baselineRow.baseline_net_income) : 0

          // Sum up the income changes from each selected policy
          let totalIncomeChange = 0
          selectedPolicies.forEach(policyId => {
            const policyRow = yearFilteredData.find(row =>
              row.reform_id === policyId && parseFloat(row.employment_income) === income
            )
            if (policyRow) {
              const reformIncome = parseFloat(policyRow.reform_net_income)
              const baselineIncome = parseFloat(policyRow.baseline_net_income)
              totalIncomeChange += (reformIncome - baselineIncome)
            }
          })

          return {
            employment: income,
            baseline: baseline,
            reform: baseline + totalIncomeChange
          }
        })

        setData(chartData)
        setLoading(false)
      })
      .catch(error => {
        console.error('Error loading income curve data:', error)
        setLoading(false)
      })
  }, [selectedPolicies, selectedYear])

  const formatCurrency = (value) => {
    if (value >= 1000) {
      return `£${(value / 1000).toFixed(0)}k`
    }
    return `£${value.toFixed(0)}`
  }

  if (loading) {
    return (
      <div className="employment-income-chart">
        <h2>Household net income analysis</h2>
        <p className="chart-description">
          This chart shows the relationship between household head employment income and total household net income in 2026-27.
        </p>
        <div style={{ textAlign: 'center', padding: '40px', color: '#666' }}>
          Loading income curve data...
        </div>
      </div>
    )
  }

  return (
    <div className="employment-income-chart">
      <h2>Household net income analysis</h2>
      <p className="chart-description">
        This chart models a household with 2 adults (both age 40) and 3 children (ages 7, 5, and 3) in 2026-27. The primary earner contributes £10,000 annually to their pension. Baseline shows current policy, reform shows impact after selected changes.
      </p>

      <ResponsiveContainer width="100%" height={430}>
        <LineChart
          data={data}
          margin={{ top: 25, right: 30, left: 20, bottom: 60 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            dataKey="employment"
            type="number"
            label={{
              value: 'Household head employment income',
              position: 'insideBottom',
              offset: -5,
              style: { textAnchor: 'middle', fill: '#374151', fontSize: 13, fontWeight: 500 }
            }}
            tickFormatter={formatCurrency}
            tick={{ fontSize: 12, fill: '#6b7280' }}
            height={60}
            ticks={[0, 20000, 40000, 60000, 80000, 100000]}
            domain={[0, 100000]}
          />
          <YAxis
            label={{
              value: 'Household net income',
              angle: -90,
              position: 'insideLeft',
              dx: 10,
              style: { textAnchor: 'middle', fill: '#374151', fontSize: 13, fontWeight: 500 }
            }}
            tickFormatter={formatCurrency}
            tick={{ fontSize: 12, fill: '#6b7280' }}
            width={80}
            ticks={[0, 20000, 40000, 60000, 80000]}
            domain={[0, 80000]}
          />
          <Tooltip
            formatter={(value) => formatCurrency(value)}
            labelFormatter={(label) => `Employment income: ${formatCurrency(label)}`}
            contentStyle={{
              background: 'white',
              border: '1px solid #d1d5db',
              borderRadius: '8px',
              padding: '12px',
              boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
            }}
            labelStyle={{ fontWeight: 600, marginBottom: '4px' }}
          />
          <Legend
            wrapperStyle={{ paddingTop: '15px', paddingBottom: '0px' }}
            iconType="line"
            iconSize={18}
            formatter={(value) => <span style={{ fontSize: '13px', fontWeight: 500, color: '#374151' }}>{value}</span>}
            verticalAlign="bottom"
            align="center"
          />
          <Line
            type="monotone"
            dataKey="baseline"
            stroke="#9CA3AF"
            strokeWidth={3}
            dot={false}
            name="Baseline"
            animationDuration={500}
            animationBegin={0}
          />
          <Line
            type="monotone"
            dataKey="reform"
            stroke="#319795"
            strokeWidth={3}
            strokeDasharray="8 4"
            dot={false}
            name="Reform"
            animationDuration={500}
            animationBegin={0}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

export default EmploymentIncomeChart
