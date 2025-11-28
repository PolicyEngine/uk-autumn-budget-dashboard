"""Flask API for personal impact calculations.

This module provides a REST API endpoint for calculating how Autumn Budget
policies affect individual households over time.
"""

import json

import numpy as np
from flask import Flask, Response, jsonify, request
from flask_cors import CORS
from pydantic import BaseModel, Field, field_validator

from uk_budget_data.personal_impact import (
    HouseholdInput,
    PersonalImpactCalculator,
)

app = Flask(__name__)
CORS(app)


class APIHouseholdInput(BaseModel):
    """API request model for household inputs."""

    employment_income: float = Field(
        ..., ge=0, description="Annual employment income in 2025 (GBP)"
    )
    income_growth_rate: float = Field(
        default=0.0,
        ge=-0.5,
        le=0.5,
        description="Annual income growth rate (e.g., 0.03 for 3%)",
    )
    is_married: bool = Field(
        default=False, description="Whether the person is married/cohabiting"
    )
    partner_income: float = Field(
        default=0.0,
        ge=0,
        description="Partner's annual employment income (GBP)",
    )
    children_ages: list[int] = Field(
        default_factory=list,
        description="Ages of children in 2025",
    )
    property_income: float = Field(
        default=0.0, ge=0, description="Annual property income (GBP)"
    )
    savings_income: float = Field(
        default=0.0, ge=0, description="Annual savings/interest income (GBP)"
    )
    dividend_income: float = Field(
        default=0.0, ge=0, description="Annual dividend income (GBP)"
    )
    pension_contributions_salary_sacrifice: float = Field(
        default=0.0,
        ge=0,
        description="Annual salary sacrifice pension contributions (GBP)",
    )
    fuel_spending: float = Field(
        default=0.0,
        ge=0,
        description="Annual fuel spending (GBP)",
    )
    rail_spending: float = Field(
        default=0.0,
        ge=0,
        description="Annual rail spending (GBP)",
    )

    @field_validator("children_ages")
    @classmethod
    def validate_children_ages(cls, v):
        """Validate that children ages are reasonable."""
        if len(v) > 10:
            raise ValueError("Maximum 10 children supported")
        for age in v:
            if age < 0 or age > 25:
                raise ValueError("Children ages must be between 0 and 25")
        return v


def convert_api_input_to_household(api_input: APIHouseholdInput) -> dict:
    """Convert API input to the format expected by PersonalImpactCalculator."""
    return HouseholdInput(
        employment_income=api_input.employment_income,
        income_growth_rate=api_input.income_growth_rate,
        is_married=api_input.is_married,
        partner_income=api_input.partner_income,
        children_ages=api_input.children_ages,
        property_income=api_input.property_income,
        savings_income=api_input.savings_income,
        dividend_income=api_input.dividend_income,
        pension_contributions_salary_sacrifice=(
            api_input.pension_contributions_salary_sacrifice
        ),
        fuel_spending=api_input.fuel_spending,
        rail_spending=api_input.rail_spending,
    )


# Lazy-load calculator to avoid startup delay
_calculator: PersonalImpactCalculator | None = None


def get_calculator() -> PersonalImpactCalculator:
    """Get or create the PersonalImpactCalculator (lazy singleton)."""
    global _calculator
    if _calculator is None:
        _calculator = PersonalImpactCalculator()
    return _calculator


@app.route("/api/personal-impact", methods=["POST"])
def calculate_personal_impact():
    """Calculate personal impact for a household.

    Request body (JSON):
        employment_income: Annual employment income in 2025 (required)
        income_growth_rate: Annual growth rate (default: 0)
        is_married: Whether married/cohabiting (default: false)
        partner_income: Partner's income (default: 0)
        children_ages: List of children's ages in 2025 (default: [])
        student_loan_plan: Plan type (default: null)
        student_loan_balance: Initial balance (default: 0)
        property_income: Annual property income (default: 0)
        savings_income: Annual savings income (default: 0)
        dividend_income: Annual dividend income (default: 0)
        pension_contributions_salary_sacrifice: Annual SS contributions
            (default: 0)

    Returns:
        JSON with year-by-year impact breakdown per policy.
    """
    try:
        # Parse and validate input
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        api_input = APIHouseholdInput(**data)
        household_input = convert_api_input_to_household(api_input)

        # Calculate impacts
        calculator = get_calculator()
        results = calculator.calculate(household_input)

        # Convert numpy types to Python native types for JSON serialisation
        def convert_to_native(obj):
            if isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, dict):
                return {k: convert_to_native(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_to_native(item) for item in obj]
            return obj

        return jsonify(convert_to_native(results))

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Calculation error: {str(e)}"}), 500


@app.route("/api/personal-impact/stream", methods=["POST"])
def calculate_personal_impact_stream():
    """Stream personal impact results year-by-year using SSE.

    Returns Server-Sent Events with progressive results as each year
    is calculated. This provides faster feedback to users.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        api_input = APIHouseholdInput(**data)
        household_input = convert_api_input_to_household(api_input)
        calculator = get_calculator()

        def generate():
            for event in calculator.calculate_streaming(household_input):
                # Convert numpy types
                event_data = convert_to_native(event)
                yield f"data: {json.dumps(event_data)}\n\n"

        return Response(
            generate(),
            mimetype="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
            },
        )

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Calculation error: {str(e)}"}), 500


def convert_to_native(obj):
    """Convert numpy types to Python native types for JSON serialisation."""
    if isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, dict):
        return {k: convert_to_native(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_native(item) for item in obj]
    return obj


@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "healthy"})


def main():
    """Run the Flask development server."""
    print("Starting UK Budget Personal Impact API...")
    print("API available at http://localhost:5001/api/personal-impact")
    app.run(host="0.0.0.0", port=5001, debug=True)


if __name__ == "__main__":
    main()
