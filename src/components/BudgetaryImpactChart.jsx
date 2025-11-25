import { ComposedChart, Bar, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine } from 'recharts'
import './BudgetaryImpactChart.css'

const POLICY_COLORS = {
  // COSTS (negative impacts - distinct warm/neutral tones)
  '2 child limit repeal': '#991B1B',              // Deep red - cost to treasury
  'National Insurance rate reduction': '#A16207',  // Dark amber/gold - cost to treasury
  'Zero-rate VAT on domestic energy': '#EA580C',   // Bright orange - VAT specific (clearly distinct from red)

  // REVENUE (positive impacts - distinct cool tones)
  'Income tax increase (basic and higher +2pp)': '#64748B',  // Lighter slate - IT specific, more visible
  'Threshold freeze extension': '#14532D',                   // Deep forest green - revenue raiser
  'Salary sacrifice cap': '#1E3A8A'                          // Navy blue - revenue raiser
}

const ALL_POLICY_NAMES = [
  '2 child limit repeal',
  'Income tax increase (basic and higher +2pp)',
  'Threshold freeze extension',
  'National Insurance rate reduction',
  'Zero-rate VAT on domestic energy',
  'Salary sacrifice cap'
]

function BudgetaryImpactChart({ data }) {
  if (!data || data.length === 0) return null

  const formatCurrency = (value) => `£${value.toFixed(2)}bn`

  // Check which policies have non-zero values for legend/tooltip
  const hasNonZeroValues = (policyName) => {
    return data.some(d => Math.abs(d[policyName] || 0) > 0.001)
  }

  const activePolicies = ALL_POLICY_NAMES.filter(hasNonZeroValues)

  // Calculate dynamic y-axis domain based on actual data
  const calculateYAxisDomain = () => {
    let minValue = 0
    let maxValue = 0

    data.forEach(yearData => {
      let positiveSum = 0
      let negativeSum = 0

      ALL_POLICY_NAMES.forEach(policyName => {
        const value = yearData[policyName] || 0
        if (value > 0) positiveSum += value
        else negativeSum += value
      })

      minValue = Math.min(minValue, negativeSum)
      maxValue = Math.max(maxValue, positiveSum)
    })

    // Add 10% padding to both ends
    const range = maxValue - minValue
    const padding = range * 0.1

    return [minValue - padding, maxValue + padding]
  }

  const yAxisDomain = calculateYAxisDomain()

  return (
    <div className="budgetary-impact-chart">
      <h2>Revenue impact</h2>
      <p className="chart-description">
        This chart shows the annual budgetary impact from 2026 to 2029, measured in billions of pounds. Positive values indicate revenue gains for the Government, whilst negative values indicate costs to the Treasury.
      </p>

      <ResponsiveContainer width="100%" height={400}>
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
            domain={yAxisDomain}
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
            formatter={(value, name) => [formatCurrency(value), name === 'netImpact' ? 'Net impact' : name]}
            labelFormatter={(label) => `Year: ${label}`}
            contentStyle={{ background: 'white', border: '1px solid #e5e7eb', borderRadius: '6px' }}
            wrapperStyle={{ top: '-120px', left: '50%', transform: 'translateX(-50%)' }}
            cursor={{ fill: 'rgba(49, 151, 149, 0.1)' }}
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
          <ReferenceLine y={0} stroke="#374151" strokeWidth={1} />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  )
}

export default BudgetaryImpactChart
