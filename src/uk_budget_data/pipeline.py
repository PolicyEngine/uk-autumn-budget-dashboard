"""Data generation pipeline for UK Budget dashboard.

This module provides the main pipeline for generating all dashboard data
from a list of reforms.
"""

import json
from datetime import datetime
from importlib.metadata import version as get_version
from pathlib import Path
from typing import Optional

import h5py
import pandas as pd
from policyengine_uk import Microsimulation
from policyengine_uk.data import UKSingleYearDataset
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from uk_budget_data.calculators import (
    BudgetaryImpactCalculator,
    ConstituencyCalculator,
    DemographicConstituencyCalculator,
    DistributionalImpactCalculator,
    HouseholdScatterCalculator,
    IncomeCurveCalculator,
    MetricsCalculator,
    WinnersLosersCalculator,
)
from uk_budget_data.models import DataConfig, Reform, ReformResult
from uk_budget_data.reforms import get_autumn_budget_2025_reforms

console = Console()


def save_csv(df: pd.DataFrame, csv_path: Path) -> None:
    """Save DataFrame to CSV, creating parent directories if needed."""
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(csv_path, index=False)


def merge_with_existing(
    new_df: pd.DataFrame,
    csv_path: Path,
    key_columns: list[str],
) -> pd.DataFrame:
    """Merge new data with existing CSV, updating matching rows.

    Args:
        new_df: New data to merge.
        csv_path: Path to existing CSV file.
        key_columns: Columns that uniquely identify rows (e.g., reform_id, year).

    Returns:
        Merged DataFrame with existing data preserved and new data updated.
    """
    if not csv_path.exists() or len(new_df) == 0:
        return new_df

    existing_df = pd.read_csv(csv_path)

    if len(existing_df) == 0:
        return new_df

    # Get the reform_ids being updated
    new_reform_ids = set(new_df["reform_id"].unique())

    # Keep rows from existing that are NOT being updated
    existing_to_keep = existing_df[
        ~existing_df["reform_id"].isin(new_reform_ids)
    ]

    # Combine: existing (excluding updated reforms) + new data
    merged = pd.concat([existing_to_keep, new_df], ignore_index=True)

    # Sort for consistent output (by key columns if they exist)
    sort_cols = [c for c in key_columns if c in merged.columns]
    if sort_cols:
        merged = merged.sort_values(sort_cols).reset_index(drop=True)

    return merged


def check_input_data(config: DataConfig) -> None:
    """Check that required input files exist.

    Args:
        config: Data configuration with paths.

    Raises:
        FileNotFoundError: If required files are missing.
    """
    weights_path = config.data_dir / "parliamentary_constituency_weights.h5"
    constituencies_path = config.data_inputs_dir / "constituencies_2024.csv"

    if not weights_path.exists():
        console.print(f"[red]Error: {weights_path} not found[/red]")
        raise FileNotFoundError(f"Required file not found: {weights_path}")

    if not constituencies_path.exists():
        console.print(f"[red]Error: {constituencies_path} not found[/red]")
        raise FileNotFoundError(
            f"Required file not found: {constituencies_path}"
        )

    console.print("[green]✓[/green] Found required constituency data files")


class ReformProcessor:
    """Processes a single reform to generate all metrics."""

    def __init__(
        self,
        reform: Reform,
        config: Optional[DataConfig] = None,
    ):
        """Initialize the processor.

        Args:
            reform: The reform to process.
            config: Data configuration (uses defaults if not provided).
        """
        self.reform = reform
        self.config = config or DataConfig()

        # Initialize calculators
        self.budgetary_calc = BudgetaryImpactCalculator(
            years=self.config.years
        )
        self.distributional_calc = DistributionalImpactCalculator()
        self.winners_losers_calc = WinnersLosersCalculator()
        self.metrics_calc = MetricsCalculator()
        self.income_curve_calc = IncomeCurveCalculator(
            max_income=self.config.income_curve_max,
            num_points=self.config.income_curve_points,
        )
        self.household_scatter_calc = HouseholdScatterCalculator(
            max_income=self.config.household_scatter_max_income,
        )
        self.constituency_calc = ConstituencyCalculator()
        self.demographic_calc = DemographicConstituencyCalculator()

    def process(
        self,
        baseline: Microsimulation,
        reformed: Microsimulation,
    ) -> ReformResult:
        """Process the reform and return all metrics.

        Args:
            baseline: Baseline microsimulation.
            reformed: Reformed microsimulation.

        Returns:
            ReformResult with all calculated metrics.
        """
        reform_id = self.reform.id
        reform_name = self.reform.name

        # Calculate budgetary impact
        budgetary = self.budgetary_calc.calculate(
            baseline, reformed, reform_id, reform_name
        )

        # Calculate per-year metrics
        all_distributional = []
        all_winners_losers = []
        all_metrics = []
        all_income_curve = []
        all_household_scatter = []
        all_constituency = []
        all_demographic = []

        scenario = self.reform.to_scenario()

        for year in self.config.years:
            # Distributional (also returns dataframe for other calcs)
            distributional, decile_df = self.distributional_calc.calculate(
                baseline, reformed, reform_id, reform_name, year
            )
            all_distributional.extend(distributional)

            # Winners/losers
            winners_losers = self.winners_losers_calc.calculate(
                decile_df, reform_id, reform_name, year
            )
            all_winners_losers.extend(winners_losers)

            # Summary metrics
            metrics = self.metrics_calc.calculate(
                baseline, reformed, reform_id, reform_name, year
            )
            all_metrics.extend(metrics)

            # Income curve
            income_curve = self.income_curve_calc.calculate(
                scenario, reform_id, reform_name, year
            )
            all_income_curve.extend(income_curve)

            # Household scatter (sampled to ~2k households per reform/year)
            household_scatter = self.household_scatter_calc.calculate(
                baseline, reformed, reform_id, reform_name, year
            )
            all_household_scatter.extend(household_scatter)

            # Constituency impacts (if data available)
            try:
                constituency, demographic = self._calculate_constituency(
                    baseline, reformed, reform_id, year
                )
                all_constituency.extend(constituency)
                all_demographic.extend(demographic)
            except FileNotFoundError:
                pass  # Skip if constituency data not available

        return ReformResult(
            reform_id=reform_id,
            reform_name=reform_name,
            budgetary_impact=budgetary,
            distributional_impact=all_distributional,
            winners_losers=all_winners_losers,
            metrics=all_metrics,
            income_curve=all_income_curve,
            household_scatter=all_household_scatter,
            constituency=all_constituency,
            demographic_constituency=all_demographic,
        )

    def _calculate_constituency(
        self,
        baseline: Microsimulation,
        reformed: Microsimulation,
        reform_id: str,
        year: int,
    ) -> tuple[list[dict], list[dict]]:
        """Calculate constituency-level impacts."""
        weights_path = self.config.data_dir / (
            "parliamentary_constituency_weights.h5"
        )
        constituencies_path = (
            self.config.data_inputs_dir / "constituencies_2024.csv"
        )

        if not weights_path.exists() or not constituencies_path.exists():
            raise FileNotFoundError("Constituency data not found")

        with h5py.File(weights_path, "r") as f:
            weights = f["2025"][...]

        constituency_df = pd.read_csv(constituencies_path)

        constituency = self.constituency_calc.calculate(
            baseline, reformed, reform_id, year, weights, constituency_df
        )

        demographic = self.demographic_calc.calculate(
            baseline, reformed, reform_id, year, weights, constituency_df
        )

        return constituency, demographic


class DataPipeline:
    """Main pipeline for generating all dashboard data."""

    def __init__(
        self,
        reforms: Optional[list[Reform]] = None,
        config: Optional[DataConfig] = None,
    ):
        """Initialize the pipeline.

        Args:
            reforms: List of reforms to process. Defaults to Autumn Budget.
            config: Data configuration. Uses defaults if not provided.
        """
        self.reforms = reforms or get_autumn_budget_2025_reforms()
        self.config = config or DataConfig()

    def run(self, skip_input_check: bool = False) -> dict[str, pd.DataFrame]:
        """Run the pipeline and generate all data.

        Args:
            skip_input_check: Skip checking for input files.

        Returns:
            Dict mapping output name to DataFrame.
        """
        if not skip_input_check:
            check_input_data(self.config)

        results = []

        # Load dataset
        if self.config.dataset_path:
            dataset = UKSingleYearDataset(
                file_path=str(self.config.dataset_path)
            )
        else:
            dataset = None  # Use default

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            for reform in self.reforms:
                task = progress.add_task(
                    f"Processing {reform.name}...", total=None
                )

                # Create simulations
                # Baseline priority: reform-specific > global config > default
                baseline_scenario = (
                    reform.to_baseline_scenario()
                    or self.config.get_baseline_scenario()
                )
                reform_scenario = reform.to_scenario()

                if dataset:
                    if baseline_scenario:
                        baseline = Microsimulation(
                            dataset=dataset, scenario=baseline_scenario
                        )
                    else:
                        baseline = Microsimulation(dataset=dataset)
                    reformed = Microsimulation(
                        dataset=dataset, scenario=reform_scenario
                    )
                else:
                    if baseline_scenario:
                        baseline = Microsimulation(scenario=baseline_scenario)
                    else:
                        baseline = Microsimulation()
                    reformed = Microsimulation(scenario=reform_scenario)

                # Process reform
                processor = ReformProcessor(reform, self.config)
                result = processor.process(baseline, reformed)
                results.append(result)

                progress.remove_task(task)
                console.print(f"[green]✓[/green] {reform.name}")

        # Aggregate and save
        aggregated = aggregate_results(results, config=self.config)
        self._save_all(aggregated)

        return aggregated

    def _save_all(self, data: dict[str, pd.DataFrame]) -> None:
        """Save all DataFrames to CSV files, merging with existing data."""
        output_dir = self.config.output_dir

        # Define file mappings with their key columns for merging
        file_mapping = {
            "budgetary_impact": (
                "budgetary_impact.csv",
                ["reform_id", "year"],
            ),
            "distributional_impact": (
                "distributional_impact.csv",
                ["reform_id", "year", "decile"],
            ),
            "winners_losers": (
                "winners_losers.csv",
                ["reform_id", "year"],
            ),
            "metrics": (
                "metrics.csv",
                ["reform_id", "year"],
            ),
            "income_curve": (
                "income_curve.csv",
                ["reform_id", "year", "employment_income"],
            ),
            "household_scatter": (
                "household_scatter_full.csv",
                ["reform_id", "year"],
            ),
            "constituency": (
                "constituency.csv",
                ["reform_id", "year", "constituency_code"],
            ),
            "demographic_constituency": (
                "demographic_constituency.csv",
                ["reform_id", "year", "constituency_code"],
            ),
            "obr_comparison": (
                "obr_comparison.csv",
                ["reform_id", "year"],
            ),
        }

        for key, (filename, key_cols) in file_mapping.items():
            if key in data and len(data[key]) > 0:
                csv_path = output_dir / filename
                merged_df = merge_with_existing(data[key], csv_path, key_cols)
                save_csv(merged_df, csv_path)

        # Save metadata with version info
        metadata = {
            "policyengine_uk_version": get_version("policyengine-uk"),
            "generated_at": datetime.now().isoformat(),
        }
        metadata_path = output_dir / "metadata.json"
        metadata_path.parent.mkdir(parents=True, exist_ok=True)
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)

        console.print(f"[green]Saved results to {output_dir}/[/green]")


def aggregate_results(
    results: list[ReformResult],
    config: "DataConfig" = None,
) -> dict[str, pd.DataFrame]:
    """Aggregate results from multiple reforms into DataFrames.

    Args:
        results: List of ReformResult objects.
        config: Data configuration (for OBR estimates path).

    Returns:
        Dict mapping metric name to combined DataFrame.
    """
    aggregated = {
        "budgetary_impact": pd.DataFrame(),
        "distributional_impact": pd.DataFrame(),
        "winners_losers": pd.DataFrame(),
        "metrics": pd.DataFrame(),
        "income_curve": pd.DataFrame(),
        "household_scatter": pd.DataFrame(),
        "constituency": pd.DataFrame(),
        "demographic_constituency": pd.DataFrame(),
        "obr_comparison": pd.DataFrame(),
    }

    for result in results:
        if result.budgetary_impact:
            aggregated["budgetary_impact"] = pd.concat(
                [
                    aggregated["budgetary_impact"],
                    pd.DataFrame(result.budgetary_impact),
                ],
                ignore_index=True,
            )

        if result.distributional_impact:
            aggregated["distributional_impact"] = pd.concat(
                [
                    aggregated["distributional_impact"],
                    pd.DataFrame(result.distributional_impact),
                ],
                ignore_index=True,
            )

        if result.winners_losers:
            aggregated["winners_losers"] = pd.concat(
                [
                    aggregated["winners_losers"],
                    pd.DataFrame(result.winners_losers),
                ],
                ignore_index=True,
            )

        if result.metrics:
            aggregated["metrics"] = pd.concat(
                [
                    aggregated["metrics"],
                    pd.DataFrame(result.metrics),
                ],
                ignore_index=True,
            )

        if result.income_curve:
            aggregated["income_curve"] = pd.concat(
                [
                    aggregated["income_curve"],
                    pd.DataFrame(result.income_curve),
                ],
                ignore_index=True,
            )

        if result.household_scatter:
            aggregated["household_scatter"] = pd.concat(
                [
                    aggregated["household_scatter"],
                    pd.DataFrame(result.household_scatter),
                ],
                ignore_index=True,
            )

        if result.constituency:
            aggregated["constituency"] = pd.concat(
                [
                    aggregated["constituency"],
                    pd.DataFrame(result.constituency),
                ],
                ignore_index=True,
            )

        if result.demographic_constituency:
            aggregated["demographic_constituency"] = pd.concat(
                [
                    aggregated["demographic_constituency"],
                    pd.DataFrame(result.demographic_constituency),
                ],
                ignore_index=True,
            )

    # Generate OBR comparison by merging budgetary impact with OBR estimates
    if config and len(aggregated["budgetary_impact"]) > 0:
        obr_path = config.data_inputs_dir / "obr_estimates.csv"
        if obr_path.exists():
            obr_df = pd.read_csv(obr_path)
            pe_df = aggregated["budgetary_impact"].copy()
            pe_df = pe_df.rename(columns={"value": "policyengine_value"})
            # Check if OBR data has both static and behavioural columns
            obr_cols = ["reform_id", "year"]
            if "obr_static_value" in obr_df.columns:
                obr_cols.append("obr_static_value")
            if "obr_post_behavioural_value" in obr_df.columns:
                obr_cols.append("obr_post_behavioural_value")
            if "obr_value" in obr_df.columns:
                obr_cols.append("obr_value")
            comparison = pd.merge(
                pe_df,
                obr_df[obr_cols],
                on=["reform_id", "year"],
                how="left",
            )
            aggregated["obr_comparison"] = comparison

    return aggregated


def generate_all_data(
    reforms: Optional[list[Reform]] = None,
    config: Optional[DataConfig] = None,
    skip_input_check: bool = False,
) -> dict[str, pd.DataFrame]:
    """Generate all dashboard data for the given reforms.

    This is the main entry point for data generation.

    Args:
        reforms: List of reforms to process. Defaults to Autumn Budget 2025.
        config: Data configuration. Uses defaults if not provided.
        skip_input_check: Skip checking for input files.

    Returns:
        Dict mapping output name to DataFrame.
    """
    pipeline = DataPipeline(reforms=reforms, config=config)
    return pipeline.run(skip_input_check=skip_input_check)
