#!/usr/bin/env python
"""Sample household scatter data for git storage.

The full household_scatter_full.csv (~100MB) contains all ~46k households
per reform/year. This script samples it to ~500 households using weighted
sampling to create household_scatter.csv for git.

IMPORTANT: We sample the SAME households across all reforms so that when
combining policies in the frontend, the dots represent consistent households
that just move position (not shuffle randomly).

Usage:
    python scripts/sample_household_scatter.py
"""

import pandas as pd
import numpy as np
from pathlib import Path

SAMPLE_SIZE = 500  # Households per year (same across all reforms)
SEED = 42  # For reproducibility


def sample_scatter_data(
    input_path: Path,
    output_path: Path,
    sample_size: int = SAMPLE_SIZE,
) -> None:
    """Sample household scatter data using weighted sampling.

    Samples the SAME households across all reforms for consistency.
    Uses baseline_income + household_weight as a unique household identifier.

    Args:
        input_path: Path to full household_scatter_full.csv
        output_path: Path to write sampled household_scatter.csv
        sample_size: Number of households to sample per year
    """
    print(f"Reading {input_path}...")
    df = pd.read_csv(input_path)
    print(f"  {len(df):,} rows")

    # Create a unique household identifier using baseline_income + household_weight
    # These should be unique per household in the FRS microdata
    df["household_id"] = (
        df["baseline_income"].astype(str) + "_" + df["household_weight"].astype(str)
    )

    rng = np.random.default_rng(seed=SEED)
    sampled_dfs = []

    # Sample households INDEPENDENTLY per reform/year to capture affected populations
    # But use consistent household_id so frontend can match if household exists in multiple reforms
    for (reform_id, year), group in df.groupby(["reform_id", "year"]):
        n_households = len(group)

        if n_households <= sample_size:
            sampled_dfs.append(group)
            print(f"  {reform_id}/{year}: kept all {n_households} households")
        else:
            # Weighted sampling - higher weight = higher chance
            weights = group["household_weight"].values
            probs = weights / weights.sum()

            indices = rng.choice(
                n_households,
                size=sample_size,
                replace=False,
                p=probs,
            )
            sampled_dfs.append(group.iloc[indices])
            print(f"  {reform_id}/{year}: sampled {sample_size} from {n_households}")

    result = pd.concat(sampled_dfs, ignore_index=True)

    # Keep household_id in output so frontend can match across reforms
    # Sort by reform_id, year, household_id for consistent ordering
    result = result.sort_values(
        ["reform_id", "year", "household_id"]
    ).reset_index(drop=True)

    print(f"Writing {output_path}...")
    print(f"  {len(result):,} rows (sampled from {len(df):,})")
    result.to_csv(output_path, index=False)

    # Show size comparison
    input_size = input_path.stat().st_size / 1e6
    output_size = output_path.stat().st_size / 1e6
    print(f"  Size: {input_size:.1f}MB -> {output_size:.1f}MB")


def main():
    data_dir = Path("public/data")
    input_path = data_dir / "household_scatter_full.csv"
    output_path = data_dir / "household_scatter.csv"

    if not input_path.exists():
        print(f"Error: {input_path} not found")
        print("Run 'uv run uk-budget-data' first to generate full data")
        return 1

    sample_scatter_data(input_path, output_path)
    print("Done!")
    return 0


if __name__ == "__main__":
    exit(main())
