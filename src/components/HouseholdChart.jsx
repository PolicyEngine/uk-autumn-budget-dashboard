import { ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, ResponsiveContainer, ReferenceLine } from 'recharts'
import './HouseholdChart.css'

function HouseholdChart({ data }) {
  if (!data || data.length === 0) return null

  return (
    <div className="household-chart">
      <h2>Household income impact</h2>
      <p className="chart-description">
        Distribution of household income changes across different income levels. Each dot represents a household.
      </p>

      <ResponsiveContainer width="100%" height={300}>
        <ScatterChart margin={{ top: 15, right: 60, left: 70, bottom: 40 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" vertical={true} horizontal={true} />

          <XAxis
            type="number"
            dataKey="x"
            domain={[-5000, 5000]}
            ticks={[-5000, -4000, -3000, -2000, -1000, 0, 1000, 2000, 3000, 4000, 5000]}
            tickFormatter={(value) => `£${Math.abs(value / 1000)}k`}
            tick={{ fontSize: 10, fill: '#666' }}
            axisLine={{ stroke: '#333', strokeWidth: 1 }}
            label={{
              value: 'Tax change (£)',
              position: 'insideBottom',
              offset: -10,
              style: { fill: '#374151', fontSize: 11, fontWeight: 500 }
            }}
          />

          <YAxis
            type="number"
            dataKey="y"
            scale="log"
            domain={[10000, 500000]}
            ticks={[10000, 25000, 50000, 75000, 100000, 150000, 200000, 300000, 500000]}
            tickFormatter={(value) => {
              if (value >= 100000) return `£${value / 1000}k`
              return `£${(value / 1000).toFixed(0)}k`
            }}
            orientation="left"
            tick={{ fontSize: 10, fill: '#666' }}
            width={70}
            label={{
              value: 'Household income',
              angle: -90,
              position: 'insideLeft',
              dx: -30,
              style: { textAnchor: 'middle', fill: '#374151', fontSize: 11, fontWeight: 500 }
            }}
          />

          <ReferenceLine x={0} stroke="#333" strokeWidth={2} />

          <Scatter
            name="Tax increases"
            data={data.filter(d => d.x < 0)}
            fill="rgba(184, 135, 90, 0.5)"
          />
          <Scatter
            name="Tax cuts"
            data={data.filter(d => d.x >= 0)}
            fill="rgba(49, 151, 149, 0.5)"
          />
        </ScatterChart>
      </ResponsiveContainer>
    </div>
  )
}

export default HouseholdChart
