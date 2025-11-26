"""Data models for UK Budget Data pipeline."""

from pathlib import Path
from typing import Any, Callable, Optional

from policyengine_uk import Scenario
from pydantic import BaseModel, Field


class Reform(BaseModel):
    """Definition of a policy reform.

    A reform can be defined either via parameter changes (simple reforms)
    or via a simulation modifier function (structural reforms).
    """

    id: str = Field(..., description="Unique identifier for the reform")
    name: str = Field(..., description="Human-readable name")
    description: str = Field(
        default="", description="Detailed description of the reform"
    )
    parameter_changes: Optional[dict[str, dict[str, Any]]] = Field(
        default=None,
        description="Parameter path -> {period: value} mappings",
    )
    simulation_modifier: Optional[Callable] = Field(
        default=None,
        description="Function that modifies a simulation object",
    )

    model_config = {"arbitrary_types_allowed": True}

    def to_scenario(self) -> Scenario:
        """Convert this reform to a PolicyEngine Scenario object."""
        if self.simulation_modifier is not None:
            return Scenario(simulation_modifier=self.simulation_modifier)
        elif self.parameter_changes is not None:
            return Scenario(parameter_changes=self.parameter_changes)
        else:
            return Scenario()


class ReformResult(BaseModel):
    """Results from processing a single reform."""

    reform_id: str
    reform_name: str
    budgetary_impact: list[dict]
    distributional_impact: list[dict]
    winners_losers: list[dict]
    metrics: list[dict]
    income_curve: list[dict]
    household_scatter: list[dict]
    constituency: list[dict]
    demographic_constituency: list[dict]

    model_config = {"arbitrary_types_allowed": True}


class DataConfig(BaseModel):
    """Configuration for the data generation pipeline."""

    years: list[int] = Field(
        default=[2026, 2027, 2028, 2029],
        description="Years to calculate metrics for",
    )
    output_dir: Path = Field(
        default=Path("./public/data"),
        description="Directory to write output CSVs",
    )
    data_dir: Path = Field(
        default=Path("./data"),
        description="Directory containing input data files",
    )
    data_inputs_dir: Path = Field(
        default=Path("./data_inputs"),
        description="Directory containing reference data",
    )
    dataset_path: Optional[Path] = Field(
        default=None,
        description="Path to enhanced FRS dataset (optional)",
    )
    income_curve_max: int = Field(
        default=150_000,
        description="Maximum employment income for curve",
    )
    income_curve_points: int = Field(
        default=201,
        description="Number of points on income curve",
    )
    household_scatter_max_income: int = Field(
        default=150_000,
        description="Max baseline income for scatter plot",
    )

    model_config = {"arbitrary_types_allowed": True}
