import { useEffect, useRef, useState, useMemo } from "react";
import * as d3 from "d3";
import YearSlider from "./YearSlider";
import { CHART_LOGO } from "../utils/chartLogo";
import { downloadSvg } from "../utils/downloadFile";
import "./ConstituencyMap.css";
import "./ChartExport.css";

// Chart metadata for export
const CHART_TITLE = "Constituency-level impacts";
const CHART_DESCRIPTION =
  "This map shows the average annual change in household net income across all 650 UK constituencies. Green shading indicates gains, red indicates losses, measured as a percentage of baseline income.";

// Format year for display (e.g., 2026 -> "2026-27")
const formatYearRange = (year) => `${year}-${(year + 1).toString().slice(-2)}`;

/**
 * Convert an image URL to a base64 data URL.
 */
async function imageToBase64(url) {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.crossOrigin = "anonymous";
    img.onload = () => {
      const canvas = document.createElement("canvas");
      canvas.width = img.naturalWidth;
      canvas.height = img.naturalHeight;
      const ctx = canvas.getContext("2d");
      ctx.drawImage(img, 0, 0);
      resolve(canvas.toDataURL("image/png"));
    };
    img.onerror = reject;
    img.src = url;
  });
}

export default function ConstituencyMap({ selectedPolicies = [] }) {
  const [internalYear, setInternalYear] = useState(2026);
  const svgRef = useRef(null);
  const tooltipRef = useRef(null);
  const [selectedConstituency, setSelectedConstituency] = useState(null);
  const [tooltipData, setTooltipData] = useState(null);
  const [tooltipPosition, setTooltipPosition] = useState({ x: 0, y: 0 });
  const [rawData, setRawData] = useState([]);
  const [geoData, setGeoData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState([]);

  // Load data
  useEffect(() => {
    Promise.all([
      fetch("/data/constituency.csv").then((r) => r.text()),
      fetch("/data/uk_constituencies_2024.geojson").then((r) => r.json()),
    ])
      .then(([csvText, geojson]) => {
        // Parse CSV with proper handling of quoted fields
        const parseCSVLine = (line) => {
          const result = [];
          let current = "";
          let inQuotes = false;

          for (let i = 0; i < line.length; i++) {
            const char = line[i];
            if (char === '"') {
              inQuotes = !inQuotes;
            } else if (char === "," && !inQuotes) {
              result.push(current.trim());
              current = "";
            } else {
              current += char;
            }
          }
          result.push(current.trim());
          return result;
        };

        const lines = csvText.split("\n");
        const headers = parseCSVLine(lines[0]);
        const parsedData = lines
          .slice(1)
          .filter((line) => line.trim())
          .map((line) => {
            const values = parseCSVLine(line);
            const row = {};
            headers.forEach((header, idx) => {
              row[header] = values[idx]?.trim();
            });

            return {
              reform_id: row.reform_id,
              year: parseInt(row.year) || 2026,
              constituency_code: row.constituency_code,
              constituency_name: row.constituency_name?.replace(/^"|"$/g, ""),
              average_gain: parseFloat(row.average_gain) || 0,
              relative_change: parseFloat(row.relative_change) || 0,
            };
          });

        setRawData(parsedData);
        setGeoData(geojson);
        setLoading(false);
      })
      .catch((error) => {
        console.error("Error loading data:", error);
        setLoading(false);
      });
  }, []);

  // Aggregate data across selected policies
  const aggregatedData = useMemo(() => {
    if (!rawData.length || !selectedPolicies.length) return [];

    // Group by constituency and sum values across selected policies
    const constituencyMap = new Map();

    rawData.forEach((row) => {
      if (!selectedPolicies.includes(row.reform_id)) return;
      if (row.year !== internalYear) return;

      const key = row.constituency_code;
      if (!constituencyMap.has(key)) {
        constituencyMap.set(key, {
          constituency_code: row.constituency_code,
          constituency_name: row.constituency_name,
          average_gain: 0,
          relative_change: 0,
        });
      }

      const existing = constituencyMap.get(key);
      existing.average_gain += row.average_gain;
      existing.relative_change += row.relative_change;
    });

    return Array.from(constituencyMap.values());
  }, [rawData, selectedPolicies, internalYear]);

  // Render map
  useEffect(() => {
    if (!svgRef.current || !geoData || !aggregatedData.length) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    const width = 800;
    const height = 600;

    const g = svg.append("g");

    // Get bounds of the British National Grid coordinates
    const bounds = {
      xMin: Infinity,
      xMax: -Infinity,
      yMin: Infinity,
      yMax: -Infinity,
    };

    geoData.features.forEach((feature) => {
      const coords = feature.geometry?.coordinates;
      if (!coords) return;

      const traverse = (c) => {
        if (typeof c[0] === "number") {
          bounds.xMin = Math.min(bounds.xMin, c[0]);
          bounds.xMax = Math.max(bounds.xMax, c[0]);
          bounds.yMin = Math.min(bounds.yMin, c[1]);
          bounds.yMax = Math.max(bounds.yMax, c[1]);
        } else {
          c.forEach(traverse);
        }
      };
      traverse(coords);
    });

    // Create scale to fit British National Grid coordinates into SVG
    const padding = 20;
    const dataWidth = bounds.xMax - bounds.xMin;
    const dataHeight = bounds.yMax - bounds.yMin;
    const scale = Math.min(
      (width - 2 * padding) / dataWidth,
      (height - 2 * padding) / dataHeight,
    );

    // Calculate centering offsets
    const scaledWidth = dataWidth * scale;
    const scaledHeight = dataHeight * scale;
    const offsetX = (width - scaledWidth) / 2;
    const offsetY = (height - scaledHeight) / 2;

    const projection = d3.geoTransform({
      point: function (x, y) {
        // Transform British National Grid to SVG coordinates
        this.stream.point(
          (x - bounds.xMin) * scale + offsetX,
          height - ((y - bounds.yMin) * scale + offsetY),
        );
      },
    });

    const path = d3.geoPath().projection(projection);

    const dataMap = new Map(
      aggregatedData.map((d) => [d.constituency_code, d]),
    );

    // Color scale - diverging with white at 0, red for losses, green for gains
    // Use relative_change (percentage of constituency's average income)
    const getValue = (d) => d.relative_change;
    const extent = d3.extent(aggregatedData, getValue);
    const maxAbsValue =
      Math.max(Math.abs(extent[0] || 0), Math.abs(extent[1] || 0)) || 1;

    // Custom interpolator: red -> light grey -> teal (matching chart palette)
    const colorScale = d3
      .scaleDiverging()
      .domain([-maxAbsValue, 0, maxAbsValue])
      .interpolator((t) => {
        if (t < 0.5) {
          // Red to grey (losses to zero)
          const ratio = t * 2; // 0 to 1
          return d3.interpolateRgb("#DC2626", "#E5E7EB")(ratio);
        } else {
          // Grey to teal (zero to gains)
          const ratio = (t - 0.5) * 2; // 0 to 1
          return d3.interpolateRgb("#E5E7EB", "#14B8A6")(ratio);
        }
      });

    // Draw constituencies
    const paths = g
      .selectAll("path")
      .data(geoData.features)
      .join("path")
      .attr("d", path)
      .attr("stroke", "#fff")
      .attr("stroke-width", 0.05)
      .attr("class", "constituency-path")
      .style("cursor", "pointer");

    // Animate fill colors
    paths
      .transition()
      .duration(500)
      .attr("fill", (d) => {
        const constData = dataMap.get(d.properties.GSScode);
        return constData ? colorScale(getValue(constData)) : "#ddd";
      });

    // Add event handlers (must be on selection, not transition)
    paths
      .on("click", function (event, d) {
        event.stopPropagation();

        const constData = dataMap.get(d.properties.GSScode);

        if (constData) {
          // Update styling for all paths
          svg
            .selectAll(".constituency-path")
            .attr("stroke", "#fff")
            .attr("stroke-width", 0.05);

          // Highlight selected constituency
          d3.select(this).attr("stroke", "#1D4044").attr("stroke-width", 0.6);

          setSelectedConstituency(constData);

          // Get centroid of constituency for tooltip positioning
          const bounds = path.bounds(d);
          const centerX = (bounds[0][0] + bounds[1][0]) / 2;
          const centerY = (bounds[0][1] + bounds[1][1]) / 2;

          // Show tooltip
          setTooltipData(constData);
          setTooltipPosition({ x: centerX, y: centerY });

          // Smooth zoom to constituency
          const dx = bounds[1][0] - bounds[0][0];
          const dy = bounds[1][1] - bounds[0][1];
          const x = (bounds[0][0] + bounds[1][0]) / 2;
          const y = (bounds[0][1] + bounds[1][1]) / 2;
          const scale = Math.min(4, 0.9 / Math.max(dx / width, dy / height));
          const translate = [width / 2 - scale * x, height / 2 - scale * y];

          svg
            .transition()
            .duration(750)
            .call(
              zoom.transform,
              d3.zoomIdentity
                .translate(translate[0], translate[1])
                .scale(scale),
            );
        }
      })
      .on("mouseover", function () {
        const currentStrokeWidth = d3.select(this).attr("stroke-width");
        if (currentStrokeWidth === "0.05") {
          d3.select(this).attr("stroke", "#666").attr("stroke-width", 0.3);
        }
      })
      .on("mouseout", function () {
        const currentStrokeWidth = d3.select(this).attr("stroke-width");
        if (currentStrokeWidth !== "0.6") {
          d3.select(this).attr("stroke", "#fff").attr("stroke-width", 0.05);
        }
      });

    // Zoom behavior
    const zoom = d3
      .zoom()
      .scaleExtent([1, 8])
      .on("zoom", (event) => {
        g.attr("transform", event.transform);
      });

    svg.call(zoom);

    // Store zoom behavior for controls
    window.mapZoomBehavior = { svg, zoom };

    // Add PolicyEngine logo in bottom-right corner (outside the zoomable group)
    svg
      .append("image")
      .attr("href", CHART_LOGO.href)
      .attr("width", CHART_LOGO.width)
      .attr("height", CHART_LOGO.height)
      .attr("x", width - CHART_LOGO.width - CHART_LOGO.padding)
      .attr("y", height - CHART_LOGO.height - CHART_LOGO.padding);
  }, [geoData, aggregatedData]);

  // Handle search
  useEffect(() => {
    if (!searchQuery.trim() || !aggregatedData.length) {
      setSearchResults([]);
      return;
    }

    const query = searchQuery.toLowerCase();
    const results = aggregatedData
      .filter((d) => d.constituency_name.toLowerCase().includes(query))
      .slice(0, 5);

    setSearchResults(results);
  }, [searchQuery, aggregatedData]);

  // Zoom control functions
  const handleZoomIn = () => {
    if (window.mapZoomBehavior) {
      const { svg, zoom } = window.mapZoomBehavior;
      svg.transition().duration(300).call(zoom.scaleBy, 1.5);
    }
  };

  const handleZoomOut = () => {
    if (window.mapZoomBehavior) {
      const { svg, zoom } = window.mapZoomBehavior;
      svg.transition().duration(300).call(zoom.scaleBy, 0.67);
    }
  };

  const handleResetZoom = () => {
    if (window.mapZoomBehavior) {
      const { svg, zoom } = window.mapZoomBehavior;
      svg.transition().duration(750).call(zoom.transform, d3.zoomIdentity);
    }
    setTooltipData(null);
    if (svgRef.current) {
      const svg = d3.select(svgRef.current);
      svg
        .selectAll(".constituency-path")
        .attr("stroke", "#fff")
        .attr("stroke-width", 0.05);
    }
  };

  const selectConstituency = (constData) => {
    setSelectedConstituency(constData);
    setSearchQuery("");
    setSearchResults([]);

    if (!geoData || !svgRef.current) return;

    const svg = d3.select(svgRef.current);

    // Update styling for all paths
    svg
      .selectAll(".constituency-path")
      .attr("stroke", "#fff")
      .attr("stroke-width", 0.05);

    // Highlight selected constituency
    const selectedPath = svg
      .selectAll(".constituency-path")
      .filter((d) => d.properties.GSScode === constData.constituency_code);

    selectedPath.attr("stroke", "#1D4044").attr("stroke-width", 0.6);

    // Get the bounding box of the selected path
    const pathNode = selectedPath.node();
    if (!pathNode) return;

    const bbox = pathNode.getBBox();
    const centerX = bbox.x + bbox.width / 2;
    const centerY = bbox.y + bbox.height / 2;

    // Show tooltip
    setTooltipData(constData);
    setTooltipPosition({ x: centerX, y: centerY });

    // Smooth zoom to constituency
    const dx = bbox.width;
    const dy = bbox.height;
    const x = centerX;
    const y = centerY;
    const scale = Math.min(4, 0.9 / Math.max(dx / 800, dy / 500));
    const translate = [800 / 2 - scale * x, 500 / 2 - scale * y];

    if (window.mapZoomBehavior) {
      const { svg: svgZoom, zoom } = window.mapZoomBehavior;
      svgZoom
        .transition()
        .duration(750)
        .call(
          zoom.transform,
          d3.zoomIdentity.translate(translate[0], translate[1]).scale(scale),
        );
    }
  };

  const handleExportSvg = async () => {
    if (!svgRef.current) return;

    const originalSvg = svgRef.current;
    const clonedSvg = originalSvg.cloneNode(true);

    // Reset zoom transform on cloned SVG for clean export
    const gElement = clonedSvg.querySelector("g");
    if (gElement) {
      gElement.removeAttribute("transform");
    }

    // Get dimensions from the original SVG
    const width = 800;
    const height = 600;

    // Style constants
    const padding = 20;
    const titleFontSize = 18;
    const descriptionFontSize = 13;
    const lineHeight = 1.5;

    // Calculate header height
    const titleHeight = titleFontSize + padding;
    const descLines = Math.ceil(CHART_DESCRIPTION.length / 80); // Rough estimate
    const descHeight = descLines * descriptionFontSize * lineHeight + 8;
    const headerHeight = titleHeight + descHeight + padding;

    // Calculate legend height (gradient bar + labels)
    const legendHeight = 50;
    const footerBottomPadding = 20;

    const totalHeight = headerHeight + height + legendHeight;

    // Update SVG dimensions
    clonedSvg.setAttribute("width", width);
    clonedSvg.setAttribute("height", totalHeight);
    clonedSvg.setAttribute("viewBox", `0 0 ${width} ${totalHeight}`);
    clonedSvg.setAttribute("xmlns", "http://www.w3.org/2000/svg");
    clonedSvg.setAttribute("xmlns:xlink", "http://www.w3.org/1999/xlink");

    // Wrap existing content and translate down
    const existingContent = Array.from(clonedSvg.childNodes);
    const contentGroup = document.createElementNS("http://www.w3.org/2000/svg", "g");
    contentGroup.setAttribute("transform", `translate(0, ${headerHeight})`);
    existingContent.forEach((child) => contentGroup.appendChild(child));
    clonedSvg.appendChild(contentGroup);

    // Add white background
    const background = document.createElementNS("http://www.w3.org/2000/svg", "rect");
    background.setAttribute("x", "0");
    background.setAttribute("y", "0");
    background.setAttribute("width", width);
    background.setAttribute("height", totalHeight);
    background.setAttribute("fill", "white");
    clonedSvg.insertBefore(background, contentGroup);

    // Add title
    const title = document.createElementNS("http://www.w3.org/2000/svg", "text");
    title.setAttribute("x", padding);
    title.setAttribute("y", padding + titleFontSize);
    title.setAttribute("style", `font-family: system-ui, -apple-system, sans-serif; font-size: ${titleFontSize}px; font-weight: 600; fill: #374151;`);
    title.textContent = `${CHART_TITLE}, ${formatYearRange(internalYear)}`;
    clonedSvg.insertBefore(title, contentGroup);

    // Add description with word wrapping
    const desc = document.createElementNS("http://www.w3.org/2000/svg", "text");
    desc.setAttribute("x", padding);
    desc.setAttribute("y", padding + titleFontSize + 8 + descriptionFontSize);
    desc.setAttribute("style", `font-family: system-ui, -apple-system, sans-serif; font-size: ${descriptionFontSize}px; font-weight: 400; fill: #4b5563;`);

    // Simple word wrapping
    const maxCharsPerLine = 100;
    const words = CHART_DESCRIPTION.split(" ");
    let lines = [];
    let currentLine = "";
    words.forEach((word) => {
      if ((currentLine + " " + word).length > maxCharsPerLine) {
        lines.push(currentLine);
        currentLine = word;
      } else {
        currentLine = currentLine ? currentLine + " " + word : word;
      }
    });
    if (currentLine) lines.push(currentLine);

    lines.forEach((line, index) => {
      const tspan = document.createElementNS("http://www.w3.org/2000/svg", "tspan");
      tspan.setAttribute("x", padding);
      tspan.setAttribute("dy", index === 0 ? "0" : `${descriptionFontSize * lineHeight}px`);
      tspan.textContent = line;
      desc.appendChild(tspan);
    });
    clonedSvg.insertBefore(desc, contentGroup);

    // Add legend gradient and labels at the bottom
    const legendY = headerHeight + height + 15;
    const gradientWidth = 200;
    const gradientHeight = 12;
    const legendX = (width - gradientWidth) / 2;

    // Create gradient definition
    const defs = document.createElementNS("http://www.w3.org/2000/svg", "defs");
    const gradient = document.createElementNS("http://www.w3.org/2000/svg", "linearGradient");
    gradient.setAttribute("id", "exportLegendGradient");
    gradient.setAttribute("x1", "0%");
    gradient.setAttribute("x2", "100%");

    const stop1 = document.createElementNS("http://www.w3.org/2000/svg", "stop");
    stop1.setAttribute("offset", "0%");
    stop1.setAttribute("stop-color", "#DC2626");
    const stop2 = document.createElementNS("http://www.w3.org/2000/svg", "stop");
    stop2.setAttribute("offset", "50%");
    stop2.setAttribute("stop-color", "#E5E7EB");
    const stop3 = document.createElementNS("http://www.w3.org/2000/svg", "stop");
    stop3.setAttribute("offset", "100%");
    stop3.setAttribute("stop-color", "#14B8A6");

    gradient.appendChild(stop1);
    gradient.appendChild(stop2);
    gradient.appendChild(stop3);
    defs.appendChild(gradient);
    clonedSvg.insertBefore(defs, background);

    // Add gradient rect
    const gradientRect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
    gradientRect.setAttribute("x", legendX);
    gradientRect.setAttribute("y", legendY);
    gradientRect.setAttribute("width", gradientWidth);
    gradientRect.setAttribute("height", gradientHeight);
    gradientRect.setAttribute("fill", "url(#exportLegendGradient)");
    gradientRect.setAttribute("rx", "2");
    clonedSvg.appendChild(gradientRect);

    // Add legend labels
    const labelStyle = "font-family: system-ui, -apple-system, sans-serif; font-size: 12px; font-weight: 500; fill: #374151;";

    const lossLabel = document.createElementNS("http://www.w3.org/2000/svg", "text");
    lossLabel.setAttribute("x", legendX);
    lossLabel.setAttribute("y", legendY + gradientHeight + 15);
    lossLabel.setAttribute("style", labelStyle);
    lossLabel.textContent = "Loss";
    clonedSvg.appendChild(lossLabel);

    const zeroLabel = document.createElementNS("http://www.w3.org/2000/svg", "text");
    zeroLabel.setAttribute("x", legendX + gradientWidth / 2);
    zeroLabel.setAttribute("y", legendY + gradientHeight + 15);
    zeroLabel.setAttribute("style", labelStyle + " text-anchor: middle;");
    zeroLabel.textContent = "0%";
    clonedSvg.appendChild(zeroLabel);

    const gainLabel = document.createElementNS("http://www.w3.org/2000/svg", "text");
    gainLabel.setAttribute("x", legendX + gradientWidth);
    gainLabel.setAttribute("y", legendY + gradientHeight + 15);
    gainLabel.setAttribute("style", labelStyle + " text-anchor: end;");
    gainLabel.textContent = "Gain";
    clonedSvg.appendChild(gainLabel);

    // Embed logo on the right of the legend area
    try {
      const base64Logo = await imageToBase64(CHART_LOGO.href);
      const logoImage = document.createElementNS("http://www.w3.org/2000/svg", "image");
      logoImage.setAttribute("href", base64Logo);
      logoImage.setAttribute("width", CHART_LOGO.width);
      logoImage.setAttribute("height", CHART_LOGO.height);
      logoImage.setAttribute("x", width - CHART_LOGO.width - 10);
      logoImage.setAttribute("y", legendY + (gradientHeight - CHART_LOGO.height) / 2 + 5);
      clonedSvg.appendChild(logoImage);
    } catch (error) {
      console.warn("Failed to embed logo", error);
    }

    // Add tooltip/hovercard if a constituency is selected
    if (tooltipData) {
      const tooltipWidth = 180;
      const tooltipHeight = 110;
      const tooltipPadding = 12;

      // Position tooltip in top-right area of the map (fixed position for export)
      const tooltipX = width - tooltipWidth - 20;
      const tooltipY = headerHeight + 20;

      // Tooltip background with shadow effect
      const tooltipBg = document.createElementNS("http://www.w3.org/2000/svg", "rect");
      tooltipBg.setAttribute("x", tooltipX);
      tooltipBg.setAttribute("y", tooltipY);
      tooltipBg.setAttribute("width", tooltipWidth);
      tooltipBg.setAttribute("height", tooltipHeight);
      tooltipBg.setAttribute("fill", "white");
      tooltipBg.setAttribute("stroke", "#e5e7eb");
      tooltipBg.setAttribute("stroke-width", "1");
      tooltipBg.setAttribute("rx", "8");
      clonedSvg.appendChild(tooltipBg);

      // Constituency name
      const nameText = document.createElementNS("http://www.w3.org/2000/svg", "text");
      nameText.setAttribute("x", tooltipX + tooltipPadding);
      nameText.setAttribute("y", tooltipY + tooltipPadding + 14);
      nameText.setAttribute("style", "font-family: system-ui, -apple-system, sans-serif; font-size: 14px; font-weight: 600; fill: #374151;");
      nameText.textContent = tooltipData.constituency_name.length > 22
        ? tooltipData.constituency_name.substring(0, 20) + "..."
        : tooltipData.constituency_name;
      clonedSvg.appendChild(nameText);

      // Average gain value
      const gainColor = tooltipData.average_gain >= 0 ? "#16a34a" : "#dc2626";
      const gainText = document.createElementNS("http://www.w3.org/2000/svg", "text");
      gainText.setAttribute("x", tooltipX + tooltipPadding);
      gainText.setAttribute("y", tooltipY + tooltipPadding + 38);
      gainText.setAttribute("style", `font-family: system-ui, -apple-system, sans-serif; font-size: 18px; font-weight: 700; fill: ${gainColor};`);
      const absGain = Math.abs(tooltipData.average_gain).toLocaleString("en-GB", { maximumFractionDigits: 0 });
      gainText.textContent = `${tooltipData.average_gain < 0 ? "-" : ""}£${absGain}`;
      clonedSvg.appendChild(gainText);

      // Label for average gain
      const gainLabel = document.createElementNS("http://www.w3.org/2000/svg", "text");
      gainLabel.setAttribute("x", tooltipX + tooltipPadding);
      gainLabel.setAttribute("y", tooltipY + tooltipPadding + 52);
      gainLabel.setAttribute("style", "font-family: system-ui, -apple-system, sans-serif; font-size: 11px; font-weight: 400; fill: #6b7280;");
      gainLabel.textContent = "Average household impact";
      clonedSvg.appendChild(gainLabel);

      // Relative change value
      const relColor = tooltipData.relative_change >= 0 ? "#16a34a" : "#dc2626";
      const relText = document.createElementNS("http://www.w3.org/2000/svg", "text");
      relText.setAttribute("x", tooltipX + tooltipPadding);
      relText.setAttribute("y", tooltipY + tooltipPadding + 72);
      relText.setAttribute("style", `font-family: system-ui, -apple-system, sans-serif; font-size: 14px; font-weight: 600; fill: ${relColor};`);
      relText.textContent = `${tooltipData.relative_change >= 0 ? "+" : ""}${tooltipData.relative_change.toFixed(2)}%`;
      clonedSvg.appendChild(relText);

      // Label for relative change
      const relLabel = document.createElementNS("http://www.w3.org/2000/svg", "text");
      relLabel.setAttribute("x", tooltipX + tooltipPadding);
      relLabel.setAttribute("y", tooltipY + tooltipPadding + 86);
      relLabel.setAttribute("style", "font-family: system-ui, -apple-system, sans-serif; font-size: 11px; font-weight: 400; fill: #6b7280;");
      relLabel.textContent = "Relative change";
      clonedSvg.appendChild(relLabel);
    }

    // Serialize and download
    const serializer = new XMLSerializer();
    const svgString = serializer.serializeToString(clonedSvg);
    downloadSvg(svgString, `constituency-map-${internalYear}`);
  };

  if (loading) {
    return <div className="constituency-loading">Loading map...</div>;
  }

  // Don't render if no policy is selected or no aggregated data
  if (!selectedPolicies.length || !aggregatedData.length) {
    return null;
  }

  return (
    <div className="constituency-map-wrapper">
      {/* Header section */}
      <div className="map-header">
        <div className="chart-header">
          <div>
            <h2>Constituency-level impacts, {formatYearRange(internalYear)}</h2>
            <p className="chart-description">
              This map shows the average annual change in household net income
              across all 650 UK constituencies. Green shading indicates gains, red
              indicates losses, measured as a percentage of baseline income.
            </p>
          </div>
          <button
            className="export-button"
            onClick={handleExportSvg}
            title="Download as SVG"
            aria-label="Download map as SVG"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="7 10 12 15 17 10" />
              <line x1="12" y1="15" x2="12" y2="3" />
            </svg>
          </button>
        </div>
      </div>

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
                    <div className="result-name">
                      {result.constituency_name}
                    </div>
                    <div className="result-value">
                      £{result.average_gain.toFixed(0)} (
                      {result.relative_change.toFixed(2)}%)
                    </div>
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
              <span className="legend-zero">0%</span>
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
            height="568"
            viewBox="0 0 800 600"
            preserveAspectRatio="xMidYMid meet"
            onClick={() => {
              setTooltipData(null);
              if (svgRef.current) {
                const svg = d3.select(svgRef.current);
                svg
                  .selectAll(".constituency-path")
                  .attr("stroke", "#fff")
                  .attr("stroke-width", 0.05);
              }
            }}
          />

          {/* Map controls */}
          <div
            className="map-controls-container"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Zoom controls */}
            <div className="zoom-controls">
              <button
                className="zoom-control-btn"
                onClick={handleZoomIn}
                title="Zoom in"
                aria-label="Zoom in"
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
                  <circle
                    cx="10"
                    cy="10"
                    r="7"
                    stroke="currentColor"
                    strokeWidth="2"
                  />
                  <path
                    d="M10 7V13M7 10H13"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                  />
                  <path
                    d="M15 15L20 20"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                  />
                </svg>
              </button>
              <button
                className="zoom-control-btn"
                onClick={handleZoomOut}
                title="Zoom out"
                aria-label="Zoom out"
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
                  <circle
                    cx="10"
                    cy="10"
                    r="7"
                    stroke="currentColor"
                    strokeWidth="2"
                  />
                  <path
                    d="M7 10H13"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                  />
                  <path
                    d="M15 15L20 20"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                  />
                </svg>
              </button>
              <button
                className="zoom-control-btn"
                onClick={handleResetZoom}
                title="Reset zoom"
                aria-label="Reset zoom"
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
                  <path
                    d="M21 12C21 16.9706 16.9706 21 12 21C7.02944 21 3 16.9706 3 12C3 7.02944 7.02944 3 12 3C14.8273 3 17.35 4.30367 19 6.34267"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                  />
                  <path
                    d="M21 3V8H16"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
              </button>
            </div>
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
              <div
                className="tooltip-close"
                onClick={() => setTooltipData(null)}
              >
                ×
              </div>
              <h4>{tooltipData.constituency_name}</h4>
              <p
                className="tooltip-value"
                style={{
                  color: tooltipData.average_gain >= 0 ? "#16a34a" : "#dc2626",
                }}
              >
                {tooltipData.average_gain < 0 ? "-" : ""}£
                {Math.abs(tooltipData.average_gain).toLocaleString("en-GB", {
                  maximumFractionDigits: 0,
                })}
              </p>
              <p className="tooltip-label">Average household impact</p>
              <p
                className="tooltip-value-secondary"
                style={{
                  color:
                    tooltipData.relative_change >= 0 ? "#16a34a" : "#dc2626",
                }}
              >
                {tooltipData.relative_change >= 0 ? "+" : ""}
                {tooltipData.relative_change.toFixed(2)}%
              </p>
              <p className="tooltip-label">Relative change</p>
            </div>
          )}
        </div>
      </div>

      <YearSlider selectedYear={internalYear} onYearChange={setInternalYear} />
    </div>
  );
}
