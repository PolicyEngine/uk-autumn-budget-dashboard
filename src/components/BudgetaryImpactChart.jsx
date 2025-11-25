import { ComposedChart, Bar, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine } from 'recharts'
import './BudgetaryImpactChart.css'

const POLICY_COLORS = {
  '2 child limit repeal': '#319795',
  'Basic rate increase by 1 percentage point': '#5A8FB8',
  'Threshold freeze extension': '#B8875A'
}

const ALL_POLICY_NAMES = [
  '2 child limit repeal',
  'Basic rate increase by 1 percentage point',
  'Threshold freeze extension'
]

function BudgetaryImpactChart({ data }) {
  if (!data || data.length === 0) return null

  const formatCurrency = (value) => `£${value.toFixed(2)}bn`

  // Check which policies have non-zero values for legend/tooltip
  const hasNonZeroValues = (policyName) => {
    return data.some(d => Math.abs(d[policyName] || 0) > 0.001)
  }

  const activePolicies = ALL_POLICY_NAMES.filter(hasNonZeroValues)

  return (
    <div className="budgetary-impact-chart">
      <h2>Fiscal impact over time</h2>
      <p className="chart-description">
        Annual budgetary impact of selected policies from 2026 to 2029. Positive values indicate revenue gains; negative values indicate costs.
      </p>

      <ResponsiveContainer width="100%" height={300}>
        <ComposedChart
          data={data}
          margin={{ top: 15, right: 20, left: 70, bottom: 15 }}
          stackOffset="sign"
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
          <ReferenceLine y={0} stroke="#666" strokeWidth={1} />
          <Tooltip
            formatter={(value, name) => [formatCurrency(value), name === 'netImpact' ? 'Net impact' : name]}
            labelFormatter={(label) => `Year: ${label}`}
            contentStyle={{ background: 'white', border: '1px solid #e5e7eb', borderRadius: '6px' }}
          />
          <Legend
            wrapperStyle={{ paddingTop: '20px' }}
            iconType="rect"
            formatter={(value) => value === 'netImpact' ? 'Net impact' : value}
            payload={[
              ...activePolicies.map(name => ({
                value: name,
                type: 'rect',
                color: POLICY_COLORS[name]
              })),
              ...(activePolicies.length > 1 ? [{
                value: 'Net impact',
                type: 'line',
                color: '#1D4044'
              }] : [])
            ]}
          />
          {ALL_POLICY_NAMES.map((policyName) => (
            <Bar
              key={policyName}
              dataKey={policyName}
              fill={POLICY_COLORS[policyName]}
              name={policyName}
              stackId="stack"
              animationDuration={500}
              animationBegin={0}
              hide={!hasNonZeroValues(policyName)}
            />
          ))}
          <Line
            type="monotone"
            dataKey="netImpact"
            stroke="#1D4044"
            strokeWidth={2}
            dot={{ fill: '#1D4044', strokeWidth: 2 }}
            name="netImpact"
            animationDuration={500}
            hide={activePolicies.length <= 1}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  )
}

export default BudgetaryImpactChart
