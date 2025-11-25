import { useMemo, useState, useRef, useCallback } from 'react'
import { ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine, Cell } from 'recharts'
import YearSlider from './YearSlider'
import './HouseholdChart.css'

function HouseholdChart({ rawData, selectedPolicies }) {
  const [internalYear, setInternalYear] = useState(2026)

  // Filter data by internal year and selected policies
  const data = useMemo(() => {
    if (!rawData) return []
    return rawData
      .filter(row => selectedPolicies.includes(row.reform_id) && parseInt(row.year) === internalYear)
      .map(row => ({
        baseline_income: parseFloat(row.baseline_income),
        income_change: parseFloat(row.income_change),
        household_weight: parseFloat(row.household_weight)
      }))
  }, [rawData, selectedPolicies, internalYear])
  // Zoom state
  const [zoomDomain, setZoomDomain] = useState(null)
  const [selectionBox, setSelectionBox] = useState(null)
  const [isDragging, setIsDragging] = useState(false)
  const chartRef = useRef(null)
  const startPoint = useRef(null)

  // Process data for Recharts
  const { chartData, stats, dataExtent } = useMemo(() => {
    if (!data || data.length === 0) return { chartData: [], stats: null, dataExtent: null }

    // Randomly sample 1000 points from the data to avoid performance issues
    const sampleSize = Math.min(1000, data.length)
    const sampledData = data
      .map(d => ({ ...d, sort: Math.random() }))
      .sort((a, b) => a.sort - b.sort)
      .slice(0, sampleSize)

    // Calculate statistics
    const gains = sampledData.filter(d => d.income_change > 0.01)
    const losses = sampledData.filter(d => d.income_change < -0.01)
    const noChange = sampledData.filter(d => Math.abs(d.income_change) <= 0.01)

    // Scale household weights for marker sizes (4-15 range for better visibility)
    const maxWeight = data.reduce((max, d) => Math.max(max, d.household_weight), 0)
    const scaleSize = (weight) => Math.max(4, Math.min(15, (weight / maxWeight) * 15))

    // Scale household weights for opacity (0.5-0.95 range for better visibility)
    const scaleOpacity = (weight) => Math.max(0.5, Math.min(0.95, 0.5 + (weight / maxWeight) * 0.45))

    // Calculate data extent for zoom
    const xValues = sampledData.map(d => d.income_change)
    const yValues = sampledData.map(d => d.baseline_income)
    const extent = {
      xMin: xValues.reduce((min, val) => Math.min(min, val), Infinity),
      xMax: xValues.reduce((max, val) => Math.max(max, val), -Infinity),
      yMin: yValues.reduce((min, val) => Math.min(min, val), Infinity),
      yMax: yValues.reduce((max, val) => Math.max(max, val), -Infinity)
    }

    // Prepare data with category, size, and opacity
    const processedData = sampledData.map(d => ({
      x: d.income_change,
      y: d.baseline_income,
      size: scaleSize(d.household_weight),
      opacity: scaleOpacity(d.household_weight),
      category: d.income_change > 0.01 ? 'gains' :
                d.income_change < -0.01 ? 'losses' : 'noChange',
      weight: d.household_weight
    }))

    return {
      chartData: processedData,
      stats: {
        gains: gains.length,
        losses: losses.length,
        noChange: noChange.length,
        total: sampledData.length
      },
      dataExtent: extent
    }
  }, [data])

  // Calculate domains (either zoomed or full)
  const { xDomain, yDomain } = useMemo(() => {
    if (!dataExtent) return { xDomain: [0, 0], yDomain: [0, 0] }

    if (zoomDomain) {
      return zoomDomain
    }

    // Fixed x-axis domain from -5k to 10k, y-axis from 0 to 160k
    return {
      xDomain: [-5000, 10000],
      yDomain: [0, 160000]
    }
  }, [dataExtent, zoomDomain])

  // Convert pixel coordinates to data coordinates
  const pixelToData = useCallback((pixelX, pixelY, chartArea) => {
    if (!chartArea) return null

    const { x: chartX, y: chartY, width, height } = chartArea

    // Calculate relative position within chart
    const relX = (pixelX - chartX) / width
    const relY = (pixelY - chartY) / height

    // Convert to data coordinates
    const dataX = xDomain[0] + relX * (xDomain[1] - xDomain[0])
    const dataY = yDomain[1] - relY * (yDomain[1] - yDomain[0]) // Y is inverted

    return { x: dataX, y: dataY }
  }, [xDomain, yDomain])

  // Mouse event handlers for drag zoom
  const handleMouseDown = useCallback((e) => {
    if (!chartRef.current) return

    const chartArea = chartRef.current.getBoundingClientRect()
    const x = e.clientX - chartArea.left
    const y = e.clientY - chartArea.top

    // Check if click is within the chart area (approximate margins)
    const margin = { left: 80, right: 30, top: 20, bottom: 60 }
    if (x < margin.left || x > chartArea.width - margin.right ||
        y < margin.top || y > chartArea.height - margin.bottom) {
      return
    }

    startPoint.current = { x: e.clientX, y: e.clientY }
    setIsDragging(true)
    setSelectionBox(null)
  }, [])

  const handleMouseMove = useCallback((e) => {
    if (!isDragging || !startPoint.current || !chartRef.current) return

    const chartArea = chartRef.current.getBoundingClientRect()
    const currentX = e.clientX - chartArea.left
    const currentY = e.clientY - chartArea.top
    const startX = startPoint.current.x - chartArea.left
    const startY = startPoint.current.y - chartArea.top

    setSelectionBox({
      left: Math.min(startX, currentX),
      top: Math.min(startY, currentY),
      width: Math.abs(currentX - startX),
      height: Math.abs(currentY - startY)
    })
  }, [isDragging])

  const handleMouseUp = useCallback((e) => {
    if (!isDragging || !startPoint.current || !chartRef.current) {
      setIsDragging(false)
      setSelectionBox(null)
      return
    }

    const chartArea = chartRef.current.getBoundingClientRect()

    // Get chart content area (excluding margins)
    const margin = { left: 80, right: 30, top: 20, bottom: 60 }
    const contentArea = {
      x: margin.left,
      y: margin.top,
      width: chartArea.width - margin.left - margin.right,
      height: chartArea.height - margin.top - margin.bottom
    }

    const start = pixelToData(startPoint.current.x, startPoint.current.y, {
      x: chartArea.left + contentArea.x,
      y: chartArea.top + contentArea.y,
      width: contentArea.width,
      height: contentArea.height
    })

    const end = pixelToData(e.clientX, e.clientY, {
      x: chartArea.left + contentArea.x,
      y: chartArea.top + contentArea.y,
      width: contentArea.width,
      height: contentArea.height
    })

    if (start && end) {
      const minDragDistance = 10
      const dragDistance = Math.sqrt(
        Math.pow(e.clientX - startPoint.current.x, 2) +
        Math.pow(e.clientY - startPoint.current.y, 2)
      )

      if (dragDistance > minDragDistance) {
        setZoomDomain({
          xDomain: [Math.min(start.x, end.x), Math.max(start.x, end.x)],
          yDomain: [Math.min(start.y, end.y), Math.max(start.y, end.y)]
        })
      }
    }

    setIsDragging(false)
    setSelectionBox(null)
    startPoint.current = null
  }, [isDragging, pixelToData])

  // Zoom control functions
  const handleZoomIn = () => {
    if (!xDomain || !yDomain) return

    const xCenter = (xDomain[0] + xDomain[1]) / 2
    const yCenter = (yDomain[0] + yDomain[1]) / 2
    const xRange = (xDomain[1] - xDomain[0]) / 1.5
    const yRange = (yDomain[1] - yDomain[0]) / 1.5

    setZoomDomain({
      xDomain: [xCenter - xRange / 2, xCenter + xRange / 2],
      yDomain: [yCenter - yRange / 2, yCenter + yRange / 2]
    })
  }

  const handleZoomOut = () => {
    if (!xDomain || !yDomain || !dataExtent) return

    const xCenter = (xDomain[0] + xDomain[1]) / 2
    const yCenter = (yDomain[0] + yDomain[1]) / 2
    const xRange = (xDomain[1] - xDomain[0]) * 1.5
    const yRange = (yDomain[1] - yDomain[0]) * 1.5

    const newXDomain = [xCenter - xRange / 2, xCenter + xRange / 2]
    const newYDomain = [yCenter - yRange / 2, yCenter + yRange / 2]

    // Don't zoom out beyond the initial view (fixed axes)
    const maxXDomain = [-5000, 10000]
    const maxYDomain = [0, 160000]

    if (newXDomain[0] <= maxXDomain[0] && newXDomain[1] >= maxXDomain[1] &&
        newYDomain[0] <= maxYDomain[0] && newYDomain[1] >= maxYDomain[1]) {
      setZoomDomain(null) // Reset to full view
    } else {
      setZoomDomain({
        xDomain: newXDomain,
        yDomain: newYDomain
      })
    }
  }

  const handleResetZoom = () => {
    setZoomDomain(null)
  }

  // Custom tooltip
  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload
      return (
        <div style={{
          backgroundColor: 'white',
          padding: '10px',
          border: '1px solid #ccc',
          borderRadius: '4px',
          fontSize: '12px'
        }}>
          <p style={{ margin: '2px 0', color: '#374151' }}>
            <strong>Income change:</strong> £{data.x.toLocaleString('en-GB')}
          </p>
          <p style={{ margin: '2px 0', color: '#374151' }}>
            <strong>Baseline income:</strong> £{data.y.toLocaleString('en-GB')}
          </p>
        </div>
      )
    }
    return null
  }

  // Color mapping
  const getColor = (category) => {
    switch (category) {
      case 'gains': return '#319795'
      case 'losses': return '#E53E3E'
      case 'noChange': return '#9CA3AF'
      default: return '#9CA3AF'
    }
  }

  if (!data || data.length === 0) {
    return (
      <div className="household-chart">
        <h2>Household income impacts</h2>
        <p className="chart-description">
          This chart plots net income change for each household against their baseline income. Points above zero represent gains; points below represent losses.
        </p>
        <div style={{ padding: '60px 20px', textAlign: 'center', color: '#666', backgroundColor: '#f9f9f9', borderRadius: '8px' }}>
          <p style={{ margin: 0, fontSize: '0.95rem' }}>No data available yet for this metric</p>
        </div>
      </div>
    )
  }

  return (
    <div className="household-chart">
      <h2>Household income impacts</h2>
      <p className="chart-description">
        This chart plots net income change against baseline income for 1,000 sampled households.
        Green dots indicate gains, red shows losses, and grey shows minimal change.
        Dot size represents household weight in the population.
      </p>

      <div
        style={{ position: 'relative', cursor: isDragging ? 'crosshair' : 'default' }}
        ref={chartRef}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
      >
        {/* Zoom controls */}
        <div className="household-zoom-controls">
          <button
            className="zoom-control-btn"
            onClick={handleZoomIn}
            title="Zoom in"
            aria-label="Zoom in"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
              <circle cx="10" cy="10" r="7" stroke="currentColor" strokeWidth="2"/>
              <path d="M10 7V13M7 10H13" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
              <path d="M15 15L20 20" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
            </svg>
          </button>
          <button
            className="zoom-control-btn"
            onClick={handleZoomOut}
            title="Zoom out"
            aria-label="Zoom out"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
              <circle cx="10" cy="10" r="7" stroke="currentColor" strokeWidth="2"/>
              <path d="M7 10H13" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
              <path d="M15 15L20 20" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
            </svg>
          </button>
          <button
            className="zoom-control-btn"
            onClick={handleResetZoom}
            title="Reset zoom"
            aria-label="Reset zoom"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
              <path d="M21 12C21 16.9706 16.9706 21 12 21C7.02944 21 3 16.9706 3 12C3 7.02944 7.02944 3 12 3C14.8273 3 17.35 4.30367 19 6.34267" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
              <path d="M21 3V8H16" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </button>
        </div>

        {/* Selection box overlay */}
        {selectionBox && (
          <div
            className="selection-box"
            style={{
              position: 'absolute',
              left: `${selectionBox.left}px`,
              top: `${selectionBox.top}px`,
              width: `${selectionBox.width}px`,
              height: `${selectionBox.height}px`,
              border: '2px dashed #319795',
              backgroundColor: 'rgba(49, 151, 149, 0.1)',
              pointerEvents: 'none',
              zIndex: 5
            }}
          />
        )}

        <ResponsiveContainer width="100%" height={500}>
          <ScatterChart margin={{ top: 20, right: 30, left: 80, bottom: 60 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />

            <XAxis
              type="number"
              dataKey="x"
              name="Income change"
              domain={xDomain}
              tickFormatter={(value) => `£${(value / 1000).toFixed(0)}k`}
              tick={{ fontSize: 11, fill: '#666' }}
              label={{
                value: 'Net income change (£)',
                position: 'bottom',
                offset: 40,
                style: { fontSize: 12, fill: '#374151' }
              }}
            />

            <YAxis
              type="number"
              dataKey="y"
              name="Baseline income"
              domain={yDomain}
              tickFormatter={(value) => `£${(value / 1000).toFixed(0)}k`}
              tick={{ fontSize: 11, fill: '#666' }}
              label={{
                value: 'Baseline household net income (£)',
                angle: -90,
                position: 'insideLeft',
                dx: -35,
                style: { textAnchor: 'middle', fontSize: 12, fill: '#374151' }
              }}
            />

            <Tooltip content={<CustomTooltip />} cursor={{ strokeDasharray: '3 3' }} />

            {/* Zero line */}
            <ReferenceLine x={0} stroke="#666" strokeWidth={2} />

            {/* Single scatter with colored cells based on category */}
            <Scatter
              data={chartData}
              fill="#319795"
            >
              {chartData.map((entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={getColor(entry.category)}
                  fillOpacity={entry.opacity}
                  strokeWidth={0.5}
                  stroke={entry.category === 'gains' ? '#2C7A7B' :
                          entry.category === 'losses' ? '#C53030' : '#6B7280'}
                />
              ))}
            </Scatter>
          </ScatterChart>
        </ResponsiveContainer>
      </div>

      <div style={{
        display: 'flex',
        justifyContent: 'center',
        gap: '20px',
        marginTop: '20px',
        marginBottom: '16px',
        fontSize: '0.9rem'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div style={{ width: '12px', height: '12px', backgroundColor: '#319795', borderRadius: '50%' }}></div>
          <span style={{ color: '#374151' }}>Gains</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div style={{ width: '12px', height: '12px', backgroundColor: '#E53E3E', borderRadius: '50%' }}></div>
          <span style={{ color: '#374151' }}>Losses</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div style={{ width: '12px', height: '12px', backgroundColor: '#9CA3AF', borderRadius: '50%' }}></div>
          <span style={{ color: '#374151' }}>No change</span>
        </div>
      </div>

      <YearSlider selectedYear={internalYear} onYearChange={setInternalYear} />
    </div>
  )
}

export default HouseholdChart
