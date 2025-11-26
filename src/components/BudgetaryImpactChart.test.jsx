import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import BudgetaryImpactChart from "./BudgetaryImpactChart";

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
  it("should display a tick label at y=0", () => {
    render(<BudgetaryImpactChart data={mockData} />);

    // Look for £0.0bn tick label
    const zeroTick = screen.getByText("£0.0bn");
    expect(zeroTick).toBeInTheDocument();
  });
});
