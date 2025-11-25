import { useState } from 'react'
import { ComposedChart, Bar, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine } from 'recharts'
import YearSlider from './YearSlider'
import './WaterfallChart.css'

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

function WaterfallChart({ rawData, selectedPolicies }) {
  const [internalYear, setInternalYear] = useState(2026)

  // Build chart data for internal year
  const POLICIES = [
    { id: 'two_child_limit', name: '2 child limit repeal' },
    { id: 'income_tax_increase_2pp', name: 'Income tax increase (basic and higher +2pp)' },
    { id: 'threshold_freeze_extension', name: 'Threshold freeze extension' },
    { id: 'ni_rate_reduction', name: 'National Insurance rate reduction' },
    { id: 'zero_vat_energy', name: 'Zero-rate VAT on domestic energy' },
    { id: 'salary_sacrifice_cap', name: 'Salary sacrifice cap' }
  ]

  const waterfallDeciles = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10']
  const waterfallSelectedYear = rawData ? rawData.filter(row =>
    parseInt(row.year) === internalYear && row.decile !== 'all' && selectedPolicies.includes(row.reform_id)
  ) : []

  const data = waterfallDeciles.map(decile => {
    const dataPoint = { decile }
    let netChange = 0
    POLICIES.forEach(policy => {
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

  // Calculate y-axis domain across ALL years to keep scale consistent
  const calculateYAxisDomain = () => {
    const allYears = [2026, 2027, 2028, 2029]
    let minValue = 0
    let maxValue = 0

    allYears.forEach(year => {
      const yearData = rawData ? rawData.filter(row =>
        parseInt(row.year) === year && row.decile !== 'all' && selectedPolicies.includes(row.reform_id)
      ) : []

      waterfallDeciles.forEach(decile => {
        let positiveSum = 0
        let negativeSum = 0

        POLICIES.forEach(policy => {
          const isSelected = selectedPolicies.includes(policy.id)
          const dataRow = yearData.find(row =>
            row.reform_id === policy.id && row.decile === decile
          )
          const value = isSelected && dataRow ? parseFloat(dataRow.avg_change) : 0
          if (value > 0) positiveSum += value
          else negativeSum += value
        })

        minValue = Math.min(minValue, negativeSum)
        maxValue = Math.max(maxValue, positiveSum)
      })
    })

    // Add 10% padding to both ends
    const range = maxValue - minValue
    const padding = range * 0.1

    return [minValue - padding, maxValue + padding]
  }

  const yAxisDomain = calculateYAxisDomain()

  if (!rawData || rawData.length === 0) {
    return (
      <div className="waterfall-chart">
        <h2>Absolute impact by income decile</h2>
        <p className="chart-description">
          This chart shows the absolute change in net income by decile, measured in pounds per year.
        </p>
        <div style={{ padding: '60px 20px', textAlign: 'center', color: '#666', backgroundColor: '#f9f9f9', borderRadius: '8px' }}>
          <p style={{ margin: 0, fontSize: '0.95rem' }}>No data available yet for this metric</p>
        </div>
      </div>
    )
  }

  const formatCurrency = (value) => `£${value.toFixed(0)}`

  // Check which policies have non-zero values
  const hasNonZeroValues = (policyName) => {
    return data.some(d => Math.abs(d[policyName] || 0) > 0.01)
  }

  const activePolicies = ALL_POLICY_NAMES.filter(hasNonZeroValues)

  return (
    <div className="waterfall-chart">
      <h2>Absolute impact by income decile</h2>
      <p className="chart-description">
        This chart shows the absolute change in net income by decile, measured in pounds per year. This represents the actual cash amount gained or lost by households in each decile.
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
            tick={{ fontSize: 11, fill: '#666' }}
            label={{
              value: 'Income decile',
              position: 'insideBottom',
              offset: -10,
              style: { fill: '#374151', fontSize: 12, fontWeight: 500 }
            }}
          />
          <YAxis
            domain={yAxisDomain}
            tickFormatter={formatCurrency}
            tick={{ fontSize: 11, fill: '#666' }}
            label={{
              value: 'Average change per household (£)',
              angle: -90,
              position: 'insideLeft',
              dx: -30,
              style: { textAnchor: 'middle', fill: '#374151', fontSize: 12, fontWeight: 500 }
            }}
          />
          <ReferenceLine y={0} stroke="#666" strokeWidth={1} />
          <Tooltip
            formatter={(value, name) => [formatCurrency(value), name === 'netChange' ? 'Net change' : name]}
            labelFormatter={(label) => `Decile: ${label}`}
            contentStyle={{ background: 'white', border: '1px solid #e5e7eb', borderRadius: '6px', fontSize: '12px' }}
            wrapperStyle={{ top: '-120px', left: '50%', transform: 'translateX(-50%)' }}
            cursor={{ fill: 'rgba(49, 151, 149, 0.1)' }}
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

      <YearSlider selectedYear={internalYear} onYearChange={setInternalYear} />
    </div>
  )
}

export default WaterfallChart
