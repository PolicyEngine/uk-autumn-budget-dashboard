import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import './BudgetaryImpactChart.css'

function BudgetaryImpactChart({ data, policyColors }) {
  if (!data || data.length === 0) return null

  const formatCurrency = (value) => `£${value.toFixed(2)}bn`

  return (
    <div className="budgetary-impact-chart">
      <h2>Budgetary impact through years</h2>
      <p className="chart-description">
        Projected revenue or expenditure impact of selected policies from 2026 to 2029, measured in billions of pounds.
      </p>

      <ResponsiveContainer width="100%" height={300}>
        <BarChart
          data={data}
          margin={{ top: 15, right: 20, left: 70, bottom: 15 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
          <XAxis
            dataKey="year"
            tick={{ fontSize: 11, fill: '#666' }}
          />
          <YAxis
            label={{
              value: 'Impact (£bn)',
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
            labelFormatter={(label) => `Year: ${label}`}
            contentStyle={{ background: 'white', border: '1px solid #e5e7eb', borderRadius: '6px' }}
          />
          <Legend
            wrapperStyle={{ paddingTop: '20px' }}
            iconType="rect"
          />
          {Object.keys(data[0] || {}).filter(key => key !== 'year').map((policyKey, idx) => (
            <Bar
              key={policyKey}
              dataKey={policyKey}
              fill={policyColors[idx % policyColors.length]}
              name={policyKey}
              animationDuration={800}
              animationBegin={0}
            />
          ))}
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

export default BudgetaryImpactChart
