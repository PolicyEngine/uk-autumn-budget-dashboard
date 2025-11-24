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
      return `£${(value / 1000).toFixed(1)}k`
    }
    return `£${value.toFixed(1)}`
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

      <ResponsiveContainer width="100%" height={500}>
        <LineChart
          data={data}
          margin={{ top: 25, right: 30, left: 20, bottom: 80 }}
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
            ticks={[0, 20000, 40000, 60000, 80000, 100000, 120000, 140000, 160000, 180000, 200000]}
            domain={[0, 200000]}
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
            ticks={[0, 20000, 40000, 60000, 80000, 100000, 120000, 140000]}
            domain={[0, 140000]}
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
            animationDuration={800}
            animationBegin={0}
          />
          <Line
            type="monotone"
            dataKey="reform"
            stroke="#4A7BA7"
            strokeWidth={3}
            strokeDasharray="8 4"
            dot={false}
            name="Reform"
            animationDuration={800}
            animationBegin={100}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

export default EmploymentIncomeChart
