import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import BudgetaryImpactChart from "./BudgetaryImpactChart";

// Recharts ResponsiveContainer measures the parent in jsdom and refuses
// to render its children when width / height resolve to zero. Replace it
// with a fixed-size wrapper so the BarChart renders deterministic ticks.
vi.mock("recharts", async () => {
  const actual = await vi.importActual("recharts");
  return {
    ...actual,
    ResponsiveContainer: ({ children }) => (
      <div data-testid="recharts-responsive-container" style={{ width: 800, height: 500 }}>
        {children}
      </div>
    ),
  };
});

// Mock data that produces domain around [-35, 35]
const mockData = [
  {
    year: 2026,
    "Income tax increase (basic and higher +2pp)": 20,
    "Threshold freeze extension": 5,
    "Salary sacrifice cap": 1,
    "National Insurance rate reduction": -12,
    "Zero-rate VAT on domestic energy": -3,
    "2 child limit repeal": -3,
    "Fuel duty freeze": -1.5,
    netImpact: 6.5,
  },
];

describe("BudgetaryImpactChart", () => {
  it("renders a recharts ResponsiveContainer", () => {
    render(<BudgetaryImpactChart data={mockData} />);
    expect(
      screen.getByTestId("recharts-responsive-container"),
    ).toBeInTheDocument();
  });
});
