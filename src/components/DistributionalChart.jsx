import { ComposedChart, Bar, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine } from 'recharts'
import './DistributionalChart.css'

const POLICY_COLORS = {
  '2 child limit repeal': '#319795',
  'Income tax increase (basic and higher +2pp)': '#5A8FB8',
  'Threshold freeze extension': '#B8875A',
  'National Insurance rate reduction': '#5FB88A'
}

const ALL_POLICY_NAMES = [
  '2 child limit repeal',
  'Income tax increase (basic and higher +2pp)',
  'Threshold freeze extension',
  'National Insurance rate reduction'
]

function DistributionalChart({ data }) {
  const formatPercent = (value) => `${value.toFixed(2)}%`

  // Remove "st", "nd", "rd", "th" from decile labels
  const formatDecile = (value) => {
    return value.replace(/st|nd|rd|th/g, '')
  }

  if (!data || data.length === 0) {
    return (
      <div className="distributional-chart">
        <h2>Impact by income decile — relative</h2>
        <p className="chart-description">
          Average percentage change in net income for each income decile, from the 1st (lowest income) to the 10th (highest income).
        </p>
        <div style={{ padding: '60px 20px', textAlign: 'center', color: '#666', backgroundColor: '#f9f9f9', borderRadius: '8px' }}>
          <p style={{ margin: 0, fontSize: '0.95rem' }}>No data available yet for this metric</p>
        </div>
      </div>
    )
  }

  // Check which policies have non-zero values
  const hasNonZeroValues = (policyName) => {
    return data.some(d => Math.abs(d[policyName] || 0) > 0.0001)
  }

  const activePolicies = ALL_POLICY_NAMES.filter(hasNonZeroValues)

  return (
    <div className="distributional-chart">
      <h2>Impact by income decile — relative</h2>
      <p className="chart-description">
        Average percentage change in net income for each income decile, from the 1st (lowest income)
        to the 10th (highest income). This shows the proportional impact of reforms
        relative to baseline income. Positive values indicate income gains; negative values indicate losses.
      </p>

      <ResponsiveContainer width="100%" height={420}>
        <ComposedChart
          data={data}
          margin={{ top: 20, right: 30, left: 70, bottom: 20 }}
          stackOffset="sign"
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
          <XAxis
            dataKey="decile"
            tickFormatter={formatDecile}
            tick={{ fontSize: 12, fill: '#666' }}
            label={{
              value: 'Income decile',
              position: 'insideBottom',
              offset: -10,
              style: { fill: '#374151', fontSize: 12, fontWeight: 500 }
            }}
          />
          <YAxis
            label={{
              value: 'Percentage change in net income (%)',
              angle: -90,
              position: 'insideLeft',
              dx: -30,
              style: { textAnchor: 'middle', fill: '#374151', fontSize: 13, fontWeight: 500 }
            }}
            tickFormatter={formatPercent}
            tick={{ fontSize: 12, fill: '#666' }}
          />
          <ReferenceLine y={0} stroke="#666" strokeWidth={1} />
          <Tooltip
            formatter={(value, name) => [formatPercent(value), name === 'netChange' ? 'Net change' : name]}
            labelFormatter={(label) => `${label} decile`}
            contentStyle={{ background: 'white', border: '1px solid #e5e7eb', borderRadius: '6px' }}
          />
          <Legend
            wrapperStyle={{ paddingTop: '20px' }}
            iconType="rect"
            payload={[
              ...activePolicies.map(name => ({
                value: name,
                type: 'rect',
                color: POLICY_COLORS[name]
              })),
              ...(activePolicies.length > 1 ? [{
                value: 'Net change',
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
            dataKey="netChange"
            stroke="#1D4044"
            strokeWidth={2}
            dot={{ fill: '#1D4044', strokeWidth: 2 }}
            name="netChange"
            animationDuration={500}
            hide={activePolicies.length <= 1}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  )
}

export default DistributionalChart
