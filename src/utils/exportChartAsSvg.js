/**
 * Export Recharts charts as SVG files with title, description, and legend.
 */

import {
  createSvgElement,
  createSvgText,
  createSvgRect,
  createSvgLine,
  createSvgGroup,
  createSvgTspan,
  addSvgNamespaces,
  serializeSvg,
} from "./svgHelpers";
import { measureTextWidth, wrapText, estimateTextHeight } from "./textMeasure";
import { downloadSvg } from "./downloadFile";

/**
 * Convert an image URL to a base64 data URL.
 * This allows embedding images directly in the SVG for standalone export.
 *
 * @param {string} url - URL or path to the image
 * @returns {Promise<string>} - Base64 data URL
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

// Style constants
const STYLES = {
  padding: 20,
  titleFontSize: 18,
  descriptionFontSize: 13,
  legendFontSize: 12,
  lineHeight: 1.5,
  titleDescGap: 8,
  legendHeight: 40,
  legendIconSize: 14,
  legendIconTextGap: 6,
  legendItemGap: 24,
  colors: {
    title: "#374151",
    description: "#4b5563",
    legendText: "#374151",
    background: "white",
  },
};

// SVG style properties to inline for consistent rendering
const SVG_STYLE_PROPERTIES = [
  "fill",
  "stroke",
  "stroke-width",
  "stroke-dasharray",
  "stroke-linecap",
  "stroke-linejoin",
  "stroke-opacity",
  "fill-opacity",
  "opacity",
  "font-family",
  "font-size",
  "font-weight",
  "font-style",
  "text-anchor",
  "dominant-baseline",
  "alignment-baseline",
  "visibility",
  "display",
];

/**
 * Recursively inline computed styles onto SVG elements.
 * This ensures the SVG looks the same when opened outside the browser.
 *
 * @param {Element} clonedElement - The cloned element to modify
 * @param {Element} originalElement - The original element to get computed styles from
 */
function inlineComputedStyles(clonedElement, originalElement) {
  const computedStyle = window.getComputedStyle(originalElement);

  const styleValues = SVG_STYLE_PROPERTIES.map((prop) => {
    const value = computedStyle.getPropertyValue(prop);
    return value && value !== "none" && value !== "normal" ? `${prop}: ${value}` : null;
  }).filter(Boolean);

  if (styleValues.length > 0) {
    const existingStyle = clonedElement.getAttribute("style") || "";
    const newStyle = existingStyle
      ? `${existingStyle}; ${styleValues.join("; ")}`
      : styleValues.join("; ");
    clonedElement.setAttribute("style", newStyle);
  }

  // Process children recursively
  const clonedChildren = clonedElement.children;
  const originalChildren = originalElement.children;

  for (let i = 0; i < clonedChildren.length && i < originalChildren.length; i++) {
    inlineComputedStyles(clonedChildren[i], originalChildren[i]);
  }
}

/**
 * Create an SVG legend from legend items.
 *
 * @param {Array<{color: string, label: string, type: string}>} items - Legend items
 * @param {number} chartWidth - Width of the chart for centering
 * @param {number} yPosition - Y position for the legend
 * @returns {SVGGElement}
 */
function createLegend(items, chartWidth, yPosition) {
  const { legendFontSize, legendIconSize, legendIconTextGap, legendItemGap, colors } = STYLES;

  // Calculate item widths and total width
  const itemWidths = items.map((item) => {
    const textWidth = measureTextWidth(item.label, { fontSize: legendFontSize });
    return legendIconSize + legendIconTextGap + textWidth;
  });
  const totalWidth = itemWidths.reduce((sum, w) => sum + w, 0) + (items.length - 1) * legendItemGap;

  // Create legend group, centered horizontally
  const legendGroup = createSvgGroup({ className: "exported-legend" });
  let currentX = (chartWidth - totalWidth) / 2;

  items.forEach((item, index) => {
    const itemGroup = createSvgGroup();

    // Draw icon based on type
    if (item.type === "line") {
      const line = createSvgLine({
        x1: currentX,
        y1: yPosition,
        x2: currentX + legendIconSize,
        y2: yPosition,
        stroke: item.color,
        strokeWidth: 2,
      });
      itemGroup.appendChild(line);
    } else {
      const rect = createSvgRect({
        x: currentX,
        y: yPosition - legendIconSize / 2,
        width: legendIconSize,
        height: legendIconSize,
        fill: item.color,
      });
      itemGroup.appendChild(rect);
    }

    // Draw label with proper font styling
    const text = createSvgText(item.label, {
      x: currentX + legendIconSize + legendIconTextGap,
      y: yPosition + legendFontSize / 3,
      fontSize: legendFontSize,
      fontWeight: "400",
      fill: colors.legendText,
    });
    itemGroup.appendChild(text);

    legendGroup.appendChild(itemGroup);
    currentX += itemWidths[index] + legendItemGap;
  });

  return legendGroup;
}

/**
 * Create SVG title element.
 *
 * @param {string} title - Title text
 * @param {number} y - Y position
 * @returns {SVGTextElement}
 */
function createTitle(title, y) {
  return createSvgText(title, {
    x: STYLES.padding,
    y,
    fontSize: STYLES.titleFontSize,
    fontWeight: "600",
    fill: STYLES.colors.title,
  });
}

/**
 * Create SVG description element with word wrapping.
 *
 * @param {string} description - Description text
 * @param {number} y - Y position
 * @param {number} maxWidth - Maximum width for text wrapping
 * @returns {SVGTextElement}
 */
function createDescription(description, y, maxWidth) {
  const { descriptionFontSize, lineHeight, padding, colors } = STYLES;

  const textElement = createSvgElement("text", { x: padding, y });
  textElement.setAttribute(
    "style",
    `font-family: system-ui, -apple-system, sans-serif; font-size: ${descriptionFontSize}px; font-weight: 400; fill: ${colors.description};`
  );

  const lines = wrapText(description, maxWidth, { fontSize: descriptionFontSize });

  lines.forEach((line, index) => {
    const tspan = createSvgTspan(line, {
      x: padding,
      dy: index === 0 ? "0" : `${descriptionFontSize * lineHeight}px`,
    });
    textElement.appendChild(tspan);
  });

  return textElement;
}

/**
 * Calculate the header height needed for title and description.
 *
 * @param {Object} options - Options containing title and description
 * @param {number} chartWidth - Chart width for text wrapping calculation
 * @returns {number} - Header height in pixels
 */
function calculateHeaderHeight({ title, description }, chartWidth) {
  const { padding, titleFontSize, descriptionFontSize, lineHeight, titleDescGap } = STYLES;
  let height = 0;

  if (title) {
    height += titleFontSize + padding;
  }

  if (description) {
    const maxWidth = chartWidth - padding * 2;
    const descHeight = estimateTextHeight(description, maxWidth, {
      fontSize: descriptionFontSize,
      lineHeight,
    });
    height += descHeight + titleDescGap;
  }

  if (title || description) {
    height += padding; // Bottom padding before chart
  }

  return height;
}

/**
 * Export a Recharts chart as an SVG file.
 *
 * @param {React.RefObject} containerRef - Ref to the chart container element
 * @param {string} filename - The filename for the downloaded SVG (without extension)
 * @param {Object} options - Export options
 * @param {string} options.title - Title to display above the chart
 * @param {string} options.description - Description text below the title
 * @param {Array<{color: string, label: string, type: string}>} options.legendItems - Legend items
 * @param {Object} options.logo - Logo configuration
 * @param {string} options.logo.href - URL/path to logo image
 * @param {number} options.logo.width - Logo width
 * @param {number} options.logo.height - Logo height
 * @param {number} options.logo.padding - Padding from edges
 * @returns {Promise<boolean>} - True if export was successful
 */
export async function exportChartAsSvg(containerRef, filename = "chart", options = {}) {
  const { title, description, legendItems = [], logo } = options;

  if (!containerRef?.current) {
    console.error("exportChartAsSvg: No container ref provided");
    return false;
  }

  // Find the SVG element within the Recharts container
  const rechartsWrapper = containerRef.current.querySelector(".recharts-wrapper");
  const svgElement = rechartsWrapper?.querySelector("svg");

  if (!svgElement) {
    console.error("exportChartAsSvg: No SVG element found in container");
    return false;
  }

  // Get dimensions
  const bbox = svgElement.getBoundingClientRect();
  const chartWidth = bbox.width;
  const chartHeight = bbox.height;

  // Clone and prepare SVG
  const clonedSvg = svgElement.cloneNode(true);
  inlineComputedStyles(clonedSvg, svgElement);

  // Calculate layout
  const headerHeight = calculateHeaderHeight({ title, description }, chartWidth);
  const legendHeight = legendItems.length > 0 ? STYLES.legendHeight : 0;
  const totalHeight = chartHeight + headerHeight + legendHeight;

  // Update SVG dimensions
  clonedSvg.setAttribute("width", chartWidth);
  clonedSvg.setAttribute("height", totalHeight);
  clonedSvg.setAttribute("viewBox", `0 0 ${chartWidth} ${totalHeight}`);
  addSvgNamespaces(clonedSvg);

  // Wrap existing content and translate down
  const existingContent = Array.from(clonedSvg.childNodes);
  const contentGroup = createSvgGroup({ transform: `translate(0, ${headerHeight})` });
  existingContent.forEach((child) => contentGroup.appendChild(child));
  clonedSvg.appendChild(contentGroup);

  // Add white background
  const background = createSvgRect({
    x: 0,
    y: 0,
    width: chartWidth,
    height: totalHeight,
    fill: STYLES.colors.background,
  });
  clonedSvg.insertBefore(background, contentGroup);

  // Add title
  let currentY = STYLES.padding;
  if (title) {
    const titleElement = createTitle(title, currentY + STYLES.titleFontSize);
    clonedSvg.insertBefore(titleElement, contentGroup);
    currentY += STYLES.titleFontSize + STYLES.titleDescGap;
  }

  // Add description
  if (description) {
    const maxWidth = chartWidth - STYLES.padding * 2;
    const descElement = createDescription(description, currentY + STYLES.descriptionFontSize, maxWidth);
    clonedSvg.insertBefore(descElement, contentGroup);
  }

  // Add legend
  if (legendItems.length > 0) {
    const legendY = headerHeight + chartHeight + legendHeight / 2;
    const legendGroup = createLegend(legendItems, chartWidth, legendY);
    clonedSvg.appendChild(legendGroup);
  }

  // Embed logo if provided
  if (logo?.href) {
    try {
      // Convert logo to base64 for standalone SVG
      const base64Logo = await imageToBase64(logo.href);
      const logoImage = createSvgElement("image", {
        width: logo.width,
        height: logo.height,
      });
      logoImage.setAttribute("href", base64Logo);

      // Position logo in bottom-right of chart area (before legend)
      // Use larger horizontal margin (30px) to bring it in from the edge
      const logoMarginRight = 30;
      const logoMarginBottom = logo.padding || 12;
      const logoX = chartWidth - logo.width - logoMarginRight;
      const logoY = headerHeight + chartHeight - logo.height - logoMarginBottom;
      logoImage.setAttribute("x", logoX);
      logoImage.setAttribute("y", logoY);

      clonedSvg.appendChild(logoImage);
    } catch (error) {
      console.warn("exportChartAsSvg: Failed to embed logo", error);
    }
  }

  // Serialize and download
  const svgString = serializeSvg(clonedSvg);
  downloadSvg(svgString, filename);

  return true;
}

export default exportChartAsSvg;
