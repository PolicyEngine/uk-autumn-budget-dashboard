import { useState, useEffect, useRef } from "react";
import "./MetricsBar.css";

// Animated number component with smooth transitions
function AnimatedNumber({ value, format = (v) => v, duration = 800 }) {
  const [displayValue, setDisplayValue] = useState(value);
  const rafRef = useRef(null);
  const prevValueRef = useRef(value);

  useEffect(() => {
    const startValue = prevValueRef.current;
    const startTime = performance.now();

    const animate = (currentTime) => {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);

      // Ease-out cubic for smooth deceleration
      const eased = 1 - Math.pow(1 - progress, 3);
      const current = startValue + (value - startValue) * eased;

      setDisplayValue(current);

      if (progress < 1) {
        rafRef.current = requestAnimationFrame(animate);
      } else {
        prevValueRef.current = value;
      }
    };

    rafRef.current = requestAnimationFrame(animate);

    return () => {
      if (rafRef.current) {
        cancelAnimationFrame(rafRef.current);
      }
    };
  }, [value, duration]);

  return <>{format(displayValue)}</>;
}

function MetricsBar({ metrics }) {
  if (!metrics) return null;

  const formatBillions = (value) => `£${value.toFixed(2)}bn`;
  const formatPercent = (value) => `${value.toFixed(1)}%`;
  const formatNumber = (value) => `${value.toFixed(2)}`;

  return (
    <div className="metrics-bar">
      <div className="metric-card">
        <div className="metric-label">2026 budgetary impact</div>
        <div className="metric-value">
          <AnimatedNumber
            value={metrics.budgetaryImpact2026}
            format={formatBillions}
          />
        </div>
      </div>

      <div className="metric-card">
        <div className="metric-label">People affected</div>
        <div className="metric-value">
          <AnimatedNumber
            value={metrics.percentAffected}
            format={formatPercent}
          />
        </div>
      </div>

      <div className="metric-card">
        <div className="metric-label">Change in inequality</div>
        <div className="metric-value">
          <AnimatedNumber value={metrics.giniChange} format={formatNumber} />
        </div>
      </div>

      <div className="metric-card">
        <div className="metric-label">
          Change in poverty rate (relative AHC)
        </div>
        <div className="metric-value">
          <AnimatedNumber
            value={metrics.povertyRateChange}
            format={formatNumber}
          />
        </div>
      </div>
    </div>
  );
}

export default MetricsBar;
