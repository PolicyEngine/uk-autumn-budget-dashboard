import {
  ComposedChart,
  Bar,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
  LabelList,
} from "recharts";
import "./BudgetaryImpactChart.css";

const POLICY_COLORS = {
  // COSTS to treasury (good for households - teal spectrum)
  "2 child limit repeal": "#0D9488", // Teal (~£3bn)
  "Fuel duty freeze extension": "#5EEAD4", // Light teal (~£1.5bn)

  // REVENUE raisers (bad for households - amber spectrum)
  "Threshold freeze extension": "#D97706", // Amber (~£7bn)
};

// Order: biggest magnitude closest to zero line
const ALL_POLICY_NAMES = [
  // Revenue raisers (positive for gov) - biggest at bottom (closest to zero)
  "Threshold freeze extension",
  // Costs to treasury (negative for gov) - biggest at top (closest to zero)
  "2 child limit repeal",
  "Fuel duty freeze extension",
];

// Custom label component for net impact values
const NetImpactLabel = (props) => {
  const { x, y, value } = props;

  const formattedValue =
    value < 0 ? `-£${Math.abs(value).toFixed(1)}bn` : `£${value.toFixed(1)}bn`;
  const yOffset = value >= 0 ? -20 : 28;

  return (
    <g>
      {/* White background for readability */}
      <rect
        x={x - 32}
        y={y + yOffset - 12}
        width={64}
        height={18}
        fill="white"
        rx={3}
        ry={3}
        stroke="#92400E"
        strokeWidth={1}
      />
      <text
        x={x}
        y={y + yOffset}
        fill="#92400E"
        fontSize={13}
        fontWeight={700}
        textAnchor="middle"
      >
        {formattedValue}
      </text>
    </g>
  );
};

function BudgetaryImpactChart({ data }) {
  if (!data || data.length === 0) return null;

  const formatCurrencyTick = (value) =>
    value < 0 ? `-£${Math.abs(value)}bn` : `£${value}bn`;
  const formatCurrencyTooltip = (value) =>
    value < 0 ? `-£${Math.abs(value).toFixed(1)}bn` : `£${value.toFixed(1)}bn`;

  // Check which policies have non-zero values for legend/tooltip
  const hasNonZeroValues = (policyName) => {
    return data.some((d) => Math.abs(d[policyName] || 0) > 0.001);
  };

  const activePolicies = ALL_POLICY_NAMES.filter(hasNonZeroValues);

  // Fixed y-axis domain to ensure 0 is always a tick mark
  // See: https://github.com/recharts/recharts/issues/6699 for interval={0} not working
  const yAxisDomain = [-40, 40];

  return (
    <div className="budgetary-impact-chart">
      <h2>Revenue impact</h2>
      <p className="chart-description">
        This chart shows the annual budgetary impact from 2026 to 2029, measured
        in billions of pounds. Positive values indicate revenue gains for the
        Government, whilst negative values indicate costs to the Treasury.
      </p>

      <ResponsiveContainer width="100%" height={400}>
        <ComposedChart
          data={data}
          margin={{ top: 15, right: 20, left: 70, bottom: 15 }}
          stackOffset="sign"
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
          <XAxis dataKey="year" tick={{ fontSize: 11, fill: "#666" }} />
          <YAxis
            domain={yAxisDomain}
            label={{
              value: "Impact (£bn)",
              angle: -90,
              position: "insideLeft",
              dx: -30,
              style: {
                textAnchor: "middle",
                fill: "#374151",
                fontSize: 12,
                fontWeight: 500,
              },
            }}
            tickFormatter={formatCurrencyTick}
            tick={{ fontSize: 11, fill: "#666" }}
            interval={0}
            ticks={(() => {
              const [min, max] = yAxisDomain;
              const interval = max <= 20 ? 5 : 10;
              const ticks = [];
              for (let i = min; i <= max + 0.001; i += interval) {
                ticks.push(Math.round(i));
              }
              // Ensure 0 is always included
              if (!ticks.includes(0)) ticks.push(0);
              return ticks.sort((a, b) => a - b);
            })()}
          />
          <Tooltip
            formatter={(value, name) => [
              formatCurrencyTooltip(value),
              name === "netImpact" ? "Net impact" : name,
            ]}
            labelFormatter={(label) => `Year: ${label}`}
            contentStyle={{
              background: "white",
              border: "1px solid #e5e7eb",
              borderRadius: "6px",
            }}
            wrapperStyle={{
              top: "-120px",
              left: "50%",
              transform: "translateX(-50%)",
            }}
            cursor={{ fill: "rgba(49, 151, 149, 0.1)" }}
          />
          <Legend
            wrapperStyle={{ paddingTop: "20px" }}
            iconType="rect"
            formatter={(value) =>
              value === "netImpact" ? "Net impact" : value
            }
            payload={[
              ...activePolicies.map((name) => ({
                value: name,
                type: "rect",
                color: POLICY_COLORS[name],
              })),
              ...(activePolicies.length > 1
                ? [
                    {
                      value: "Net impact",
                      type: "line",
                      color: "#FBBF24",
                    },
                  ]
                : []),
            ]}
          />
          {ALL_POLICY_NAMES.map((policyName) => (
            <Bar
              key={policyName}
              dataKey={policyName}
              fill={POLICY_COLORS[policyName]}
              name={policyName}
              stackId="stack"
              animationDuration={500}
              animationBegin={0}
              hide={!hasNonZeroValues(policyName)}
            />
          ))}
          <Line
            type="monotone"
            dataKey="netImpact"
            stroke="#FBBF24"
            strokeWidth={3}
            dot={{ fill: "#FBBF24", stroke: "#92400E", strokeWidth: 2, r: 5 }}
            name="netImpact"
            animationDuration={500}
            hide={activePolicies.length <= 1}
            label={activePolicies.length > 1 ? <NetImpactLabel /> : false}
          />
          <ReferenceLine y={0} stroke="#374151" strokeWidth={1} />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}

export default BudgetaryImpactChart;
