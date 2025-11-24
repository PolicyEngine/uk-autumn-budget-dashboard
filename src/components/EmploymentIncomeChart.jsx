import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import './EmploymentIncomeChart.css'

function EmploymentIncomeChart() {
  // Generate data showing relationship between employment income and net household income
  // The curve reflects tax and benefit system effects
  const generateData = () => {
    const data = []
    for (let employment = 0; employment <= 200000; employment += 5000) {
      // Simplified model: net income is affected by taxes and benefits
      let net
      if (employment === 0) {
        net = 5000 // Benefits only
      } else if (employment <= 12570) {
        net = employment + 3000 // Below personal allowance + some benefits
      } else if (employment <= 50270) {
        // Basic rate: 20% tax
        const taxableIncome = employment - 12570
        const tax = taxableIncome * 0.2
        net = employment - tax
      } else if (employment <= 125140) {
        // Higher rate: 40% on income above 50270
        const basicRateTax = (50270 - 12570) * 0.2
        const higherRateIncome = employment - 50270
        const higherRateTax = higherRateIncome * 0.4
        net = employment - basicRateTax - higherRateTax
      } else {
        // Additional rate: 45% on income above 125140
        const basicRateTax = (50270 - 12570) * 0.2
        const higherRateTax = (125140 - 50270) * 0.4
        const additionalRateIncome = employment - 125140
        const additionalRateTax = additionalRateIncome * 0.45
        net = employment - basicRateTax - higherRateTax - additionalRateTax
      }

      data.push({
        employment,
        net: Math.round(net)
      })
    }
    return data
  }

  const data = generateData()

  const formatCurrency = (value) => {
    if (value >= 1000) {
      return `£${(value / 1000).toFixed(0)}k`
    }
    return `£${value}`
  }

  return (
    <div className="employment-income-chart">
      <h2>Employment income to net income</h2>
      <p className="chart-description">
        Relationship between household head employment income and total household net income
      </p>

      <ResponsiveContainer width="100%" height={300}>
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
            dataKey="net"
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
          <Line
            type="monotone"
            dataKey="net"
            stroke="#4A7BA7"
            strokeWidth={2}
            dot={false}
            name="Net income"
            animationDuration={800}
            animationBegin={0}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

export default EmploymentIncomeChart
