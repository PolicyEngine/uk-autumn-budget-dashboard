"""Generate embeddable HTML charts for the combined Autumn Budget 2025 reforms blog post.

This script generates standalone HTML files that exactly replicate the charts from the
uk-combined-reforms-autumn-budget-2025.md blog post, suitable for iframing.

Charts:
1. Distributional impact (£/year by decile) - vertical bar with year slider
2. Winners/losers (% population in each category by decile) - horizontal stacked bar
3. Constituency map (average £/year by constituency) - D3.js choropleth
4. Poverty impact - line chart with toggles for absolute/relative and BHC/AHC

Data is hardcoded from the blog post analysis (from Vahid's gist calculations).

Usage:
    uv run python scripts/generate_combined_charts.py

Output:
    public/combined_reforms/*.html files for iframing
"""

import json
from pathlib import Path

# PolicyEngine design system colors (from app-v2/designTokens/colors.ts and dashboard)
COLORS = {
    # Primary teal from design system
    "primary": "#319795",  # teal/500
    "primary_dark": "#2C7A7B",  # teal/600
    "primary_700": "#285E61",  # teal/700 - darkest teal for "gain more than 5%"
    "primary_light": "#81E6D9",  # teal/200
    "primary_alpha_60": "#31979599",  # 60% opacity for "gain less than 5%"
    # Secondary/gray colors
    "gray_50": "#F9FAFB",
    "gray_100": "#F2F4F7",
    "gray_200": "#E2E8F0",  # No change category
    "gray_400": "#9CA3AF",  # Lose less than 5%
    "gray_500": "#6B7280",
    "gray_600": "#4B5563",  # Lose more than 5%
    "gray_700": "#344054",
    "gray_900": "#101828",
    # Amber colors for losses (from dashboard policyConfig.js)
    "amber_600": "#D97706",  # Primary loss color
    "amber_500": "#F59E0B",
    "amber_400": "#FBBF24",
    # Semantic colors
    "success": "#22C55E",
    "error": "#EF4444",
    "error_light": "#FCA5A5",
    # Chart-specific
    "background": "#FFFFFF",
    "text": "#000000",
}

# Font family from design system
FONT_FAMILY = "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"

YEAR_LABELS = ["2026-27", "2027-28", "2028-29", "2029-30", "2030-31"]

# ============================================================================
# DATA FROM BLOG POST (extracted from plotly JSON) - rounded to 1 decimal
# ============================================================================

# Figure 1: Distributional impact data (£/year by decile)
DISTRIBUTIONAL_DATA = {
    "2026-27": [669.9, 1139.5, 440.1, 363.7, 211.8, 152.7, 140.5, 183.4, 164.7, 170.0],
    "2027-28": [655.3, 1155.5, 441.8, 309.2, 146.1, 91.2, 54.5, 72.9, 56.0, 59.8],
    "2028-29": [458.4, 1446.0, 338.4, 283.1, 39.2, -36.7, -156.0, -179.4, -290.9, -504.8],
    "2029-30": [441.9, 1434.7, 176.4, 216.2, -180.8, -231.9, -416.1, -526.9, -1028.2, -1449.0],
    "2030-31": [466.7, 1343.2, 235.8, 58.7, -202.0, -350.2, -576.2, -766.5, -1327.7, -1874.0],
}

# Figure 2: Winners/losers data (% by category for each decile + All) - rounded to 1 decimal
# Order: ["All", " ", "10", "9", "8", "7", "6", "5", "4", "3", "2", "1"]
WINNERS_LOSERS_DATA = {
    "2026-27": {
        "gain_more_5": [8.8, None, 4.2, 5.8, 4.9, 3.8, 5.7, 5.7, 11.2, 10.5, 23.0, 13.4],
        "gain_less_5": [43.7, None, 42.6, 47.5, 53.6, 50.2, 49.1, 50.9, 38.9, 36.5, 33.5, 33.5],
        "no_change": [47.6, None, 53.2, 46.7, 41.6, 46.0, 45.2, 43.5, 50.0, 53.1, 43.6, 53.2],
        "lose_less_5": [0.0, None, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        "lose_more_5": [0.0, None, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    },
    "2027-28": {
        "gain_more_5": [8.3, None, 3.7, 5.5, 4.7, 3.3, 5.0, 5.8, 10.0, 10.7, 22.1, 12.1],
        "gain_less_5": [42.5, None, 41.3, 44.4, 51.0, 46.7, 47.8, 47.7, 41.0, 35.7, 34.0, 35.1],
        "no_change": [45.5, None, 49.6, 41.3, 36.3, 43.6, 41.8, 44.9, 48.3, 53.3, 43.8, 52.8],
        "lose_less_5": [3.7, None, 5.5, 8.8, 8.0, 6.5, 5.4, 1.6, 0.6, 0.4, 0.2, 0.0],
        "lose_more_5": [0.0, None, 0.0, 0.1, 0.0, 0.0, 0.0, 0.0, 0.1, 0.0, 0.0, 0.0],
    },
    "2028-29": {
        "gain_more_5": [6.7, None, 1.8, 0.9, 2.8, 2.2, 3.2, 4.9, 8.5, 8.4, 24.3, 10.2],
        "gain_less_5": [12.8, None, 2.8, 3.3, 9.2, 10.9, 12.3, 13.3, 16.9, 13.7, 22.1, 24.9],
        "no_change": [8.7, None, 0.8, 0.4, 1.5, 2.9, 4.4, 5.6, 7.0, 11.4, 14.6, 40.7],
        "lose_less_5": [69.8, None, 91.9, 90.8, 84.7, 81.9, 78.4, 75.3, 64.7, 65.0, 37.9, 23.4],
        "lose_more_5": [2.0, None, 2.6, 4.6, 1.8, 2.1, 1.8, 0.9, 2.9, 1.5, 1.2, 0.7],
    },
    "2029-30": {
        "gain_more_5": [4.7, None, 0.0, 0.0, 0.2, 0.2, 0.7, 1.4, 7.1, 7.0, 22.2, 8.9],
        "gain_less_5": [6.4, None, 0.2, 0.2, 2.9, 2.7, 6.9, 3.2, 7.4, 5.8, 13.2, 22.4],
        "no_change": [7.1, None, 0.3, 0.1, 0.9, 1.0, 3.8, 3.8, 5.8, 8.6, 12.1, 36.6],
        "lose_less_5": [77.1, None, 93.4, 91.7, 90.6, 91.8, 84.0, 87.2, 74.1, 75.1, 49.0, 30.1],
        "lose_more_5": [4.8, None, 6.1, 7.9, 5.5, 4.3, 4.7, 4.4, 5.6, 3.6, 3.6, 2.0],
    },
    "2030-31": {
        "gain_more_5": [4.7, None, 0.0, 0.0, 0.1, 0.2, 0.5, 2.5, 5.4, 8.6, 20.9, 9.9],
        "gain_less_5": [6.3, None, 0.2, 0.3, 3.0, 2.9, 6.4, 2.8, 6.8, 6.0, 13.3, 22.8],
        "no_change": [6.8, None, 0.3, 0.1, 1.0, 1.0, 3.8, 4.2, 3.7, 8.3, 11.3, 36.4],
        "lose_less_5": [76.7, None, 91.2, 90.9, 89.3, 91.3, 84.2, 85.1, 78.2, 73.4, 50.4, 29.0],
        "lose_more_5": [5.5, None, 8.3, 8.7, 6.6, 4.6, 5.2, 5.3, 6.0, 3.7, 4.2, 2.0],
    },
}

# Figure 4: Poverty impact data - 2x2 grid (absolute/relative × BHC/AHC) by demographic
# Demographics: Overall, Child, Working-age, Pensioner
# All values rounded to 1 decimal
POVERTY_DATA = {
    "absolute": {
        "bhc": {
            "Overall": {"2026-27": -0.7, "2027-28": -0.7, "2028-29": -0.7, "2029-30": -0.7, "2030-31": -0.8},
            "Child": {"2026-27": -2.3, "2027-28": -2.3, "2028-29": -2.5, "2029-30": -2.5, "2030-31": -2.9},
            "Working-age": {"2026-27": -0.3, "2027-28": -0.3, "2028-29": -0.4, "2029-30": -0.4, "2030-31": -0.4},
            "Pensioner": {"2026-27": 0.0, "2027-28": 0.0, "2028-29": 0.1, "2029-30": 0.1, "2030-31": 0.1},
        },
        "ahc": {
            "Overall": {"2026-27": -1.0, "2027-28": -1.1, "2028-29": -1.0, "2029-30": -0.9, "2030-31": -1.0},
            "Child": {"2026-27": -3.5, "2027-28": -3.6, "2028-29": -3.5, "2029-30": -3.4, "2030-31": -3.8},
            "Working-age": {"2026-27": -0.5, "2027-28": -0.5, "2028-29": -0.5, "2029-30": -0.4, "2030-31": -0.5},
            "Pensioner": {"2026-27": 0.0, "2027-28": 0.0, "2028-29": 0.1, "2029-30": 0.1, "2030-31": 0.1},
        },
    },
    "relative": {
        "bhc": {
            "Overall": {"2026-27": -0.5, "2027-28": -0.5, "2028-29": -0.5, "2029-30": -0.5, "2030-31": -0.6},
            "Child": {"2026-27": -1.8, "2027-28": -1.8, "2028-29": -1.9, "2029-30": -1.9, "2030-31": -2.2},
            "Working-age": {"2026-27": -0.2, "2027-28": -0.2, "2028-29": -0.3, "2029-30": -0.3, "2030-31": -0.3},
            "Pensioner": {"2026-27": 0.0, "2027-28": 0.0, "2028-29": 0.1, "2029-30": 0.0, "2030-31": 0.1},
        },
        "ahc": {
            "Overall": {"2026-27": -0.8, "2027-28": -0.8, "2028-29": -0.8, "2029-30": -0.7, "2030-31": -0.8},
            "Child": {"2026-27": -2.8, "2027-28": -2.9, "2028-29": -2.8, "2029-30": -2.7, "2030-31": -3.0},
            "Working-age": {"2026-27": -0.4, "2027-28": -0.4, "2028-29": -0.4, "2029-30": -0.3, "2030-31": -0.4},
            "Pensioner": {"2026-27": 0.0, "2027-28": 0.0, "2028-29": 0.1, "2029-30": 0.1, "2030-31": 0.1},
        },
    },
}


def create_distributional_html(output_path: Path) -> None:
    """Create Figure 1: Distributional impact chart (£/year by decile) with year slider."""

    html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Distributional Impact - Combined Autumn Budget 2025</title>
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        body {{ margin: 0; padding: 16px; font-family: {FONT_FAMILY}; background: white; }}
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
            const colors = values.map(v => v >= 0 ? '{COLORS["primary"]}' : '{COLORS["amber_600"]}');
            return {{
                x: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                y: values,
                type: 'bar',
                marker: {{ color: colors }},
                text: values.map(v => v >= 0 ? '+£' + Math.round(v).toLocaleString() : '-£' + Math.round(Math.abs(v)).toLocaleString()),
                textposition: 'outside',
                textfont: {{ family: "{FONT_FAMILY}", size: 10 }},
                hovertemplate: 'Decile %{{x}}<br>Change: £%{{y:,.0f}}<extra></extra>',
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
                gridcolor: '{COLORS["gray_200"]}'
            }},
            yaxis: {{
                title: 'Average change in household income (£/year)',
                tickprefix: '£',
                showgrid: true,
                gridcolor: '{COLORS["gray_200"]}',
                range: [-2000, 2000],
                zeroline: true,
                zerolinecolor: '{COLORS["gray_700"]}',
                zerolinewidth: 2
            }},
            height: 500,
            margin: {{ l: 80, r: 50, b: 100, t: 60 }},
            font: {{ family: "{FONT_FAMILY}" }},
            showlegend: false,
            sliders: [{{
                active: 0,
                steps: steps,
                x: 0.2,
                len: 0.6,
                y: 1.1,
                currentvalue: {{ visible: false }},
                font: {{ family: "{FONT_FAMILY}" }}
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
                text: data[year].map(v => v >= 0 ? '+£' + Math.round(v).toLocaleString() : '-£' + Math.round(Math.abs(v)).toLocaleString()),
                marker: {{ color: data[year].map(v => v >= 0 ? '{COLORS["primary"]}' : '{COLORS["amber_600"]}') }}
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
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        body {{ margin: 0; padding: 16px; font-family: {FONT_FAMILY}; background: white; }}
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
            {{ key: 'gain_more_5', name: 'Gain more than 5%', color: '{COLORS["primary_700"]}', textColor: 'white' }},
            {{ key: 'gain_less_5', name: 'Gain less than 5%', color: '{COLORS["primary_alpha_60"]}', textColor: '{COLORS["gray_700"]}' }},
            {{ key: 'no_change', name: 'No change', color: '{COLORS["gray_200"]}', textColor: '{COLORS["gray_700"]}' }},
            {{ key: 'lose_less_5', name: 'Lose less than 5%', color: '{COLORS["gray_400"]}', textColor: '{COLORS["gray_700"]}' }},
            {{ key: 'lose_more_5', name: 'Lose more than 5%', color: '{COLORS["gray_600"]}', textColor: 'white' }}
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
                text: values.map(v => v !== null && v > 0.5 ? v.toFixed(1) + '%' : ''),
                textposition: 'inside',
                textfont: {{ color: cat.textColor, size: 11, family: "{FONT_FAMILY}" }},
                hovertemplate: '%{{y}}<br>' + cat.name + ': %{{x:.1f}}%<extra></extra>',
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
                title: {{ text: 'Population share', font: {{ family: "{FONT_FAMILY}", size: 14 }} }},
                tickfont: {{ family: "{FONT_FAMILY}", size: 12 }},
                showgrid: true,
                gridcolor: '{COLORS["gray_200"]}',
                range: [0, 100],
                tickformat: '.0f',
                ticksuffix: '%'
            }},
            yaxis: {{
                title: {{ text: 'Income decile', font: {{ family: "{FONT_FAMILY}", size: 14 }} }},
                tickfont: {{ family: "{FONT_FAMILY}", size: 12 }},
                categoryorder: 'array',
                categoryarray: ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', ' ', 'All'],
                type: 'category',
                automargin: true
            }},
            height: 650,
            margin: {{ l: 80, r: 50, b: 120, t: 60 }},
            plot_bgcolor: 'white',
            paper_bgcolor: 'white',
            font: {{ family: "{FONT_FAMILY}" }},
            legend: {{
                orientation: 'h',
                yanchor: 'top',
                y: -0.12,
                xanchor: 'center',
                x: 0.5,
                font: {{ family: "{FONT_FAMILY}", size: 10 }},
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
                    text: values.map(v => v !== null && v > 0.5 ? v.toFixed(1) + '%' : '')
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
    """Create Figure 4: Poverty impact chart with toggles for absolute/relative and BHC/AHC."""

    html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Poverty Impact - Combined Autumn Budget 2025</title>
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        body {{ margin: 0; padding: 16px; font-family: {FONT_FAMILY}; background: white; }}
        #chart {{ width: 100%; height: 450px; }}
        .controls {{
            display: flex;
            gap: 24px;
            margin-bottom: 16px;
            flex-wrap: wrap;
        }}
        .toggle-group {{
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .toggle-label {{
            font-size: 14px;
            color: {COLORS["gray_700"]};
            font-weight: 500;
        }}
        .toggle-buttons {{
            display: flex;
            border: 1px solid {COLORS["gray_200"]};
            border-radius: 6px;
            overflow: hidden;
        }}
        .toggle-btn {{
            padding: 6px 12px;
            border: none;
            background: white;
            cursor: pointer;
            font-size: 13px;
            font-family: {FONT_FAMILY};
            color: {COLORS["gray_500"]};
            transition: all 0.2s;
        }}
        .toggle-btn:not(:last-child) {{
            border-right: 1px solid {COLORS["gray_200"]};
        }}
        .toggle-btn.active {{
            background: {COLORS["primary"]};
            color: white;
        }}
        .toggle-btn:hover:not(.active) {{
            background: {COLORS["gray_100"]};
        }}
    </style>
</head>
<body>
    <div class="controls">
        <div class="toggle-group">
            <span class="toggle-label">Poverty measure:</span>
            <div class="toggle-buttons" id="measure-toggle">
                <button class="toggle-btn active" data-value="absolute">Absolute</button>
                <button class="toggle-btn" data-value="relative">Relative</button>
            </div>
        </div>
        <div class="toggle-group">
            <span class="toggle-label">Housing costs:</span>
            <div class="toggle-buttons" id="housing-toggle">
                <button class="toggle-btn active" data-value="bhc">Before (BHC)</button>
                <button class="toggle-btn" data-value="ahc">After (AHC)</button>
            </div>
        </div>
    </div>
    <div id="chart"></div>
    <script>
        const povertyData = {json.dumps(POVERTY_DATA)};
        const years = {json.dumps(YEAR_LABELS)};
        const demographics = ['Overall', 'Child', 'Working-age', 'Pensioner'];
        const colors = {{
            'Overall': '{COLORS["primary"]}',
            'Child': '{COLORS["primary_dark"]}',
            'Working-age': '{COLORS["gray_500"]}',
            'Pensioner': '{COLORS["gray_400"]}'
        }};

        let currentMeasure = 'absolute';
        let currentHousing = 'bhc';

        function updateChart() {{
            const data = povertyData[currentMeasure][currentHousing];

            const traces = demographics.map(demo => ({{
                x: years,
                y: years.map(year => data[demo][year]),
                type: 'scatter',
                mode: 'lines+markers',
                name: demo,
                line: {{ color: colors[demo], width: 2 }},
                marker: {{ size: 6 }},
                hovertemplate: demo + '<br>%{{x}}: %{{y:+.1f}}pp<extra></extra>'
            }}));

            const layout = {{
                xaxis: {{
                    title: 'Fiscal year',
                    tickfont: {{ family: "{FONT_FAMILY}", size: 12 }},
                    showgrid: true,
                    gridcolor: '{COLORS["gray_200"]}'
                }},
                yaxis: {{
                    title: 'Change in poverty rate (pp)',
                    ticksuffix: 'pp',
                    showgrid: true,
                    gridcolor: '{COLORS["gray_200"]}',
                    zeroline: true,
                    zerolinecolor: '{COLORS["gray_700"]}',
                    zerolinewidth: 2,
                    range: [-4.5, 0.5]
                }},
                height: 450,
                margin: {{ l: 70, r: 50, b: 60, t: 20 }},
                font: {{ family: "{FONT_FAMILY}" }},
                legend: {{
                    orientation: 'h',
                    yanchor: 'bottom',
                    y: -0.25,
                    xanchor: 'center',
                    x: 0.5,
                    font: {{ family: "{FONT_FAMILY}", size: 12 }}
                }},
                hovermode: 'x unified'
            }};

            Plotly.react('chart', traces, layout);
        }}

        // Toggle button handlers
        document.querySelectorAll('#measure-toggle .toggle-btn').forEach(btn => {{
            btn.addEventListener('click', function() {{
                document.querySelectorAll('#measure-toggle .toggle-btn').forEach(b => b.classList.remove('active'));
                this.classList.add('active');
                currentMeasure = this.dataset.value;
                updateChart();
            }});
        }});

        document.querySelectorAll('#housing-toggle .toggle-btn').forEach(btn => {{
            btn.addEventListener('click', function() {{
                document.querySelectorAll('#housing-toggle .toggle-btn').forEach(b => b.classList.remove('active'));
                this.classList.add('active');
                currentHousing = this.dataset.value;
                updateChart();
            }});
        }});

        // Initial render
        updateChart();
    </script>
</body>
</html>'''

    output_path.write_text(html_content)
    print(f"  + Saved: {output_path}")


def create_constituency_map_html(output_path: Path) -> None:
    """Create Figure 3: Constituency map with D3.js choropleth and year slider.

    Reads constituency data from public/data/constituency.csv.
    Uses GSScode property from GeoJSON for matching.
    """
    import pandas as pd

    # Load constituency data
    constituency_df = pd.read_csv("public/data/constituency.csv")
    reform_data = constituency_df[constituency_df["reform_id"] == "autumn_budget_2025_combined"].copy()

    # Prepare data by year (map constituency code to average gain) - round to 1 decimal
    data_by_year = {}
    for year_label in YEAR_LABELS:
        year = int(year_label.split("-")[0])
        year_data = reform_data[reform_data["year"] == year]
        data_by_year[year_label] = {
            row["constituency_code"]: {
                "name": row["constituency_name"],
                "value": round(row["average_gain"], 1),
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
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        body {{ margin: 0; overflow: hidden; background: white; font-family: {FONT_FAMILY}; }}
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
        .loss {{ color: {COLORS["amber_600"]}; }}
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
            background: {COLORS["gray_200"]};
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
            color: {COLORS["gray_500"]};
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
            border: 1px solid {COLORS["gray_200"]};
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

        // Calculate global absMax across all years for consistent legend
        let globalAbsMax = 0;
        years.forEach(year => {{
            const yearData = dataByYear[year] || {{}};
            Object.values(yearData).forEach(d => {{
                if (d && !isNaN(d.value)) {{
                    globalAbsMax = Math.max(globalAbsMax, Math.abs(d.value));
                }}
            }});
        }});
        globalAbsMax = Math.ceil(globalAbsMax / 50) * 50; // Round up to nearest 50
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

        // Load GeoJSON - using GSScode property for matching
        // Note: GeoJSON uses British National Grid (EPSG:27700) coordinates, not WGS84
        // Use geoIdentity with fitSize since coordinates are already projected
        d3.json("../data/uk_constituencies_2024.geojson").then(geojson => {{
            const projection = d3.geoIdentity()
                .reflectY(true)  // BNG y-axis is inverted relative to SVG
                .fitSize([width - 100, height - 150], geojson);

            const path = d3.geoPath().projection(projection);

            // Set up fixed legend (consistent across all years)
            document.getElementById("legend-min").textContent = "-£" + globalAbsMax;
            document.getElementById("legend-max").textContent = "+£" + globalAbsMax;
            document.getElementById("legend-bar").style.background =
                `linear-gradient(to right, {COLORS["amber_600"]}, white, {COLORS["primary"]})`;

            const colorScale = d3.scaleLinear()
                .domain([-globalAbsMax, 0, globalAbsMax])
                .range(["{COLORS["amber_600"]}", "white", "{COLORS["primary"]}"]);

            function updateMap() {{
                const yearLabel = years[currentYearIndex];
                const yearData = dataByYear[yearLabel] || {{}};

                const paths = g.selectAll("path")
                    .data(geojson.features, d => d.properties.GSScode);

                paths.enter()
                    .append("path")
                    .attr("d", path)
                    .attr("stroke", "#fff")
                    .attr("stroke-width", 0.3)
                    .merge(paths)
                    .attr("fill", d => {{
                        const code = d.properties.GSScode;
                        const data = yearData[code];
                        return data ? colorScale(data.value) : "{COLORS["gray_200"]}";
                    }})
                    .on("mouseover", function(event, d) {{
                        const code = d.properties.GSScode;
                        const data = yearData[code];
                        if (data) {{
                            const tooltip = document.getElementById("tooltip");
                            const sign = data.value >= 0 ? '+' : '-';
                            tooltip.innerHTML = `<strong>${{data.name}}</strong>` +
                                `<span class="${{data.value >= 0 ? 'gain' : 'loss'}} value">` +
                                `${{sign}}£${{Math.round(Math.abs(data.value)).toLocaleString()}}/year</span>`;
                            tooltip.style.opacity = 1;
                            tooltip.style.left = (event.clientX + 15) + "px";
                            tooltip.style.top = (event.clientY + 15) + "px";
                        }}
                        d3.select(this).attr("stroke", "{COLORS["gray_700"]}").attr("stroke-width", 1.5);
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
        }}).catch(error => {{
            console.error("Error loading GeoJSON:", error);
            document.body.innerHTML = '<div style="padding: 20px; color: {COLORS["error"]};">Error loading map data. Please check the GeoJSON file path.</div>';
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

    print("4. Poverty impact chart (trend lines with toggles)...")
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
