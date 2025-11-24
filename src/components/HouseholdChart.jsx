import { useMemo } from 'react'
import Plot from 'react-plotly.js'
import './HouseholdChart.css'

function HouseholdChart({ data }) {
  // Process data for Plotly
  const plotData = useMemo(() => {
    if (!data || data.length === 0) return null

    // Separate data into gains, losses, and no change
    const gains = data.filter(d => d.income_change > 0.01)
    const losses = data.filter(d => d.income_change < -0.01)
    const noChange = data.filter(d => Math.abs(d.income_change) <= 0.01)

    // Scale household weights for marker sizes (1-20 range)
    const maxWeight = Math.max(...data.map(d => d.household_weight))
    const scaleSize = (weight) => Math.max(1, Math.min(20, (weight / maxWeight) * 20))

    const traces = []

    // No change trace (grey)
    if (noChange.length > 0) {
      traces.push({
        x: noChange.map(d => d.income_change),
        y: noChange.map(d => d.baseline_income),
        mode: 'markers',
        type: 'scatter',
        name: `No change (${noChange.length.toLocaleString()})`,
        marker: {
          size: noChange.map(d => scaleSize(d.household_weight)),
          color: '#9CA3AF',
          opacity: 0.7,
          line: { width: 0.5, color: '#6B7280' }
        },
        hovertemplate: 'Income change: £%{x:,.0f}<br>Baseline income: £%{y:,.0f}<extra></extra>'
      })
    }

    // Gains trace (teal)
    if (gains.length > 0) {
      traces.push({
        x: gains.map(d => d.income_change),
        y: gains.map(d => d.baseline_income),
        mode: 'markers',
        type: 'scatter',
        name: `Gains (${gains.length.toLocaleString()})`,
        marker: {
          size: gains.map(d => scaleSize(d.household_weight)),
          color: '#319795',
          opacity: 0.75,
          line: { width: 0.5, color: '#2C7A7B' }
        },
        hovertemplate: 'Income change: £%{x:,.0f}<br>Baseline income: £%{y:,.0f}<extra></extra>'
      })
    }

    // Losses trace (red)
    if (losses.length > 0) {
      traces.push({
        x: losses.map(d => d.income_change),
        y: losses.map(d => d.baseline_income),
        mode: 'markers',
        type: 'scatter',
        name: `Losses (${losses.length.toLocaleString()})`,
        marker: {
          size: losses.map(d => scaleSize(d.household_weight)),
          color: '#E53E3E',
          opacity: 0.75,
          line: { width: 0.5, color: '#C53030' }
        },
        hovertemplate: 'Income change: £%{x:,.0f}<br>Baseline income: £%{y:,.0f}<extra></extra>'
      })
    }

    return traces
  }, [data])

  if (!data || data.length === 0) {
    return (
      <div className="household-chart">
        <h2>Income changes by household</h2>
        <p className="chart-description">
          Net income change for each household plotted against their baseline income. Points above zero represent gains; points below represent losses.
        </p>
        <div style={{ padding: '60px 20px', textAlign: 'center', color: '#666', backgroundColor: '#f9f9f9', borderRadius: '8px' }}>
          <p style={{ margin: 0, fontSize: '0.95rem' }}>No data available yet for this metric</p>
        </div>
      </div>
    )
  }

  return (
    <div className="household-chart">
      <h2>Income changes by household</h2>
      <p className="chart-description">
        Net income change for each household plotted against their baseline income. Points above zero represent gains; points below represent losses. Dot size represents household weight. Use mouse wheel to zoom in/out.
      </p>

      <div style={{ width: '100%', height: '500px' }}>
        <Plot
          data={plotData}
          layout={{
            autosize: true,
            margin: { l: 80, r: 40, t: 20, b: 60 },
            xaxis: {
              title: {
                text: 'Net income change (£)',
                font: { size: 12, color: '#374151', family: 'Inter, sans-serif' }
              },
              gridcolor: '#e0e0e0',
              zeroline: true,
              zerolinecolor: '#666',
              zerolinewidth: 2,
              tickfont: { size: 10, color: '#666' }
            },
            yaxis: {
              title: {
                text: 'Baseline household net income (£)',
                font: { size: 12, color: '#374151', family: 'Inter, sans-serif' }
              },
              gridcolor: '#e0e0e0',
              tickfont: { size: 10, color: '#666' }
            },
            hovermode: 'closest',
            showlegend: false,
            plot_bgcolor: '#ffffff',
            paper_bgcolor: '#ffffff'
          }}
          config={{
            displayModeBar: true,
            displaylogo: false,
            modeBarButtonsToRemove: ['select2d', 'lasso2d'],
            responsive: true
          }}
          style={{ width: '100%', height: '100%' }}
          useResizeHandler={true}
        />
      </div>
    </div>
  )
}

export default HouseholdChart
