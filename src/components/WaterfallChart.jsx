import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, LabelList } from 'recharts'
import './WaterfallChart.css'

function WaterfallChart({ data }) {
  if (!data || data.length === 0) {
    return (
      <div className="waterfall-chart">
        <h2>Impact by income decile — absolute</h2>
        <p className="chart-description">
          Average absolute change in net income for each income decile, from the poorest 10% (1st) to the richest 10% (10th) of households.
        </p>
        <div style={{ padding: '60px 20px', textAlign: 'center', color: '#666', backgroundColor: '#f9f9f9', borderRadius: '8px' }}>
          <p style={{ margin: 0, fontSize: '0.95rem' }}>No data available yet for this metric</p>
        </div>
      </div>
    )
  }

  // Transform data for the chart - expect data with decile and avg_change
  const chartData = data
    .filter(d => d.decile && d.decile !== 'all')
    .sort((a, b) => parseInt(a.decile) - parseInt(b.decile))
    .map(d => ({
      decile: `${d.decile}`,
      value: d.avg_change || 0,
      displayDecile: `${d.decile}`
    }))

  const getColor = (value) => {
    return value >= 0 ? '#319795' : '#dc2626'
  }

  return (
    <div className="waterfall-chart">
      <h2>Impact by income decile — absolute</h2>
      <p className="chart-description">
        Average absolute change in net income for each income decile, from the poorest 10% (1st) to the richest 10% (10th) of households.
      </p>

      <ResponsiveContainer width="100%" height={420}>
        <BarChart
          data={chartData}
          margin={{ top: 20, right: 30, left: 30, bottom: 20 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
          <XAxis
            dataKey="displayDecile"
            tick={{ fontSize: 11, fill: '#666' }}
            label={{
              value: 'Income decile',
              position: 'insideBottom',
              offset: -10,
              style: { fill: '#374151', fontSize: 12, fontWeight: 500 }
            }}
          />
          <YAxis
            tickFormatter={(value) => `£${value.toFixed(0)}`}
            tick={{ fontSize: 11, fill: '#666' }}
            label={{
              value: 'Average change per household (£)',
              angle: -90,
              position: 'insideLeft',
              dx: -30,
              style: { textAnchor: 'middle', fill: '#374151', fontSize: 12, fontWeight: 500 }
            }}
          />
          <Tooltip
            formatter={(value) => [`£${value.toFixed(2)}`, 'Average change']}
            labelFormatter={(label) => `Decile: ${label}`}
            contentStyle={{ background: 'white', border: '1px solid #e5e7eb', borderRadius: '6px', fontSize: '12px' }}
          />
          <Bar dataKey="value" animationDuration={800}>
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={getColor(entry.value)} />
            ))}
            <LabelList
              dataKey="value"
              position="inside"
              formatter={(value) => Math.abs(value) >= 10 ? `${Math.round(value)}` : ''}
              style={{ fontSize: 11, fill: 'white', fontWeight: 500 }}
            />
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

export default WaterfallChart
