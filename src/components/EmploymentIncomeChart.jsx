import { useState, useEffect } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import './EmploymentIncomeChart.css'

function EmploymentIncomeChart() {
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Load income curve data from CSV
    fetch('/data/reform-results.csv')
      .then(response => response.text())
      .then(csvText => {
        const lines = csvText.trim().split('\n')
        const headers = lines[0].split(',')

        // Parse income curve data
        const incomeCurveData = []

        for (let i = 1; i < lines.length; i++) {
          const values = lines[i].split(',')
          const row = {}
          headers.forEach((header, index) => {
            row[header] = values[index]
          })

          // Filter for income_curve metric
          if (row.metric_type === 'income_curve' && row.reform_id === 'two_child_limit') {
            incomeCurveData.push({
              employment_income: parseFloat(row.employment_income),
              category: row.category,
              net_income: parseFloat(row.value)
            })
          }
        }

        // Group by employment income
        const groupedData = {}
        incomeCurveData.forEach(item => {
          const empIncome = item.employment_income
          if (!groupedData[empIncome]) {
            groupedData[empIncome] = { employment: empIncome }
          }
          if (item.category === 'baseline') {
            groupedData[empIncome].baseline = item.net_income
          } else if (item.category === 'reform') {
            groupedData[empIncome].reform = item.net_income
          }
        })

        // Convert to array and sort
        const chartData = Object.values(groupedData).sort((a, b) => a.employment - b.employment)

        setData(chartData)
        setLoading(false)
      })
      .catch(error => {
        console.error('Error loading income curve data:', error)
        setLoading(false)
      })
  }, [])

  const formatCurrency = (value) => {
    if (value >= 1000) {
      return `£${(value / 1000).toFixed(0)}k`
    }
    return `£${value}`
  }

  if (loading) {
    return (
      <div className="employment-income-chart">
        <h2>Employment income to net income</h2>
        <p className="chart-description">
          Relationship between household head employment income and total household net income
        </p>
        <div style={{ textAlign: 'center', padding: '40px', color: '#666' }}>
          Loading income curve data...
        </div>
      </div>
    )
  }

  return (
    <div className="employment-income-chart">
      <h2>Employment income to net income</h2>
      <p className="chart-description">
        Relationship between household head employment income and total household net income
      </p>

      <ResponsiveContainer width="100%" height={350}>
        <LineChart
          data={data}
          margin={{ top: 15, right: 20, left: 70, bottom: 15 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
          <XAxis
            dataKey="employment"
            label={{
              value: 'Household head employment income',
              position: 'insideBottom',
              offset: -10,
              style: { textAnchor: 'middle', fill: '#374151', fontSize: 12, fontWeight: 500 }
            }}
            tickFormatter={formatCurrency}
            tick={{ fontSize: 11, fill: '#666' }}
          />
          <YAxis
            label={{
              value: 'Household net income',
              angle: -90,
              position: 'insideLeft',
              dx: -30,
              style: { textAnchor: 'middle', fill: '#374151', fontSize: 12, fontWeight: 500 }
            }}
            tickFormatter={formatCurrency}
            tick={{ fontSize: 11, fill: '#666' }}
          />
          <Tooltip
            formatter={(value) => formatCurrency(value)}
            labelFormatter={(label) => `Employment income: ${formatCurrency(label)}`}
            contentStyle={{ background: 'white', border: '1px solid #e5e7eb', borderRadius: '6px' }}
          />
          <Legend
            wrapperStyle={{ paddingTop: '20px' }}
            iconType="line"
          />
          <Line
            type="monotone"
            dataKey="baseline"
            stroke="#9CA3AF"
            strokeWidth={2}
            dot={false}
            name="Baseline"
            animationDuration={800}
            animationBegin={0}
          />
          <Line
            type="monotone"
            dataKey="reform"
            stroke="#4A7BA7"
            strokeWidth={2}
            strokeDasharray="5 5"
            dot={false}
            name="Reform"
            animationDuration={800}
            animationBegin={0}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

export default EmploymentIncomeChart
