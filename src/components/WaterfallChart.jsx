import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, LabelList } from 'recharts'
import './WaterfallChart.css'

function WaterfallChart({ data }) {
  if (!data || data.length === 0) return null

  // Colors based on change type
  const getColor = (category) => {
    if (category === 'All') return '#5A8FB8'
    if (category.includes('Gain more')) return '#2d5f7f'
    if (category.includes('Gain less')) return '#5A8FB8'
    if (category.includes('No change')) return '#e5e7eb'
    if (category.includes('Loss less')) return '#9ca3af'
    if (category.includes('Loss more')) return '#4b5563'
    return '#9ca3af'
  }

  return (
    <div className="waterfall-chart">
      <h2>Change in income</h2>
      <p className="chart-description">
        Distribution of income changes across the population, showing the share of people experiencing different levels of impact.
      </p>

      <ResponsiveContainer width="100%" height={300}>
        <BarChart
          data={data}
          layout="horizontal"
          margin={{ top: 10, right: 100, left: 100, bottom: 10 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" horizontal={false} />
          <XAxis
            type="number"
            domain={[0, 100]}
            ticks={[0, 20, 40, 60, 80, 100]}
            tickFormatter={(value) => `${value}%`}
            tick={{ fontSize: 11, fill: '#666' }}
            label={{
              value: 'Population share',
              position: 'insideBottom',
              offset: -5,
              style: { fill: '#374151', fontSize: 12, fontWeight: 500 }
            }}
          />
          <YAxis
            type="category"
            dataKey="category"
            tick={{ fontSize: 11, fill: '#666' }}
            width={110}
            label={{
              value: 'Income decile',
              angle: -90,
              position: 'insideLeft',
              dx: -50,
              style: { textAnchor: 'middle', fill: '#374151', fontSize: 12, fontWeight: 500 }
            }}
          />
          <Tooltip
            formatter={(value) => `${value}%`}
            contentStyle={{ background: 'white', border: '1px solid #e5e7eb', borderRadius: '6px', fontSize: '12px' }}
          />
          <Bar dataKey="value" animationDuration={800}>
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={getColor(entry.category)} />
            ))}
            <LabelList
              dataKey="percentLabel"
              position="right"
              style={{ fontSize: 11, fill: '#374151', fontWeight: 500 }}
              offset={8}
            />
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      <div className="waterfall-legend">
        <div className="legend-item">
          <span className="legend-color" style={{ background: '#2d5f7f' }}></span>
          <span>Gain more than 5%</span>
        </div>
        <div className="legend-item">
          <span className="legend-color" style={{ background: '#5A8FB8' }}></span>
          <span>Gain less than 5%</span>
        </div>
        <div className="legend-item">
          <span className="legend-color" style={{ background: '#e5e7eb' }}></span>
          <span>No change</span>
        </div>
        <div className="legend-item">
          <span className="legend-color" style={{ background: '#9ca3af' }}></span>
          <span>Loss less than 5%</span>
        </div>
        <div className="legend-item">
          <span className="legend-color" style={{ background: '#4b5563' }}></span>
          <span>Loss more than 5%</span>
        </div>
      </div>
    </div>
  )
}

export default WaterfallChart
