#!/usr/bin/env python
"""Sample household scatter data for git storage.

The full household_scatter_full.csv (~100MB) contains all ~46k households
per reform/year. This script samples it to ~2k households using weighted
sampling to create household_scatter.csv (~5MB) for git.

Usage:
    python scripts/sample_household_scatter.py
"""

import pandas as pd
import numpy as np
from pathlib import Path

SAMPLE_SIZE = 2000  # Households per reform per year
SEED = 42  # For reproducibility


def sample_scatter_data(
    input_path: Path,
    output_path: Path,
    sample_size: int = SAMPLE_SIZE,
) -> None:
    """Sample household scatter data using weighted sampling.

    Args:
        input_path: Path to full household_scatter_full.csv
        output_path: Path to write sampled household_scatter.csv
        sample_size: Number of households to sample per reform/year
    """
    print(f"Reading {input_path}...")
    df = pd.read_csv(input_path)
    print(f"  {len(df):,} rows")

    # Sample within each reform/year group
    rng = np.random.default_rng(seed=SEED)
    sampled_dfs = []

    for (reform_id, year), group in df.groupby(["reform_id", "year"]):
        if len(group) <= sample_size:
            sampled_dfs.append(group)
        else:
            # Weighted sampling - higher weight = higher chance
            weights = group["household_weight"].values
            probs = weights / weights.sum()

            indices = rng.choice(
                len(group),
                size=sample_size,
                replace=False,
                p=probs,
            )
            sampled_dfs.append(group.iloc[indices])

    result = pd.concat(sampled_dfs, ignore_index=True)

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
