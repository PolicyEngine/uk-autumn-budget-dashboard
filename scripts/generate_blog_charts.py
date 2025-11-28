"""Generate Plotly JSON charts for blog posts from dashboard data.

This script reads the dashboard CSV outputs and generates Plotly JSON files
that can be directly embedded in policyengine-app-v2 blog posts.

Usage:
    python scripts/generate_blog_charts.py [reform_id] [--year YEAR]

Examples:
    python scripts/generate_blog_charts.py freeze_student_loan_thresholds
    python scripts/generate_blog_charts.py fuel_duty_freeze --year 2027
"""

import argparse
import json
from pathlib import Path

import pandas as pd

# PolicyEngine app-v2 design system
# See: policyengine-app-v2/app/src/designTokens/colors.ts
COLORS = {
    # Primary teal palette
    "primary": "#319795",      # Teal-500 (main)
    "primary_light": "#4FD1C5",  # Teal-300
    "primary_dark": "#285E61",   # Teal-700
    # Gray palette
    "gray_light": "#9CA3AF",   # Gray-400
    "gray": "#6B7280",         # Gray-500
    "gray_dark": "#344054",    # Gray-700
    # Semantic
    "success": "#22C55E",
    "error": "#EF4444",
    # UI
    "neutral": "#F2F4F7",      # Gray-100
    "background": "#FFFFFF",
    "text": "#000000",
}

# Inter is PolicyEngine's official font
FONT_FAMILY = "Inter, sans-serif"


def create_distributional_chart(
    df: pd.DataFrame, reform_id: str, year: int
) -> dict:
    """Create a distributional impact bar chart.

    Args:
        df: DataFrame with distributional_impact.csv data
        reform_id: The reform ID to filter for
        year: The year to show

    Returns:
        Plotly JSON chart specification
    """
    reform_data = df[
        (df["reform_id"] == reform_id) & (df["year"] == year)
    ].copy()

    if reform_data.empty:
        raise ValueError(f"No data found for {reform_id} in {year}")

    # Sort by decile order
    decile_order = [f"{i}{'st' if i == 1 else 'nd' if i == 2 else 'rd' if i == 3 else 'th'}"
                    for i in range(1, 11)]
    reform_data["decile_num"] = reform_data["decile"].apply(
        lambda x: decile_order.index(x) + 1 if x in decile_order else 0
    )
    reform_data = reform_data.sort_values("decile_num")

    values = reform_data["value"].tolist()
    # Convert to percentage (values are already in percentage points)
    values_pct = [v / 100 for v in values]

    # Create text labels
    text_labels = [f"{v:+.2%}" for v in values_pct]

    return {
        "data": [
            {
                "x": ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"],
                "y": values_pct,
                "type": "bar",
                "marker": {
                    "color": COLORS["primary"],
                    "line": {"width": 0}
                },
                "hovertemplate": "Decile %{x}<br>Change: %{y:.2%}<extra></extra>",
                "text": text_labels,
                "textposition": "outside",
                "textfont": {
                    "family": FONT_FAMILY,
                    "size": 14,
                    "color": COLORS["text"]
                }
            }
        ],
        "layout": {
            "xaxis": {
                "title": {
                    "text": "Income decile",
                    "font": {"family": FONT_FAMILY, "size": 14}
                },
                "tickfont": {"family": FONT_FAMILY},
                "showgrid": True,
                "gridcolor": "#e0e0e0",
                "gridwidth": 1,
                "tickmode": "linear",
                "tick0": 1,
                "dtick": 1
            },
            "yaxis": {
                "title": {
                    "text": "Relative change in net income",
                    "font": {"family": FONT_FAMILY, "size": 14}
                },
                "tickfont": {"family": FONT_FAMILY},
                "tickformat": ".2%",
                "showgrid": True,
                "gridcolor": "#e0e0e0",
                "gridwidth": 1,
                "zeroline": True,
                "zerolinecolor": "#333",
                "zerolinewidth": 2
            },
            "height": 500,
            "margin": {"l": 100, "r": 40, "b": 80, "t": 40, "pad": 4},
            "plot_bgcolor": "white",
            "paper_bgcolor": "white",
            "font": {"family": FONT_FAMILY}
        }
    }


def create_avg_change_chart(
    df: pd.DataFrame, reform_id: str, year: int
) -> dict:
    """Create an average income change by decile bar chart.

    Args:
        df: DataFrame with winners_losers.csv data (has avg_change column)
        reform_id: The reform ID to filter for
        year: The year to show

    Returns:
        Plotly JSON chart specification
    """
    reform_data = df[
        (df["reform_id"] == reform_id) & (df["year"] == year)
    ].copy()

    if reform_data.empty:
        raise ValueError(f"No data found for {reform_id} in {year}")

    # Sort by decile
    reform_data = reform_data.sort_values("decile")

    values = reform_data["avg_change"].tolist()

    # Color bars based on positive/negative
    bar_colors = [
        COLORS["primary"] if v >= 0 else COLORS["error"]
        for v in values
    ]

    # Format text labels
    text_labels = [f"£{v:+,.0f}" for v in values]

    return {
        "data": [
            {
                "x": ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"],
                "y": values,
                "type": "bar",
                "marker": {
                    "color": bar_colors,
                    "line": {"width": 0}
                },
                "hovertemplate": "Decile %{x}<br>Avg change: £%{y:,.0f}<extra></extra>",
                "text": text_labels,
                "textposition": "outside",
                "textfont": {
                    "family": FONT_FAMILY,
                    "size": 12,
                    "color": COLORS["text"]
                }
            }
        ],
        "layout": {
            "xaxis": {
                "title": {
                    "text": "Income decile",
                    "font": {"family": FONT_FAMILY, "size": 14}
                },
                "tickfont": {"family": FONT_FAMILY},
                "showgrid": True,
                "gridcolor": "#e0e0e0",
                "gridwidth": 1
            },
            "yaxis": {
                "title": {
                    "text": "Average change in household income (£/year)",
                    "font": {"family": FONT_FAMILY, "size": 14}
                },
                "tickfont": {"family": FONT_FAMILY},
                "tickprefix": "£",
                "showgrid": True,
                "gridcolor": "#e0e0e0",
                "gridwidth": 1,
                "zeroline": True,
                "zerolinecolor": COLORS["gray_dark"],
                "zerolinewidth": 2
            },
            "height": 500,
            "margin": {"l": 100, "r": 40, "b": 80, "t": 40, "pad": 4},
            "plot_bgcolor": COLORS["background"],
            "paper_bgcolor": COLORS["background"],
            "font": {"family": FONT_FAMILY}
        }
    }


def create_revenue_table_data(
    df: pd.DataFrame, reform_id: str, obr_df: pd.DataFrame = None
) -> dict:
    """Create revenue comparison table data.

    Args:
        df: DataFrame with budgetary_impact.csv data
        reform_id: The reform ID to filter for
        obr_df: Optional DataFrame with OBR estimates

    Returns:
        Dict with table data for markdown
    """
    reform_data = df[df["reform_id"] == reform_id].copy()

    if reform_data.empty:
        raise ValueError(f"No data found for {reform_id}")

    reform_data = reform_data.sort_values("year")

    result = {
        "years": reform_data["year"].tolist(),
        "policyengine": reform_data["value"].tolist(),
    }

    if obr_df is not None:
        obr_data = obr_df[obr_df["reform_id"] == reform_id]
        if not obr_data.empty:
            obr_data = obr_data.sort_values("year")
            result["obr_static"] = obr_data["obr_static_value"].tolist()
            result["obr_behavioural"] = obr_data["obr_post_behavioural_value"].tolist()

    return result


def main():
    parser = argparse.ArgumentParser(
        description="Generate Plotly JSON charts for blog posts"
    )
    parser.add_argument(
        "reform_id",
        help="Reform ID to generate charts for"
    )
    parser.add_argument(
        "--year",
        type=int,
        default=2027,
        help="Year for distributional charts (default: 2027)"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("public/data/blog_charts"),
        help="Output directory for JSON files"
    )

    args = parser.parse_args()

    # Read data
    data_dir = Path("public/data")

    distributional_df = pd.read_csv(data_dir / "distributional_impact.csv")
    winners_losers_df = pd.read_csv(data_dir / "winners_losers.csv")
    budgetary_df = pd.read_csv(data_dir / "budgetary_impact.csv")

    obr_path = Path("data_inputs/obr_estimates.csv")
    obr_df = pd.read_csv(obr_path) if obr_path.exists() else None

    # Create output directory
    output_dir = args.output_dir / args.reform_id
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate charts
    print(f"Generating charts for {args.reform_id} (year {args.year})...")

    try:
        dist_chart = create_distributional_chart(
            distributional_df, args.reform_id, args.year
        )
        with open(output_dir / f"distributional_{args.year}.json", "w") as f:
            json.dump(dist_chart, f, indent=2)
        print(f"  ✓ Distributional chart: {output_dir}/distributional_{args.year}.json")
    except ValueError as e:
        print(f"  ✗ Distributional chart: {e}")

    try:
        avg_chart = create_avg_change_chart(
            winners_losers_df, args.reform_id, args.year
        )
        with open(output_dir / f"avg_change_{args.year}.json", "w") as f:
            json.dump(avg_chart, f, indent=2)
        print(f"  ✓ Avg change chart: {output_dir}/avg_change_{args.year}.json")
    except ValueError as e:
        print(f"  ✗ Avg change chart: {e}")

    try:
        revenue_data = create_revenue_table_data(
            budgetary_df, args.reform_id, obr_df
        )
        with open(output_dir / "revenue.json", "w") as f:
            json.dump(revenue_data, f, indent=2)
        print(f"  ✓ Revenue data: {output_dir}/revenue.json")
    except ValueError as e:
        print(f"  ✗ Revenue data: {e}")

    print(f"\nCharts saved to {output_dir}/")
    print("\nTo embed in a blog post, copy the JSON content into a ```plotly code block.")


if __name__ == "__main__":
    main()
