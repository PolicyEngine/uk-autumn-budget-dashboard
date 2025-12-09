"""Generate embeddable HTML charts for the combined Autumn Budget 2025 reforms blog post.

This script generates standalone HTML files that exactly replicate the charts from the
uk-combined-reforms-autumn-budget-2025.md blog post, suitable for iframing.

Charts:
1. Distributional impact (£/year by decile) - vertical bar with year slider
2. Winners/losers (% population in each category by decile) - horizontal stacked bar
3. Constituency map (average £/year by constituency) - D3.js choropleth
4. Poverty impact (pp change by demographic) - vertical bar with year slider

Data is hardcoded from the blog post analysis (from Vahid's gist calculations).

Usage:
    uv run python scripts/generate_combined_charts.py

Output:
    public/combined_reforms/*.html files for iframing
"""

import json
from pathlib import Path

# PolicyEngine design system colors (from app-v2/designTokens/colors.ts)
COLORS = {
    "primary": "#2C6496",  # Blue used in blog post charts
    "primary_light": "#C5D3E8",  # Light blue for gain <5%
    "neutral": "#F0F0F0",  # No change
    "error_light": "#FACBCB",  # Lose <5%
    "error": "#B71C1C",  # Lose >5%
    "gray": "#616161",  # Negative values
    "background": "#FFFFFF",
    "text": "#333333",
}

YEAR_LABELS = ["2026-27", "2027-28", "2028-29", "2029-30", "2030-31"]

# ============================================================================
# DATA FROM BLOG POST (extracted from plotly JSON)
# ============================================================================

# Figure 1: Distributional impact data (£/year by decile)
DISTRIBUTIONAL_DATA = {
    "2026-27": [669.91, 1139.47, 440.08, 363.70, 211.78, 152.68, 140.49, 183.43, 164.73, 169.94],
    "2027-28": [655.31, 1155.52, 441.83, 309.15, 146.06, 91.15, 54.48, 72.93, 56.04, 59.78],
    "2028-29": [458.42, 1446.00, 338.39, 283.08, 39.22, -36.66, -156.03, -179.41, -290.87, -504.81],
    "2029-30": [441.86, 1434.73, 176.43, 216.17, -180.77, -231.89, -416.12, -526.88, -1028.16, -1448.99],
    "2030-31": [466.71, 1343.23, 235.79, 58.70, -201.97, -350.20, -576.17, -766.52, -1327.66, -1873.95],
}

# Figure 2: Winners/losers data (% by category for each decile + All)
# Order: ["All", " ", "10", "9", "8", "7", "6", "5", "4", "3", "2", "1"]
WINNERS_LOSERS_DATA = {
    "2026-27": {
        "gain_more_5": [8.76, None, 4.21, 5.82, 4.86, 3.83, 5.66, 5.66, 11.15, 10.45, 22.95, 13.35],
        "gain_less_5": [43.68, None, 42.60, 47.48, 53.58, 50.19, 49.12, 50.85, 38.88, 36.49, 33.49, 33.45],
        "no_change": [47.55, None, 53.19, 46.70, 41.56, 45.98, 45.22, 43.49, 49.98, 53.06, 43.56, 53.20],
        "lose_less_5": [0.00, None, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00],
        "lose_more_5": [0.00, None, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00],
    },
    "2027-28": {
        "gain_more_5": [8.26, None, 3.74, 5.45, 4.74, 3.28, 5.04, 5.83, 9.98, 10.65, 22.07, 12.12],
        "gain_less_5": [42.50, None, 41.25, 44.35, 51.01, 46.65, 47.80, 47.69, 40.99, 35.67, 34.00, 35.06],
        "no_change": [45.49, None, 49.55, 41.30, 36.29, 43.56, 41.75, 44.85, 48.33, 53.28, 43.75, 52.83],
        "lose_less_5": [3.73, None, 5.46, 8.83, 7.95, 6.50, 5.41, 1.64, 0.63, 0.39, 0.18, 0.00],
        "lose_more_5": [0.02, None, 0.00, 0.07, 0.00, 0.00, 0.00, 0.00, 0.08, 0.00, 0.01, 0.00],
    },
    "2028-29": {
        "gain_more_5": [6.66, None, 1.81, 0.89, 2.84, 2.17, 3.18, 4.89, 8.53, 8.43, 24.28, 10.24],
        "gain_less_5": [12.83, None, 2.77, 3.32, 9.15, 10.94, 12.31, 13.29, 16.86, 13.73, 22.07, 24.93],
        "no_change": [8.71, None, 0.83, 0.38, 1.51, 2.92, 4.36, 5.64, 7.02, 11.36, 14.63, 40.71],
        "lose_less_5": [69.76, None, 91.94, 90.77, 84.66, 81.87, 78.35, 75.30, 64.66, 64.96, 37.87, 23.38],
        "lose_more_5": [2.03, None, 2.64, 4.64, 1.83, 2.10, 1.80, 0.88, 2.92, 1.52, 1.15, 0.74],
    },
    "2029-30": {
        "gain_more_5": [4.68, None, 0.00, 0.01, 0.16, 0.17, 0.65, 1.39, 7.08, 6.95, 22.24, 8.93],
        "gain_less_5": [6.35, None, 0.16, 0.20, 2.87, 2.66, 6.89, 3.17, 7.41, 5.79, 13.18, 22.42],
        "no_change": [7.11, None, 0.31, 0.14, 0.93, 1.03, 3.76, 3.84, 5.82, 8.59, 12.06, 36.57],
        "lose_less_5": [77.09, None, 93.44, 91.74, 90.56, 91.84, 83.98, 87.21, 74.06, 75.09, 48.97, 30.10],
        "lose_more_5": [4.78, None, 6.09, 7.90, 5.47, 4.29, 4.72, 4.39, 5.63, 3.57, 3.55, 1.97],
    },
    "2030-31": {
        "gain_more_5": [4.71, None, 0.00, 0.01, 0.09, 0.15, 0.48, 2.52, 5.36, 8.64, 20.86, 9.85],
        "gain_less_5": [6.32, None, 0.16, 0.26, 3.04, 2.94, 6.44, 2.83, 6.82, 5.95, 13.27, 22.78],
        "no_change": [6.82, None, 0.32, 0.14, 0.98, 1.04, 3.77, 4.22, 3.65, 8.31, 11.31, 36.37],
        "lose_less_5": [76.68, None, 91.18, 90.93, 89.29, 91.32, 84.16, 85.14, 78.16, 73.36, 50.40, 29.04],
        "lose_more_5": [5.47, None, 8.34, 8.66, 6.59, 4.56, 5.15, 5.29, 6.01, 3.74, 4.16, 1.95],
    },
}

# Figure 4: Poverty impact data (pp change by demographic)
# Order: ["Overall (BHC)", "Overall (AHC)", "Child (BHC)", "Child (AHC)", "Working-age (BHC)", "Pensioner (BHC)"]
POVERTY_DATA = {
    "2026-27": [-0.69, -1.02, -2.30, -3.51, -0.34, 0.00],
    "2027-28": [-0.69, -1.05, -2.31, -3.59, -0.33, 0.00],
    "2028-29": [-0.74, -0.99, -2.50, -3.46, -0.37, 0.08],
    "2029-30": [-0.73, -0.94, -2.47, -3.35, -0.36, 0.05],
    "2030-31": [-0.81, -1.02, -2.88, -3.77, -0.37, 0.14],
}

POVERTY_LABELS = [
    "Overall<br>(BHC)",
    "Overall<br>(AHC)",
    "Child<br>(BHC)",
    "Child<br>(AHC)",
    "Working-age<br>(BHC)",
    "Pensioner<br>(BHC)",
]


def create_distributional_html(output_path: Path) -> None:
    """Create Figure 1: Distributional impact chart (£/year by decile) with year slider."""

    html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Distributional Impact - Combined Autumn Budget 2025</title>
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Roboto+Serif:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        body {{ margin: 0; padding: 16px; font-family: 'Roboto Serif', serif; background: white; }}
        #chart {{ width: 100%; height: 500px; }}
    </style>
</head>
<body>
    <div id="chart"></div>
    <script>
        const data = {json.dumps(DISTRIBUTIONAL_DATA)};
        const years = {json.dumps(YEAR_LABELS)};

        const traces = years.map((year, i) => {{
            const values = data[year];
            const colors = values.map(v => v >= 0 ? '{COLORS["primary"]}' : '{COLORS["gray"]}');
            return {{
                x: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                y: values,
                type: 'bar',
                marker: {{ color: colors }},
                text: values.map(v => v >= 0 ? '£' + v.toFixed(2) : '-£' + Math.abs(v).toFixed(2)),
                textposition: 'outside',
                textfont: {{ family: 'Roboto Serif', size: 10 }},
                hovertemplate: 'Decile %{{x}}<br>Change: £%{{y:,.2f}}<extra></extra>',
                visible: i === 0,
                name: year
            }};
        }});

        const steps = years.map((year, i) => ({{
            method: 'update',
            args: [{{ visible: years.map((_, j) => j === i) }}],
            label: year
        }}));

        const layout = {{
            xaxis: {{
                title: 'Income decile',
                tickmode: 'array',
                tickvals: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                showgrid: true,
                gridcolor: '#e0e0e0'
            }},
            yaxis: {{
                title: 'Average change in household income (£/year)',
                tickprefix: '£',
                showgrid: true,
                gridcolor: '#e0e0e0',
                range: [-2200, 1600],
                zeroline: true,
                zerolinecolor: '#333',
                zerolinewidth: 2
            }},
            height: 500,
            margin: {{ l: 80, r: 50, b: 100, t: 60 }},
            font: {{ family: 'Roboto Serif' }},
            showlegend: false,
            sliders: [{{
                active: 0,
                steps: steps,
                x: 0.2,
                len: 0.6,
                y: 1.1,
                currentvalue: {{ visible: false }},
                font: {{ family: 'Roboto Serif' }}
            }}],
            updatemenus: [{{
                type: 'buttons',
                showactive: false,
                x: 0.1,
                y: 1.15,
                xanchor: 'right',
                buttons: [{{
                    label: 'Play',
                    method: 'animate',
                    args: [null, {{ frame: {{ duration: 1000, redraw: true }}, fromcurrent: true, mode: 'afterall' }}]
                }}]
            }}]
        }};

        // Create frames for animation
        const frames = years.map(year => ({{
            name: year,
            data: [{{
                y: data[year],
                text: data[year].map(v => v >= 0 ? '£' + v.toFixed(2) : '-£' + Math.abs(v).toFixed(2)),
                marker: {{ color: data[year].map(v => v >= 0 ? '{COLORS["primary"]}' : '{COLORS["gray"]}') }}
            }}]
        }}));

        Plotly.newPlot('chart', traces, layout).then(() => {{
            Plotly.addFrames('chart', frames);
        }});
    </script>
</body>
</html>'''

    output_path.write_text(html_content)
    print(f"  + Saved: {output_path}")


def create_winners_losers_html(output_path: Path) -> None:
    """Create Figure 2: Winners/losers horizontal stacked bar chart with year slider."""

    y_labels = ["All", " ", "10", "9", "8", "7", "6", "5", "4", "3", "2", "1"]

    html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Winners and Losers - Combined Autumn Budget 2025</title>
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Roboto+Serif:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        body {{ margin: 0; padding: 16px; font-family: 'Roboto Serif', serif; background: white; }}
        #chart {{ width: 100%; height: 650px; }}
    </style>
</head>
<body>
    <div id="chart"></div>
    <script>
        const data = {json.dumps(WINNERS_LOSERS_DATA)};
        const years = {json.dumps(YEAR_LABELS)};
        const yLabels = {json.dumps(y_labels)};

        const categories = [
            {{ key: 'gain_more_5', name: 'Gain more than 5%', color: '{COLORS["primary"]}', textColor: 'white' }},
            {{ key: 'gain_less_5', name: 'Gain less than 5%', color: '{COLORS["primary_light"]}', textColor: '#333' }},
            {{ key: 'no_change', name: 'No change', color: '{COLORS["neutral"]}', textColor: '#333' }},
            {{ key: 'lose_less_5', name: 'Lose less than 5%', color: '{COLORS["error_light"]}', textColor: '#333' }},
            {{ key: 'lose_more_5', name: 'Lose more than 5%', color: '{COLORS["error"]}', textColor: 'white' }}
        ];

        // Create initial traces for 2026-27
        const initialYear = years[0];
        const traces = categories.map(cat => {{
            const values = data[initialYear][cat.key];
            return {{
                name: cat.name,
                type: 'bar',
                orientation: 'h',
                x: values,
                y: yLabels,
                marker: {{ color: cat.color }},
                text: values.map(v => v !== null && v > 0.5 ? v.toFixed(2) + '%' : ''),
                textposition: 'inside',
                textfont: {{ color: cat.textColor, size: 11 }},
                hovertemplate: '%{{y}}<br>' + cat.name + ': %{{x:.2f}}%<extra></extra>',
                showlegend: true
            }};
        }});

        const steps = years.map((year, i) => ({{
            method: 'animate',
            args: [[year], {{ frame: {{ duration: 800, redraw: true }}, mode: 'immediate' }}],
            label: year
        }}));

        const layout = {{
            barmode: 'stack',
            xaxis: {{
                title: {{ text: 'Population share', font: {{ family: 'Roboto Serif', size: 14 }} }},
                tickfont: {{ family: 'Roboto Serif', size: 12 }},
                showgrid: true,
                gridcolor: '#e0e0e0',
                range: [0, 100],
                tickformat: '.0f',
                ticksuffix: '%'
            }},
            yaxis: {{
                title: {{ text: 'Income decile', font: {{ family: 'Roboto Serif', size: 14 }} }},
                tickfont: {{ family: 'Roboto Serif', size: 12 }},
                categoryorder: 'array',
                categoryarray: ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', ' ', 'All'],
                type: 'category',
                automargin: true
            }},
            height: 650,
            margin: {{ l: 80, r: 50, b: 120, t: 60 }},
            plot_bgcolor: 'white',
            paper_bgcolor: 'white',
            font: {{ family: 'Roboto Serif' }},
            legend: {{
                orientation: 'h',
                yanchor: 'top',
                y: -0.12,
                xanchor: 'center',
                x: 0.5,
                font: {{ family: 'Roboto Serif', size: 10 }},
                traceorder: 'normal',
                entrywidth: 100
            }},
            sliders: [{{
                active: 0,
                yanchor: 'middle',
                xanchor: 'center',
                currentvalue: {{ visible: false }},
                transition: {{ duration: 800 }},
                pad: {{ b: 10, t: 50, l: 80 }},
                len: 0.7,
                x: 0.45,
                y: 1.15,
                steps: steps
            }}],
            updatemenus: [{{
                buttons: [{{
                    args: [null, {{ frame: {{ duration: 1500, redraw: true }}, fromcurrent: true, transition: {{ duration: 800 }} }}],
                    label: 'Play',
                    method: 'animate'
                }}],
                direction: 'left',
                pad: {{ r: 10, t: 10 }},
                showactive: false,
                type: 'buttons',
                x: 0.05,
                xanchor: 'left',
                y: 1.15,
                yanchor: 'middle'
            }}]
        }};

        // Create frames for animation
        const frames = years.map(year => ({{
            name: year,
            data: categories.map(cat => {{
                const values = data[year][cat.key];
                return {{
                    x: values,
                    text: values.map(v => v !== null && v > 0.5 ? v.toFixed(2) + '%' : '')
                }};
            }})
        }}));

        Plotly.newPlot('chart', traces, layout).then(() => {{
            Plotly.addFrames('chart', frames);
        }});
    </script>
</body>
</html>'''

    output_path.write_text(html_content)
    print(f"  + Saved: {output_path}")


def create_poverty_html(output_path: Path) -> None:
    """Create Figure 4: Poverty impact chart (pp change by demographic) with year slider."""

    html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Poverty Impact - Combined Autumn Budget 2025</title>
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Roboto+Serif:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        body {{ margin: 0; padding: 16px; font-family: 'Roboto Serif', serif; background: white; }}
        #chart {{ width: 100%; height: 500px; }}
    </style>
</head>
<body>
    <div id="chart"></div>
    <script>
        const data = {json.dumps(POVERTY_DATA)};
        const years = {json.dumps(YEAR_LABELS)};
        const labels = {json.dumps(POVERTY_LABELS)};

        const traces = years.map((year, i) => {{
            const values = data[year];
            const colors = values.map(v => v < 0 ? '{COLORS["primary"]}' : '{COLORS["gray"]}');
            return {{
                x: labels,
                y: values,
                type: 'bar',
                marker: {{ color: colors }},
                text: values.map(v => (v >= 0 ? '+' : '') + v.toFixed(2) + 'pp'),
                textposition: 'outside',
                textfont: {{ family: 'Roboto Serif', size: 11 }},
                hovertemplate: '%{{x}}<br>Change: %{{y:+.2f}}pp<extra></extra>',
                visible: i === 0,
                name: year
            }};
        }});

        const steps = years.map((year, i) => ({{
            method: 'animate',
            args: [[year], {{ frame: {{ duration: 0, redraw: true }}, mode: 'immediate' }}],
            label: year
        }}));

        const layout = {{
            xaxis: {{
                title: 'Poverty measure',
                tickfont: {{ family: 'Roboto Serif', size: 10 }},
                showgrid: false
            }},
            yaxis: {{
                title: 'Change in poverty headcount rate (pp)',
                ticksuffix: 'pp',
                showgrid: true,
                gridcolor: '#e0e0e0',
                range: [-5, 1],
                zeroline: true,
                zerolinecolor: '#333',
                zerolinewidth: 2
            }},
            height: 500,
            margin: {{ l: 80, r: 50, b: 120, t: 60 }},
            font: {{ family: 'Roboto Serif' }},
            showlegend: false,
            sliders: [{{
                active: 0,
                steps: steps,
                x: 0.2,
                len: 0.6,
                y: 1.1,
                currentvalue: {{ visible: false }},
                font: {{ family: 'Roboto Serif' }}
            }}],
            updatemenus: [{{
                type: 'buttons',
                showactive: false,
                x: 0.1,
                y: 1.15,
                xanchor: 'right',
                buttons: [{{
                    label: 'Play',
                    method: 'animate',
                    args: [null, {{ frame: {{ duration: 1000, redraw: true }}, fromcurrent: true, mode: 'afterall' }}]
                }}]
            }}]
        }};

        // Create frames for animation
        const frames = years.map(year => ({{
            name: year,
            data: [{{
                y: data[year],
                text: data[year].map(v => (v >= 0 ? '+' : '') + v.toFixed(2) + 'pp'),
                marker: {{ color: data[year].map(v => v < 0 ? '{COLORS["primary"]}' : '{COLORS["gray"]}') }}
            }}]
        }}));

        Plotly.newPlot('chart', traces, layout).then(() => {{
            Plotly.addFrames('chart', frames);
        }});
    </script>
</body>
</html>'''

    output_path.write_text(html_content)
    print(f"  + Saved: {output_path}")


def create_constituency_map_html(output_path: Path) -> None:
    """Create Figure 3: Constituency map with D3.js choropleth and year slider.

    Reads constituency data from public/data/constituency.csv.
    """
    import pandas as pd

    # Load constituency data
    constituency_df = pd.read_csv("public/data/constituency.csv")
    reform_data = constituency_df[constituency_df["reform_id"] == "autumn_budget_2025_combined"].copy()

    # Prepare data by year (map constituency code to average gain)
    data_by_year = {}
    for year_label in YEAR_LABELS:
        year = int(year_label.split("-")[0])
        year_data = reform_data[reform_data["year"] == year]
        data_by_year[year_label] = {
            row["constituency_code"]: {
                "name": row["constituency_name"],
                "value": round(row["average_gain"], 2),
            }
            for _, row in year_data.iterrows()
        }

    html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Constituency Map - Combined Autumn Budget 2025</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Roboto+Serif:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        body {{ margin: 0; overflow: hidden; background: white; font-family: 'Roboto Serif', serif; }}
        svg {{ display: block; }}
        .tooltip {{
            position: fixed;
            background: white;
            padding: 10px 14px;
            border-radius: 6px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.15);
            pointer-events: none;
            opacity: 0;
            font-size: 13px;
            z-index: 1001;
        }}
        .tooltip strong {{ display: block; margin-bottom: 4px; }}
        .tooltip .value {{ font-weight: 600; }}
        .gain {{ color: {COLORS["primary"]}; }}
        .loss {{ color: #B71C1C; }}
        .controls {{
            position: absolute;
            top: 10px;
            left: 50%;
            transform: translateX(-50%);
            background: white;
            padding: 12px 20px;
            border-radius: 8px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.15);
            display: flex;
            align-items: center;
            gap: 15px;
            z-index: 1000;
        }}
        .play-btn {{
            width: 36px;
            height: 36px;
            border: none;
            background: {COLORS["primary"]};
            color: white;
            border-radius: 50%;
            cursor: pointer;
            font-size: 14px;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        .year-slider {{
            width: 200px;
            height: 6px;
            -webkit-appearance: none;
            background: #e5e5e5;
            border-radius: 3px;
        }}
        .year-slider::-webkit-slider-thumb {{
            -webkit-appearance: none;
            width: 18px;
            height: 18px;
            background: {COLORS["primary"]};
            border-radius: 50%;
            cursor: pointer;
        }}
        .year-marks {{
            display: flex;
            justify-content: space-between;
            width: 200px;
            font-size: 9px;
            color: #666;
            margin-top: 4px;
        }}
        .legend {{
            position: absolute;
            bottom: 20px;
            right: 20px;
            background: white;
            padding: 10px;
            border-radius: 6px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            font-size: 11px;
        }}
        .legend-bar {{
            width: 150px;
            height: 12px;
            border-radius: 2px;
        }}
        .legend-labels {{
            display: flex;
            justify-content: space-between;
            margin-top: 4px;
        }}
        .zoom-controls {{
            position: absolute;
            bottom: 20px;
            left: 20px;
            display: flex;
            flex-direction: column;
            gap: 5px;
        }}
        .zoom-btn {{
            width: 32px;
            height: 32px;
            border: 1px solid #ccc;
            background: white;
            border-radius: 4px;
            cursor: pointer;
            font-size: 18px;
        }}
    </style>
</head>
<body>
    <div class="controls">
        <button class="play-btn" id="play-btn">&#9654;</button>
        <div>
            <input type="range" class="year-slider" id="year-slider" min="0" max="4" value="0" step="1">
            <div class="year-marks">
                {"".join(f"<span>{y}</span>" for y in YEAR_LABELS)}
            </div>
        </div>
    </div>
    <div class="zoom-controls">
        <button class="zoom-btn" id="zoom-in">+</button>
        <button class="zoom-btn" id="zoom-out">−</button>
        <button class="zoom-btn" id="zoom-reset">⟲</button>
    </div>
    <div class="legend">
        <div class="legend-bar" id="legend-bar"></div>
        <div class="legend-labels">
            <span id="legend-min"></span>
            <span id="legend-max"></span>
        </div>
    </div>
    <svg id="map"></svg>
    <div class="tooltip" id="tooltip"></div>
    <script>
        const dataByYear = {json.dumps(data_by_year)};
        const years = {json.dumps(YEAR_LABELS)};
        let currentYearIndex = 0;
        let isPlaying = false;
        let playInterval;

        const width = window.innerWidth;
        const height = window.innerHeight;

        const svg = d3.select("#map")
            .attr("width", width)
            .attr("height", height);

        const g = svg.append("g");

        const zoom = d3.zoom()
            .scaleExtent([0.5, 8])
            .on("zoom", (event) => g.attr("transform", event.transform));

        svg.call(zoom);

        // Load GeoJSON
        d3.json("../data/uk_constituencies_2024.geojson").then(geojson => {{
            const projection = d3.geoMercator()
                .fitSize([width - 100, height - 150], geojson);

            const path = d3.geoPath().projection(projection);

            function updateMap() {{
                const yearLabel = years[currentYearIndex];
                const yearData = dataByYear[yearLabel] || {{}};

                const values = Object.values(yearData).map(d => d.value).filter(v => !isNaN(v));
                const minVal = Math.min(...values);
                const maxVal = Math.max(...values);

                const colorScale = d3.scaleLinear()
                    .domain([minVal, 0, maxVal])
                    .range(["#B71C1C", "#f5f5f5", "{COLORS["primary"]}"]);

                document.getElementById("legend-min").textContent = "£" + Math.round(minVal);
                document.getElementById("legend-max").textContent = "£" + Math.round(maxVal);
                document.getElementById("legend-bar").style.background =
                    `linear-gradient(to right, #B71C1C, #f5f5f5, {COLORS["primary"]})`;

                const paths = g.selectAll("path")
                    .data(geojson.features, d => d.properties.PCON24CD);

                paths.enter()
                    .append("path")
                    .attr("d", path)
                    .attr("stroke", "#fff")
                    .attr("stroke-width", 0.3)
                    .merge(paths)
                    .attr("fill", d => {{
                        const code = d.properties.PCON24CD;
                        const data = yearData[code];
                        return data ? colorScale(data.value) : "#ccc";
                    }})
                    .on("mouseover", function(event, d) {{
                        const code = d.properties.PCON24CD;
                        const data = yearData[code];
                        if (data) {{
                            const tooltip = document.getElementById("tooltip");
                            const sign = data.value >= 0 ? '+' : '';
                            tooltip.innerHTML = `<strong>${{data.name}}</strong>` +
                                `<span class="${{data.value >= 0 ? 'gain' : 'loss'}} value">` +
                                `£${{sign}}${{data.value.toFixed(0)}}/year</span>`;
                            tooltip.style.opacity = 1;
                            tooltip.style.left = (event.clientX + 15) + "px";
                            tooltip.style.top = (event.clientY + 15) + "px";
                        }}
                        d3.select(this).attr("stroke", "#333").attr("stroke-width", 1.5);
                    }})
                    .on("mouseout", function() {{
                        document.getElementById("tooltip").style.opacity = 0;
                        d3.select(this).attr("stroke", "#fff").attr("stroke-width", 0.3);
                    }});
            }}

            updateMap();

            document.getElementById("year-slider").addEventListener("input", function() {{
                currentYearIndex = parseInt(this.value);
                updateMap();
            }});

            document.getElementById("play-btn").addEventListener("click", function() {{
                if (isPlaying) {{
                    clearInterval(playInterval);
                    this.innerHTML = "&#9654;";
                }} else {{
                    playInterval = setInterval(() => {{
                        currentYearIndex = (currentYearIndex + 1) % years.length;
                        document.getElementById("year-slider").value = currentYearIndex;
                        updateMap();
                    }}, 1500);
                    this.innerHTML = "&#9724;";
                }}
                isPlaying = !isPlaying;
            }});

            document.getElementById("zoom-in").addEventListener("click", () =>
                svg.transition().call(zoom.scaleBy, 1.5));
            document.getElementById("zoom-out").addEventListener("click", () =>
                svg.transition().call(zoom.scaleBy, 0.67));
            document.getElementById("zoom-reset").addEventListener("click", () =>
                svg.transition().call(zoom.transform, d3.zoomIdentity));
        }});
    </script>
</body>
</html>'''

    output_path.write_text(html_content)
    print(f"  + Saved: {output_path}")


def main():
    """Generate all charts for combined reforms blog post."""
    output_dir = Path("public/combined_reforms")
    output_dir.mkdir(parents=True, exist_ok=True)

    print("Generating charts for combined Autumn Budget 2025 reforms...")
    print()

    print("1. Distributional impact chart (£/year by decile)...")
    create_distributional_html(output_dir / "distributional.html")

    print("2. Winners/losers stacked bar chart (% by category)...")
    create_winners_losers_html(output_dir / "winners_losers.html")

    print("3. Constituency map (D3.js choropleth)...")
    create_constituency_map_html(output_dir / "constituency_map.html")

    print("4. Poverty impact chart (pp by demographic)...")
    create_poverty_html(output_dir / "poverty_inequality.html")

    print()
    print(f"All charts saved to {output_dir}/")
    print()
    print("Charts will be available at:")
    print("  https://policyengine.github.io/uk-autumn-budget-dashboard/combined_reforms/distributional.html")
    print("  https://policyengine.github.io/uk-autumn-budget-dashboard/combined_reforms/winners_losers.html")
    print("  https://policyengine.github.io/uk-autumn-budget-dashboard/combined_reforms/constituency_map.html")
    print("  https://policyengine.github.io/uk-autumn-budget-dashboard/combined_reforms/poverty_inequality.html")


if __name__ == "__main__":
    main()
