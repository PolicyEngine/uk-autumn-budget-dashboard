import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine, LabelList } from 'recharts'
import './DistributionalChart.css'

function DistributionalChart({ data }) {
  const formatPercent = (value) => `${value.toFixed(1)}%`

  // Remove "st", "nd", "rd", "th" from decile labels
  const formatDecile = (value) => {
    return value.replace(/st|nd|rd|th/g, '')
  }

  // Calculate Y-axis domain for better space utilization
  const getYAxisDomain = () => {
    if (!data || data.length === 0) return [0, 'auto']

    const values = data.map(d => d.percentChange)
    const maxValue = Math.max(...values)
    const minValue = Math.min(...values, 0) // Include 0 if all values are positive

    // Add 10% padding to the top
    const topPadding = maxValue * 0.1
    const bottomPadding = minValue < 0 ? Math.abs(minValue) * 0.1 : 0

    return [minValue - bottomPadding, maxValue + topPadding]
  }

  // Generate exactly 5 evenly spaced ticks
  const getYAxisTicks = () => {
    const [min, max] = getYAxisDomain()
    const range = max - min
    const step = range / 4 // 4 intervals = 5 ticks
    return [
      min,
      min + step,
      min + step * 2,
      min + step * 3,
      max
    ]
  }

  if (!data || data.length === 0) {
    return (
      <div className="distributional-chart">
        <h2>Impact by income decile — relative</h2>
        <p className="chart-description">
          Average percentage change in net income for each income decile, from the poorest 10% (1st) to the richest 10% (10th) of households.
        </p>
        <div style={{ padding: '60px 20px', textAlign: 'center', color: '#666', backgroundColor: '#f9f9f9', borderRadius: '8px' }}>
          <p style={{ margin: 0, fontSize: '0.95rem' }}>No data available yet for this metric</p>
        </div>
      </div>
    )
  }

  return (
    <div className="distributional-chart">
      <h2>Impact by income decile — relative</h2>
      <p className="chart-description">
        Average percentage change in net income for each income decile, from the poorest 10% (1st) to the richest 10% (10th) of households.
      </p>

      <ResponsiveContainer width="100%" height={420}>
        <BarChart
          data={data}
          margin={{ top: 20, right: 30, left: 30, bottom: 20 }}
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
            domain={getYAxisDomain()}
            ticks={getYAxisTicks()}
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
          <Tooltip
            formatter={(value) => formatPercent(value)}
            labelFormatter={(label) => `${label} decile`}
            contentStyle={{ background: 'white', border: '1px solid #e5e7eb', borderRadius: '6px' }}
          />
          <ReferenceLine y={0} stroke="#333" strokeWidth={1} />
          <Bar
            dataKey="percentChange"
            fill="#319795"
            name="% change in net income"
            animationDuration={800}
            animationBegin={0}
          >
            <LabelList
              dataKey="percentChange"
              position="inside"
              formatter={(value) => Math.abs(value) >= 0.1 ? `${value.toFixed(1)}%` : ''}
              style={{ fontSize: 11, fill: 'white', fontWeight: 500 }}
            />
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

export default DistributionalChart
