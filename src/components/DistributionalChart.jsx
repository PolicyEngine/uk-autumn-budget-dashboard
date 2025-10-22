import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts'
import './DistributionalChart.css'

function DistributionalChart({ data }) {
  if (!data || data.length === 0) return null

  const formatPercent = (value) => `${value.toFixed(2)}%`

  return (
    <div className="distributional-chart">
      <h2>Impact by income decile</h2>
      <p className="chart-description">
        Average percentage change in net income for each income decile, from the poorest 10% (1st) to the richest 10% (10th) of households.
      </p>

      <ResponsiveContainer width="100%" height={300}>
        <BarChart
          data={data}
          margin={{ top: 15, right: 20, left: 70, bottom: 15 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
          <XAxis
            dataKey="decile"
            tick={{ fontSize: 12, fill: '#666' }}
            label={{
              value: 'Income decile (1st = poorest, 10th = richest)',
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
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

export default DistributionalChart
