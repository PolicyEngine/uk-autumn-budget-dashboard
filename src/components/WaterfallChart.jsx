import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, LabelList } from 'recharts'
import './WaterfallChart.css'

function WaterfallChart({ data }) {
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

  if (!data || data.length === 0) {
    return (
      <div className="waterfall-chart">
        <h2>Winners and losers</h2>
        <p className="chart-description">
          Proportion of the population experiencing income gains or losses, broken down by magnitude of change from the policy reforms.
        </p>
        <div style={{ padding: '60px 20px', textAlign: 'center', color: '#666', backgroundColor: '#f9f9f9', borderRadius: '8px' }}>
          <p style={{ margin: 0, fontSize: '0.95rem' }}>No data available yet for this metric</p>
        </div>
      </div>
    )
  }

  // Separate "All" from decile data
  const allData = data.filter(d => d.category === 'All')
  const decileData = data.filter(d => d.category !== 'All')

  return (
    <div className="waterfall-chart">
      <h2>Winners and losers</h2>
      <p className="chart-description">
        Proportion of the population experiencing income gains or losses, broken down by magnitude of change from the policy reforms.
      </p>

      {/* All chart */}
      {allData.length > 0 && (
        <div className="waterfall-all-chart" style={{ marginBottom: '16px' }}>
          <ResponsiveContainer width="100%" height={60}>
            <BarChart
              data={allData}
              layout="vertical"
              margin={{ top: 10, right: 20, left: 30, bottom: 10 }}
              stackOffset="expand"
            >
              <XAxis
                type="number"
                domain={[0, 1]}
                tickFormatter={(value) => `${(value * 100).toFixed(0)}%`}
                tick={{ fontSize: 11, fill: '#666' }}
                hide
              />
              <YAxis
                type="category"
                dataKey="category"
                tick={{ fontSize: 11, fill: '#666' }}
                width={30}
              />
              <Tooltip
                formatter={(value) => `${(value * 100).toFixed(1)}%`}
                contentStyle={{ background: 'white', border: '1px solid #e5e7eb', borderRadius: '6px', fontSize: '12px' }}
              />
              <Bar dataKey="Gain more than 5%" stackId="a" fill="#2d5f7f" animationDuration={800}>
                <LabelList
                  dataKey="Gain more than 5%"
                  position="center"
                  formatter={(value) => {
                    const pct = value * 100
                    return pct >= 3 ? `${Math.round(pct)}%` : ''
                  }}
                  style={{ fontSize: 11, fill: 'white', fontWeight: 500 }}
                />
              </Bar>
              <Bar dataKey="Gain less than 5%" stackId="a" fill="#5A8FB8" animationDuration={800}>
                <LabelList
                  dataKey="Gain less than 5%"
                  position="center"
                  formatter={(value) => {
                    const pct = value * 100
                    return pct >= 3 ? `${Math.round(pct)}%` : ''
                  }}
                  style={{ fontSize: 11, fill: 'white', fontWeight: 500 }}
                />
              </Bar>
              <Bar dataKey="No change" stackId="a" fill="#e5e7eb" animationDuration={800}>
                <LabelList
                  dataKey="No change"
                  position="insideRight"
                  formatter={(value) => `${Math.round(value * 100)}%`}
                  style={{ fontSize: 11, fill: '#374151', fontWeight: 500 }}
                />
              </Bar>
              <Bar dataKey="Lose less than 5%" stackId="a" fill="#9ca3af" animationDuration={800} />
              <Bar dataKey="Lose more than 5%" stackId="a" fill="#4b5563" animationDuration={800} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Decile chart */}
      <ResponsiveContainer width="100%" height={360}>
        <BarChart
          data={decileData}
          layout="vertical"
          margin={{ top: 10, right: 20, left: 30, bottom: 30 }}
          stackOffset="expand"
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" vertical={false} />
          <XAxis
            type="number"
            domain={[0, 1]}
            tickFormatter={(value) => `${(value * 100).toFixed(0)}%`}
            tick={{ fontSize: 11, fill: '#666' }}
            label={{
              value: 'Population share',
              position: 'insideBottom',
              offset: -15,
              style: { fill: '#374151', fontSize: 12, fontWeight: 500 }
            }}
          />
          <YAxis
            type="category"
            dataKey="category"
            tick={{ fontSize: 11, fill: '#666' }}
            width={30}
            label={{
              value: 'Income decile',
              angle: -90,
              position: 'insideLeft',
              style: { textAnchor: 'middle', fill: '#374151', fontSize: 12, fontWeight: 500 }
            }}
          />
          <Tooltip
            formatter={(value) => `${(value * 100).toFixed(1)}%`}
            contentStyle={{ background: 'white', border: '1px solid #e5e7eb', borderRadius: '6px', fontSize: '12px' }}
          />
          <Bar dataKey="Gain more than 5%" stackId="a" fill="#2d5f7f" animationDuration={800}>
            <LabelList
              dataKey="Gain more than 5%"
              position="center"
              formatter={(value) => {
                const pct = value * 100
                return pct >= 3 ? `${Math.round(pct)}%` : ''
              }}
              style={{ fontSize: 11, fill: 'white', fontWeight: 500 }}
            />
          </Bar>
          <Bar dataKey="Gain less than 5%" stackId="a" fill="#5A8FB8" animationDuration={800}>
            <LabelList
              dataKey="Gain less than 5%"
              position="center"
              formatter={(value) => {
                const pct = value * 100
                return pct >= 3 ? `${Math.round(pct)}%` : ''
              }}
              style={{ fontSize: 11, fill: 'white', fontWeight: 500 }}
            />
          </Bar>
          <Bar dataKey="No change" stackId="a" fill="#e5e7eb" animationDuration={800}>
            <LabelList
              dataKey="No change"
              position="insideRight"
              formatter={(value) => `${Math.round(value * 100)}%`}
              style={{ fontSize: 11, fill: '#374151', fontWeight: 500 }}
            />
          </Bar>
          <Bar dataKey="Lose less than 5%" stackId="a" fill="#9ca3af" animationDuration={800}>
            <LabelList
              dataKey="Lose less than 5%"
              position="center"
              formatter={(value) => {
                const pct = value * 100
                return pct >= 3 ? `${Math.round(pct)}%` : ''
              }}
              style={{ fontSize: 11, fill: 'white', fontWeight: 500 }}
            />
          </Bar>
          <Bar dataKey="Lose more than 5%" stackId="a" fill="#4b5563" animationDuration={800}>
            <LabelList
              dataKey="Lose more than 5%"
              position="center"
              formatter={(value) => {
                const pct = value * 100
                return pct >= 3 ? `${Math.round(pct)}%` : ''
              }}
              style={{ fontSize: 11, fill: 'white', fontWeight: 500 }}
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
