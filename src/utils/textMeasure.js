/**
 * Text measurement utilities using Canvas API.
 */

const DEFAULT_FONT = "system-ui, -apple-system, sans-serif";

// Shared canvas context for text measurement (lazy initialized)
let measureContext = null;

/**
 * Get a shared canvas context for text measurement.
 * @returns {CanvasRenderingContext2D}
 */
function getContext() {
  if (!measureContext) {
    const canvas = document.createElement("canvas");
    measureContext = canvas.getContext("2d");
  }
  return measureContext;
}

/**
 * Measure the width of text using Canvas API.
 *
 * @param {string} text - The text to measure
 * @param {Object} options - Font options
 * @param {number} options.fontSize - Font size in pixels
 * @param {string} options.fontWeight - Font weight (default "400")
 * @param {string} options.fontFamily - Font family (default system fonts)
 * @returns {number} - The width in pixels
 */
export function measureTextWidth(
  text,
  { fontSize, fontWeight = "400", fontFamily = DEFAULT_FONT },
) {
  const context = getContext();
  context.font = `${fontWeight} ${fontSize}px ${fontFamily}`;
  return context.measureText(text).width;
}

/**
 * Word-wrap text to fit within a maximum width.
 *
 * @param {string} text - The text to wrap
 * @param {number} maxWidth - Maximum width in pixels
 * @param {Object} options - Font options
 * @param {number} options.fontSize - Font size in pixels
 * @param {string} options.fontWeight - Font weight (default "400")
 * @param {string} options.fontFamily - Font family (default system fonts)
 * @returns {string[]} - Array of lines
 */
export function wrapText(
  text,
  maxWidth,
  { fontSize, fontWeight = "400", fontFamily = DEFAULT_FONT },
) {
  const context = getContext();
  context.font = `${fontWeight} ${fontSize}px ${fontFamily}`;

  const words = text.split(" ");
  const lines = [];
  let currentLine = "";

  for (const word of words) {
    const testLine = currentLine ? `${currentLine} ${word}` : word;
    const metrics = context.measureText(testLine);

    if (metrics.width > maxWidth && currentLine) {
      lines.push(currentLine);
      currentLine = word;
    } else {
      currentLine = testLine;
    }
  }

  if (currentLine) {
    lines.push(currentLine);
  }

  return lines;
}

/**
 * Estimate the height needed for wrapped text.
 *
 * @param {string} text - The text to measure
 * @param {number} maxWidth - Maximum width in pixels
 * @param {Object} options - Font options
 * @param {number} options.fontSize - Font size in pixels
 * @param {number} options.lineHeight - Line height multiplier (default 1.5)
 * @param {string} options.fontWeight - Font weight (default "400")
 * @returns {number} - Estimated height in pixels
 */
export function estimateTextHeight(
  text,
  maxWidth,
  { fontSize, lineHeight = 1.5, fontWeight = "400" },
) {
  const lines = wrapText(text, maxWidth, { fontSize, fontWeight });
  return lines.length * fontSize * lineHeight;
}
