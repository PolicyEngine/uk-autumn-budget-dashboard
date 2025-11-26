import { useState } from 'react'
import { ComposedChart, Bar, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine } from 'recharts'
import YearSlider from './YearSlider'
import './DistributionalChart.css'

const POLICY_COLORS = {
  // GOOD for households (teal spectrum) - these increase household income
  'National Insurance rate reduction': '#0F766E',  // Darkest teal (biggest ~£12bn)
  'Zero-rate VAT on domestic energy': '#14B8A6',   // Medium teal (~£3.3bn)
  '2 child limit repeal': '#2DD4BF',               // Light teal (~£3bn)
  'Fuel duty freeze': '#5EEAD4',                   // Lightest teal (smallest ~£1.5bn)

  // BAD for households (red spectrum) - these decrease household income
  'Income tax increase (basic and higher +2pp)': '#991B1B',  // Darkest red (biggest ~£20bn)
  'Threshold freeze extension': '#B91C1C',                   // Dark red (~£4-7bn)
  'Salary sacrifice cap': '#F87171'                          // Light red (smallest ~£1.4bn)
}

// Order: biggest magnitude closest to zero line (darkest colours at zero)
const ALL_POLICY_NAMES = [
  // Good for households (positive, teal) - biggest at bottom (closest to zero), smallest at top
  'National Insurance rate reduction',
  'Zero-rate VAT on domestic energy',
  '2 child limit repeal',
  'Fuel duty freeze',
  // Bad for households (negative, red) - biggest at top (closest to zero), smallest at bottom
  'Income tax increase (basic and higher +2pp)',
  'Threshold freeze extension',
  'Salary sacrifice cap'
]

function DistributionalChart({ rawData, selectedPolicies }) {
  const [internalYear, setInternalYear] = useState(2026)

  const formatPercent = (value) => `${value.toFixed(1)}%`

  // Remove "st", "nd", "rd", "th" from decile labels
  const formatDecile = (value) => {
    return value.replace(/st|nd|rd|th/g, '')
  }

  // Build chart data for internal year
  const POLICIES = [
    { id: 'two_child_limit', name: '2 child limit repeal' },
    { id: 'income_tax_increase_2pp', name: 'Income tax increase (basic and higher +2pp)' },
    { id: 'threshold_freeze_extension', name: 'Threshold freeze extension' },
    { id: 'ni_rate_reduction', name: 'National Insurance rate reduction' },
    { id: 'zero_vat_energy', name: 'Zero-rate VAT on domestic energy' },
    { id: 'salary_sacrifice_cap', name: 'Salary sacrifice cap' },
    { id: 'fuel_duty_freeze', name: 'Fuel duty freeze' }
  ]

  const decileOrder = ['1st', '2nd', '3rd', '4th', '5th', '6th', '7th', '8th', '9th', '10th']
  const distributionalSelectedYear = rawData ? rawData.filter(row =>
    parseInt(row.year) === internalYear && selectedPolicies.includes(row.reform_id)
  ) : []

  // Policies that need sign flip (raise revenue but data shows positive household impact incorrectly)
  const FLIP_SIGN_POLICIES = ['salary_sacrifice_cap']

  const data = decileOrder.map(decile => {
    const dataPoint = { decile }
    let netChange = 0
    POLICIES.forEach(policy => {
      const isSelected = selectedPolicies.includes(policy.id)
      const dataRow = distributionalSelectedYear.find(row =>
        row.reform_id === policy.id && row.decile === decile
      )
      let value = isSelected && dataRow ? parseFloat(dataRow.value) : 0
      // Flip sign for policies with incorrect data sign
      if (FLIP_SIGN_POLICIES.includes(policy.id)) {
        value = -value
      }
      dataPoint[policy.name] = value
      netChange += value
    })
    dataPoint.netChange = netChange
    return dataPoint
  })

  // Calculate y-axis domain across ALL years, symmetrical around zero
  const calculateYAxisDomain = () => {
    const allYears = [2026, 2027, 2028, 2029]
    let minValue = 0
    let maxValue = 0

    allYears.forEach(year => {
      const yearData = rawData ? rawData.filter(row =>
        parseInt(row.year) === year && selectedPolicies.includes(row.reform_id)
      ) : []

      decileOrder.forEach(decile => {
        let positiveSum = 0
        let negativeSum = 0

        POLICIES.forEach(policy => {
          const isSelected = selectedPolicies.includes(policy.id)
          const dataRow = yearData.find(row =>
            row.reform_id === policy.id && row.decile === decile
          )
          let value = isSelected && dataRow ? parseFloat(dataRow.value) : 0
          // Flip sign for policies with incorrect data sign
          if (FLIP_SIGN_POLICIES.includes(policy.id)) {
            value = -value
          }
          if (value > 0) positiveSum += value
          else negativeSum += value
        })

        minValue = Math.min(minValue, negativeSum)
        maxValue = Math.max(maxValue, positiveSum)
      })
    })

    // Round to nice numbers and make symmetrical
    const roundToNice = (val) => {
      if (val <= 1) return Math.ceil(val * 2) / 2  // Round to 0.5
      if (val <= 5) return Math.ceil(val)          // Round to 1
      return Math.ceil(val / 2) * 2                // Round to 2
    }

    const maxAbs = Math.max(Math.abs(minValue), Math.abs(maxValue)) + 0.2
    const rounded = roundToNice(maxAbs)

    return [-rounded, rounded]
  }

  const yAxisDomain = calculateYAxisDomain()

  if (!rawData || rawData.length === 0) {
    return (
      <div className="distributional-chart">
        <h2>Relative impact by income decile</h2>
        <p className="chart-description">
          This chart shows the percentage change in net income by decile, displaying the proportional impact relative to baseline income.
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
      <h2>Relative impact by income decile</h2>
      <p className="chart-description">
        This chart shows the percentage change in net income by decile, displaying the proportional impact relative to baseline income. Positive values indicate gains; negative values indicate losses.
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
            domain={yAxisDomain}
            label={{
              value: 'Percentage change in net income (%)',
              angle: -90,
              position: 'insideLeft',
              dx: -30,
              style: { textAnchor: 'middle', fill: '#374151', fontSize: 13, fontWeight: 500 }
            }}
            tickFormatter={formatPercent}
            tick={{ fontSize: 12, fill: '#666' }}
            ticks={(() => {
              const [min, max] = yAxisDomain
              const range = max - min
              let interval = 0.5
              if (range > 4) interval = 1
              if (range > 10) interval = 2
              const ticks = []
              for (let i = min; i <= max + 0.001; i += interval) {
                ticks.push(Math.round(i * 10) / 10)
              }
              if (!ticks.includes(0)) ticks.push(0)
              return ticks.sort((a, b) => a - b)
            })()}
          />
          <ReferenceLine y={0} stroke="#666" strokeWidth={1} />
          <Tooltip
            formatter={(value, name) => [formatPercent(value), name === 'netChange' ? 'Net change' : name]}
            labelFormatter={(label) => `${label} decile`}
            contentStyle={{ background: 'white', border: '1px solid #e5e7eb', borderRadius: '6px' }}
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
                color: '#FBBF24'
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
            stroke="#FBBF24"
            strokeWidth={3}
            dot={{ fill: '#FBBF24', stroke: '#92400E', strokeWidth: 2, r: 5 }}
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

export default DistributionalChart
