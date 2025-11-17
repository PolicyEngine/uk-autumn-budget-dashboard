import { useEffect, useRef, useState } from 'react'
import * as d3 from 'd3'
import './ConstituencyMap.css'

const SCENARIOS = {
  'raise_basic_rate_1p': 'Raise basic rate by 1p',
  'raise_higher_rate_1p': 'Raise higher rate by 1p',
  'remove_2_child_limit': 'Remove 2-child limit',
}

export default function ConstituencyMap() {
  const svgRef = useRef(null)
  const tooltipRef = useRef(null)
  const [selectedScenario, setSelectedScenario] = useState('raise_basic_rate_1p')
  const [selectedConstituency, setSelectedConstituency] = useState(null)
  const [tooltipData, setTooltipData] = useState(null)
  const [tooltipPosition, setTooltipPosition] = useState({ x: 0, y: 0 })
  const [data, setData] = useState([])
  const [geoData, setGeoData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState([])

  // Load data
  useEffect(() => {
    Promise.all([
      fetch('/data/scenario_gains_by_constituency.csv').then(r => r.text()),
      fetch('/data/uk_constituencies_2024.geojson').then(r => r.json())
    ]).then(([csvText, geojson]) => {
      // Parse CSV with proper handling of quoted fields
      const parseCSVLine = (line) => {
        const result = []
        let current = ''
        let inQuotes = false

        for (let i = 0; i < line.length; i++) {
          const char = line[i]
          if (char === '"') {
            inQuotes = !inQuotes
          } else if (char === ',' && !inQuotes) {
            result.push(current.trim())
            current = ''
          } else {
            current += char
          }
        }
        result.push(current.trim())
        return result
      }

      const lines = csvText.split('\n')
      const parsedData = lines.slice(1)
        .filter(line => line.trim())
        .map(line => {
          const values = parseCSVLine(line)
          return {
            scenario: values[0]?.trim(),
            constituency_code: values[1]?.trim(),
            constituency_name: values[2]?.trim().replace(/^"|"$/g, ''),
            average_gain: parseFloat(values[3]),
          }
        })

      setData(parsedData)
      setGeoData(geojson)
      setLoading(false)
    }).catch(error => {
      console.error('Error loading data:', error)
      setLoading(false)
    })
  }, [])

  // Render map
  useEffect(() => {
    if (!svgRef.current || !geoData || !data.length) return

    const svg = d3.select(svgRef.current)
    svg.selectAll('*').remove()

    const width = 800
    const height = 500

    const g = svg.append('g')

    // Get bounds of the British National Grid coordinates
    const bounds = {
      xMin: Infinity,
      xMax: -Infinity,
      yMin: Infinity,
      yMax: -Infinity
    }

    geoData.features.forEach((feature) => {
      const coords = feature.geometry?.coordinates
      if (!coords) return

      const traverse = (c) => {
        if (typeof c[0] === 'number') {
          bounds.xMin = Math.min(bounds.xMin, c[0])
          bounds.xMax = Math.max(bounds.xMax, c[0])
          bounds.yMin = Math.min(bounds.yMin, c[1])
          bounds.yMax = Math.max(bounds.yMax, c[1])
        } else {
          c.forEach(traverse)
        }
      }
      traverse(coords)
    })

    // Create scale to fit British National Grid coordinates into SVG
    const padding = 20
    const dataWidth = bounds.xMax - bounds.xMin
    const dataHeight = bounds.yMax - bounds.yMin
    const scale = Math.min((width - 2 * padding) / dataWidth, (height - 2 * padding) / dataHeight)

    // Calculate centering offsets
    const scaledWidth = dataWidth * scale
    const scaledHeight = dataHeight * scale
    const offsetX = (width - scaledWidth) / 2
    const offsetY = (height - scaledHeight) / 2

    const projection = d3.geoTransform({
      point: function(x, y) {
        // Transform British National Grid to SVG coordinates
        this.stream.point(
          (x - bounds.xMin) * scale + offsetX,
          height - ((y - bounds.yMin) * scale + offsetY)
        )
      }
    })

    const path = d3.geoPath().projection(projection)

    // Filter data for current scenario
    const scenarioData = data.filter(d => d.scenario === selectedScenario)
    const dataMap = new Map(scenarioData.map(d => [d.constituency_code, d]))

    // Color scale - diverging with white at 0, red for losses, green for gains
    const extent = d3.extent(scenarioData, d => d.average_gain)
    const maxAbsValue = Math.max(Math.abs(extent[0]), Math.abs(extent[1]))

    const colorScale = d3.scaleDiverging()
      .domain([-maxAbsValue, 0, maxAbsValue])
      .interpolator(d3.interpolateRdYlGn)

    // Draw constituencies
    g.selectAll('path')
      .data(geoData.features)
      .join('path')
      .attr('d', path)
      .attr('fill', (d) => {
        const constData = dataMap.get(d.properties.GSScode)
        return constData ? colorScale(constData.average_gain) : '#ddd'
      })
      .attr('stroke', '#fff')
      .attr('stroke-width', 0.05)
      .attr('class', 'constituency-path')
      .style('cursor', 'pointer')
      .on('click', function(event, d) {
        event.stopPropagation()

        const constData = dataMap.get(d.properties.GSScode)

        if (constData) {
          // Update styling for all paths
          svg.selectAll('.constituency-path')
            .attr('stroke', '#fff')
            .attr('stroke-width', 0.05)

          // Highlight selected constituency
          d3.select(this)
            .attr('stroke', '#1D4044')
            .attr('stroke-width', 0.6)

          setSelectedConstituency(constData)

          // Get centroid of constituency for tooltip positioning
          const bounds = path.bounds(d)
          const centerX = (bounds[0][0] + bounds[1][0]) / 2
          const centerY = (bounds[0][1] + bounds[1][1]) / 2

          // Show tooltip
          setTooltipData(constData)
          setTooltipPosition({ x: centerX, y: centerY })

          // Smooth zoom to constituency
          const dx = bounds[1][0] - bounds[0][0]
          const dy = bounds[1][1] - bounds[0][1]
          const x = (bounds[0][0] + bounds[1][0]) / 2
          const y = (bounds[0][1] + bounds[1][1]) / 2
          const scale = Math.min(4, 0.9 / Math.max(dx / width, dy / height))
          const translate = [width / 2 - scale * x, height / 2 - scale * y]

          svg.transition()
            .duration(750)
            .call(
              zoom.transform,
              d3.zoomIdentity.translate(translate[0], translate[1]).scale(scale)
            )
        }
      })
      .on('mouseover', function() {
        const currentStrokeWidth = d3.select(this).attr('stroke-width')
        if (currentStrokeWidth === '0.05') {
          d3.select(this)
            .attr('stroke', '#666')
            .attr('stroke-width', 0.3)
        }
      })
      .on('mouseout', function() {
        const currentStrokeWidth = d3.select(this).attr('stroke-width')
        if (currentStrokeWidth !== '0.6') {
          d3.select(this)
            .attr('stroke', '#fff')
            .attr('stroke-width', 0.05)
        }
      })

    // Zoom behavior
    const zoom = d3.zoom()
      .scaleExtent([1, 8])
      .on('zoom', (event) => {
        g.attr('transform', event.transform)
      })

    svg.call(zoom)

    // Store zoom behavior for controls
    window.mapZoomBehavior = { svg, zoom }
  }, [geoData, data, selectedScenario])

  // Update colors when scenario changes
  useEffect(() => {
    if (!svgRef.current || !geoData || !data.length) return

    const svg = d3.select(svgRef.current)
    const scenarioData = data.filter(d => d.scenario === selectedScenario)
    const dataMap = new Map(scenarioData.map(d => [d.constituency_code, d]))

    // Color scale
    const extent = d3.extent(scenarioData, d => d.average_gain)
    const maxAbsValue = Math.max(Math.abs(extent[0]), Math.abs(extent[1]))
    const colorScale = d3.scaleDiverging()
      .domain([-maxAbsValue, 0, maxAbsValue])
      .interpolator(d3.interpolateRdYlGn)

    // Update fill colors with transition
    svg.selectAll('.constituency-path')
      .transition()
      .duration(500)
      .attr('fill', (d) => {
        const constData = dataMap.get(d.properties.GSScode)
        return constData ? colorScale(constData.average_gain) : '#ddd'
      })
  }, [selectedScenario, data, geoData])

  // Update selected constituency data when scenario changes
  useEffect(() => {
    if (!selectedConstituency || !data.length) return

    const scenarioData = data.filter(d => d.scenario === selectedScenario)
    const dataMap = new Map(scenarioData.map(d => [d.constituency_code, d]))
    const newData = dataMap.get(selectedConstituency.constituency_code)

    if (newData) {
      setSelectedConstituency(newData)
    }
  }, [selectedScenario, data, selectedConstituency])

  // Handle search
  useEffect(() => {
    if (!searchQuery.trim() || !data.length) {
      setSearchResults([])
      return
    }

    const scenarioData = data.filter(d => d.scenario === selectedScenario)
    const query = searchQuery.toLowerCase()
    const results = scenarioData.filter(d =>
      d.constituency_name.toLowerCase().includes(query)
    ).slice(0, 5)

    setSearchResults(results)
  }, [searchQuery, data, selectedScenario])

  // Zoom control functions
  const handleZoomIn = () => {
    if (window.mapZoomBehavior) {
      const { svg, zoom } = window.mapZoomBehavior
      svg.transition().duration(300).call(zoom.scaleBy, 1.5)
    }
  }

  const handleZoomOut = () => {
    if (window.mapZoomBehavior) {
      const { svg, zoom } = window.mapZoomBehavior
      svg.transition().duration(300).call(zoom.scaleBy, 0.67)
    }
  }

  const handleResetZoom = () => {
    if (window.mapZoomBehavior) {
      const { svg, zoom } = window.mapZoomBehavior
      svg.transition().duration(750).call(zoom.transform, d3.zoomIdentity)
    }
    setTooltipData(null)
    if (svgRef.current) {
      const svg = d3.select(svgRef.current)
      svg.selectAll('.constituency-path')
        .attr('stroke', '#fff')
        .attr('stroke-width', 0.05)
    }
  }

  const selectConstituency = (constData) => {
    setSelectedConstituency(constData)
    setSearchQuery('')
    setSearchResults([])

    if (!geoData || !svgRef.current) return

    const svg = d3.select(svgRef.current)

    // Update styling for all paths
    svg.selectAll('.constituency-path')
      .attr('stroke', '#fff')
      .attr('stroke-width', 0.05)

    // Highlight selected constituency
    const selectedPath = svg.selectAll('.constituency-path')
      .filter((d) => d.properties.GSScode === constData.constituency_code)

    selectedPath
      .attr('stroke', '#1D4044')
      .attr('stroke-width', 0.6)

    // Get the bounding box of the selected path
    const pathNode = selectedPath.node()
    if (!pathNode) return

    const bbox = pathNode.getBBox()
    const centerX = bbox.x + bbox.width / 2
    const centerY = bbox.y + bbox.height / 2

    // Show tooltip
    setTooltipData(constData)
    setTooltipPosition({ x: centerX, y: centerY })

    // Smooth zoom to constituency
    const dx = bbox.width
    const dy = bbox.height
    const x = centerX
    const y = centerY
    const scale = Math.min(4, 0.9 / Math.max(dx / 800, dy / 500))
    const translate = [800 / 2 - scale * x, 500 / 2 - scale * y]

    if (window.mapZoomBehavior) {
      const { svg: svgZoom, zoom } = window.mapZoomBehavior
      svgZoom.transition()
        .duration(750)
        .call(
          zoom.transform,
          d3.zoomIdentity.translate(translate[0], translate[1]).scale(scale)
        )
    }
  }

  if (loading) {
    return <div className="constituency-loading">Loading map...</div>
  }

  return (
    <div className="constituency-map-wrapper">
      {/* Search and legend in top bar */}
      <div className="map-top-bar">
        <div className="map-search-section">
          <h3>Search constituency</h3>
          <div className="search-container">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Type to search..."
              className="constituency-search"
            />
            {searchResults.length > 0 && (
              <div className="search-results">
                {searchResults.map((result) => (
                  <button
                    key={result.constituency_code}
                    onClick={() => selectConstituency(result)}
                    className="search-result-item"
                  >
                    <div className="result-name">{result.constituency_name}</div>
                    <div className="result-value">£{result.average_gain.toFixed(2)}</div>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        <div className="map-legend-horizontal">
          <div className="legend-horizontal-content">
            <div className="legend-gradient-horizontal" />
            <div className="legend-labels-horizontal">
              <span>Loss</span>
              <span className="legend-zero">£0</span>
              <span>Gain</span>
            </div>
          </div>
        </div>
      </div>

      {/* Map full width */}
      <div className="map-content">
        <div className="map-canvas">
          <svg
            ref={svgRef}
            width="800"
            height="500"
            viewBox="0 0 800 500"
            preserveAspectRatio="xMidYMid meet"
            onClick={() => {
              setTooltipData(null)
              if (svgRef.current) {
                const svg = d3.select(svgRef.current)
                svg.selectAll('.constituency-path')
                  .attr('stroke', '#fff')
                  .attr('stroke-width', 0.05)
              }
            }}
          />

          {/* Zoom controls */}
          <div className="zoom-controls" onClick={(e) => e.stopPropagation()}>
            <button
              className="zoom-control-btn"
              onClick={handleZoomIn}
              title="Zoom in"
              aria-label="Zoom in"
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
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
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
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
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                <path d="M21 12C21 16.9706 16.9706 21 12 21C7.02944 21 3 16.9706 3 12C3 7.02944 7.02944 3 12 3C14.8273 3 17.35 4.30367 19 6.34267" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
                <path d="M21 3V8H16" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </button>
          </div>

          {/* Tooltip overlay */}
          {tooltipData && (
            <div
              className="constituency-tooltip"
              style={{
                left: `${tooltipPosition.x}px`,
                top: `${tooltipPosition.y}px`,
              }}
              onClick={(e) => e.stopPropagation()}
            >
              <div className="tooltip-close" onClick={() => setTooltipData(null)}>×</div>
              <h4>{tooltipData.constituency_name}</h4>
              <p
                className="tooltip-value"
                style={{
                  color: tooltipData.average_gain >= 0 ? '#16a34a' : '#dc2626'
                }}
              >
                £{tooltipData.average_gain.toFixed(2)}
              </p>
              <p className="tooltip-label">Average gain per household</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
