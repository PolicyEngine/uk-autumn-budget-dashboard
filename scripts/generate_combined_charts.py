"""Generate embeddable HTML charts for the combined Autumn Budget 2025 reforms blog post.

This script reads the dashboard CSV outputs and generates standalone HTML files
that can be iframed into policyengine-app-v2 blog posts.

Charts include:
- Distributional impact (£/year) with year slider
- Winners and losers stacked bar chart with year slider
- Revenue trend line across years
- Poverty rates trend lines across years (overall, child, working-age, pensioner)
- Constituency map (D3.js interactive)

Usage:
    uv run python scripts/generate_combined_charts.py

Output:
    public/combined_reforms/*.html files for iframing
"""

import json
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# PolicyEngine app-v2 design system
# See: policyengine-app-v2/app/src/designTokens/colors.ts
COLORS = {
    # Primary teal palette
    "primary": "#319795",  # Teal-500 (main)
    "primary_light": "#4FD1C5",  # Teal-300
    "primary_dark": "#285E61",  # Teal-700
    # Gray palette
    "gray_light": "#9CA3AF",  # Gray-400
    "gray": "#6B7280",  # Gray-500
    "gray_dark": "#344054",  # Gray-700
    # Semantic
    "success": "#22C55E",
    "error": "#EF4444",
    # UI
    "neutral": "#F2F4F7",  # Gray-100
    "background": "#FFFFFF",
    "text": "#000000",
}

# Inter is PolicyEngine's official font
FONT_FAMILY = "Inter, sans-serif"

REFORM_ID = "autumn_budget_2025_combined"
YEARS = [2026, 2027, 2028, 2029, 2030]
YEAR_LABELS = ["2026-27", "2027-28", "2028-29", "2029-30", "2030-31"]


def save_plotly_html(fig: go.Figure, output_path: Path, title: str = "") -> None:
    """Save a Plotly figure as a standalone HTML file suitable for iframing."""
    html_content = fig.to_html(
        include_plotlyjs="cdn",
        full_html=True,
        config={
            "displayModeBar": True,
            "modeBarButtonsToRemove": ["lasso2d", "select2d"],
            "displaylogo": False,
        },
    )

    # Add responsive styling for iframe embedding
    html_content = html_content.replace(
        "<head>",
        """<head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { margin: 0; padding: 0; font-family: Inter, sans-serif; }
        .plotly-graph-div { width: 100% !important; }
    </style>"""
    )

    output_path.write_text(html_content)
    print(f"  + Saved: {output_path}")


def create_distributional_chart(df: pd.DataFrame) -> go.Figure:
    """Create distributional impact chart (£/year) with year slider.

    Shows average change in household income by income decile.
    """
    reform_data = df[df["reform_id"] == REFORM_ID].copy()

    # Parse decile number
    reform_data["decile_num"] = reform_data["decile"].str.extract(r"(\d+)").astype(int)

    # Create figure with slider
    fig = go.Figure()

    for i, year in enumerate(YEARS):
        year_data = reform_data[reform_data["year"] == year].sort_values("decile_num")
        if year_data.empty:
            continue

        # Convert percentage to £/year (approximate using avg income by decile)
        # For now, use the raw percentage values scaled
        values = year_data["value"].tolist()

        # Color bars based on positive/negative
        bar_colors = [COLORS["primary"] if v >= 0 else COLORS["error"] for v in values]

        fig.add_trace(
            go.Bar(
                x=list(range(1, 11)),
                y=values,
                marker_color=bar_colors,
                text=[f"{v:+.2f}%" for v in values],
                textposition="outside",
                textfont=dict(family=FONT_FAMILY, size=11),
                hovertemplate="Decile %{x}<br>Change: %{y:+.2f}%<extra></extra>",
                visible=(i == 0),
                name=YEAR_LABELS[i],
            )
        )

    # Create slider steps
    steps = []
    for i, label in enumerate(YEAR_LABELS):
        step = dict(
            method="update",
            args=[{"visible": [j == i for j in range(len(YEARS))]}],
            label=label,
        )
        steps.append(step)

    fig.update_layout(
        xaxis=dict(
            title="Income decile",
            tickmode="linear",
            tick0=1,
            dtick=1,
            showgrid=True,
            gridcolor="#e0e0e0",
        ),
        yaxis=dict(
            title="Relative change in net income (%)",
            showgrid=True,
            gridcolor="#e0e0e0",
            zeroline=True,
            zerolinecolor=COLORS["gray_dark"],
            zerolinewidth=2,
            ticksuffix="%",
        ),
        height=500,
        margin=dict(l=80, r=40, b=120, t=60),
        plot_bgcolor=COLORS["background"],
        paper_bgcolor=COLORS["background"],
        font=dict(family=FONT_FAMILY),
        sliders=[dict(
            active=0,
            currentvalue=dict(prefix="Year: ", font=dict(size=14)),
            pad=dict(t=50),
            steps=steps,
            x=0.1,
            len=0.8,
        )],
        showlegend=False,
    )

    return fig


def create_winners_losers_chart(df: pd.DataFrame) -> go.Figure:
    """Create winners/losers stacked bar chart with year slider.

    Shows percentage of population gaining vs losing by income decile.
    """
    reform_data = df[df["reform_id"] == REFORM_ID].copy()

    # Filter out 'all' decile for per-decile view
    reform_data = reform_data[reform_data["decile"] != "all"]

    fig = go.Figure()

    for i, year in enumerate(YEARS):
        year_data = reform_data[reform_data["year"] == year].sort_values("decile")
        if year_data.empty:
            continue

        values = year_data["avg_change"].tolist()
        bar_colors = [COLORS["primary"] if v >= 0 else COLORS["error"] for v in values]

        fig.add_trace(
            go.Bar(
                x=list(range(1, 11)),
                y=values,
                marker_color=bar_colors,
                text=[f"£{v:+,.0f}" for v in values],
                textposition="outside",
                textfont=dict(family=FONT_FAMILY, size=10),
                hovertemplate="Decile %{x}<br>Avg change: £%{y:,.0f}<extra></extra>",
                visible=(i == 0),
                name=YEAR_LABELS[i],
            )
        )

    steps = []
    for i, label in enumerate(YEAR_LABELS):
        step = dict(
            method="update",
            args=[{"visible": [j == i for j in range(len(YEARS))]}],
            label=label,
        )
        steps.append(step)

    fig.update_layout(
        xaxis=dict(
            title="Income decile",
            tickmode="linear",
            tick0=1,
            dtick=1,
            showgrid=True,
            gridcolor="#e0e0e0",
        ),
        yaxis=dict(
            title="Average change in household income (£/year)",
            showgrid=True,
            gridcolor="#e0e0e0",
            zeroline=True,
            zerolinecolor=COLORS["gray_dark"],
            zerolinewidth=2,
            tickprefix="£",
        ),
        height=500,
        margin=dict(l=100, r=40, b=120, t=60),
        plot_bgcolor=COLORS["background"],
        paper_bgcolor=COLORS["background"],
        font=dict(family=FONT_FAMILY),
        sliders=[dict(
            active=0,
            currentvalue=dict(prefix="Year: ", font=dict(size=14)),
            pad=dict(t=50),
            steps=steps,
            x=0.1,
            len=0.8,
        )],
        showlegend=False,
    )

    return fig


def create_revenue_chart(df: pd.DataFrame) -> go.Figure:
    """Create revenue trend line chart across years."""
    reform_data = df[df["reform_id"] == REFORM_ID].sort_values("year")

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=YEAR_LABELS,
            y=reform_data["value"].tolist(),
            mode="lines+markers+text",
            line=dict(color=COLORS["primary"], width=3),
            marker=dict(size=10, color=COLORS["primary"]),
            text=[f"£{v:.1f}bn" for v in reform_data["value"]],
            textposition="top center",
            textfont=dict(family=FONT_FAMILY, size=12),
            hovertemplate="Year: %{x}<br>Revenue: £%{y:.2f}bn<extra></extra>",
        )
    )

    fig.update_layout(
        xaxis=dict(
            title="Fiscal year",
            showgrid=True,
            gridcolor="#e0e0e0",
        ),
        yaxis=dict(
            title="Budgetary impact (£ billion)",
            showgrid=True,
            gridcolor="#e0e0e0",
            zeroline=True,
            zerolinecolor=COLORS["gray_dark"],
            zerolinewidth=2,
            tickprefix="£",
            ticksuffix="bn",
        ),
        height=450,
        margin=dict(l=100, r=40, b=80, t=40),
        plot_bgcolor=COLORS["background"],
        paper_bgcolor=COLORS["background"],
        font=dict(family=FONT_FAMILY),
        showlegend=False,
    )

    return fig


def create_poverty_trend_html(output_path: Path) -> None:
    """Create an interactive poverty chart with multiple trend lines.

    Shows all four demographic groups (Child, Overall, Working-age, Pensioner) as
    separate trend lines on one plot, with toggle for:
    - Housing costs: AHC vs BHC

    Data shows absolute poverty change in percentage points.
    Colors from app-v2 design system (designTokens/colors.ts).

    Uses hardcoded data from the blog post analysis (from gist).
    """
    # Data from the blog post analysis
    # Absolute poverty changes in percentage points
    # Colors from app-v2 design system (designTokens/colors.ts)
    poverty_data = {
        "child": {
            "label": "Child",
            "color": "#319795",  # primary[500] - teal
            "bhc": [-2.30, -2.31, -2.50, -2.47, -2.88],
            "ahc": [-3.51, -3.59, -3.46, -3.35, -3.77],
        },
        "overall": {
            "label": "Overall",
            "color": "#0284C7",  # blue[600]
            "bhc": [-0.69, -0.69, -0.74, -0.73, -0.81],
            "ahc": [-1.02, -1.05, -0.99, -0.94, -1.02],
        },
        "working_age": {
            "label": "Working-age",
            "color": "#4B5563",  # gray[600]
            "bhc": [-0.34, -0.33, -0.37, -0.36, -0.37],
            "ahc": None,  # Only BHC available
        },
        "pensioner": {
            "label": "Pensioner",
            "color": "#9CA3AF",  # gray[400]
            "bhc": [0.00, 0.00, 0.08, 0.05, 0.14],
            "ahc": None,  # Only BHC available
        },
    }

    html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Poverty Impact - Combined Autumn Budget 2025</title>
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: white;
            padding: 24px;
        }}
        .controls {{
            display: flex;
            flex-wrap: wrap;
            gap: 16px;
            margin-bottom: 24px;
            justify-content: center;
        }}
        .control-group {{
            background: #F9FAFB;
            padding: 14px 18px;
            border-radius: 8px;
            border: 1px solid #E2E8F0;
        }}
        .control-group h3 {{
            color: #344054;
            font-size: 0.7rem;
            margin-bottom: 10px;
            text-transform: uppercase;
            letter-spacing: 0.8px;
            font-weight: 600;
        }}
        .toggle-buttons {{
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
        }}
        .toggle-btn {{
            padding: 8px 14px;
            border: 1px solid #CBD5E1;
            background: white;
            color: #344054;
            border-radius: 6px;
            cursor: pointer;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            font-size: 0.8rem;
            font-weight: 500;
            transition: all 0.2s ease;
        }}
        .toggle-btn:hover {{
            background: #F9FAFB;
            border-color: #94A3B8;
        }}
        .toggle-btn.active {{
            background: #319795;
            color: white;
            border-color: #319795;
        }}
        #chart {{
            width: 100%;
            height: 420px;
            border-radius: 8px;
            overflow: hidden;
        }}
        .chart-title {{
            text-align: center;
            font-size: 1rem;
            font-weight: 600;
            color: #000000;
            margin-bottom: 4px;
        }}
        .chart-subtitle {{
            text-align: center;
            font-size: 0.8rem;
            color: #6B7280;
            margin-bottom: 16px;
        }}
        @media (max-width: 640px) {{
            .controls {{
                flex-direction: column;
                align-items: stretch;
            }}
            .control-group {{
                width: 100%;
            }}
            .toggle-buttons {{
                justify-content: center;
            }}
        }}
    </style>
</head>
<body>
    <div class="chart-title">Change in absolute poverty rate</div>
    <div class="chart-subtitle">Combined Autumn Budget 2025 reforms</div>

    <div class="controls">
        <div class="control-group">
            <h3>Housing Costs</h3>
            <div class="toggle-buttons">
                <button class="toggle-btn active" data-housing="ahc" onclick="setHousing('ahc')"><span>After housing costs</span></button>
                <button class="toggle-btn" data-housing="bhc" onclick="setHousing('bhc')"><span>Before housing costs</span></button>
            </div>
        </div>
    </div>

    <div id="chart"></div>

    <script>
        const povertyData = {json.dumps(poverty_data)};
        const years = {json.dumps(YEAR_LABELS)};

        let currentHousing = 'ahc';

        function setHousing(housing) {{
            currentHousing = housing;
            document.querySelectorAll('[data-housing]').forEach(btn => {{
                btn.classList.toggle('active', btn.dataset.housing === housing);
            }});
            updateChart();
        }}

        function updateChart() {{
            let traces = [];
            const housingLabel = currentHousing === 'ahc' ? 'after housing costs' : 'before housing costs';

            const groups = ['child', 'overall', 'working_age', 'pensioner'];
            groups.forEach(group => {{
                const data = povertyData[group];

                // Use AHC if available and selected, otherwise use BHC
                let values;
                let label = data.label;
                if (data[currentHousing]) {{
                    values = data[currentHousing];
                }} else {{
                    values = data.bhc;
                    label = data.label + ' (BHC only)';
                }}

                traces.push({{
                    x: years,
                    y: values,
                    type: 'scatter',
                    mode: 'lines+markers',
                    name: label,
                    line: {{
                        color: data.color,
                        width: 3
                    }},
                    marker: {{
                        size: 8,
                        color: data.color,
                        line: {{ color: 'white', width: 2 }}
                    }},
                    hovertemplate: '<b>' + data.label + '</b><br>%{{x}}: %{{y:+.2f}}pp<extra></extra>'
                }});
            }});

            // Calculate y-axis range across all traces
            let allValues = [];
            traces.forEach(t => allValues = allValues.concat(t.y));
            const minVal = Math.min(...allValues);
            const maxVal = Math.max(...allValues);
            const padding = Math.max(Math.abs(minVal), Math.abs(maxVal)) * 0.15;

            const layout = {{
                xaxis: {{
                    title: {{ text: 'Fiscal year', font: {{ size: 12, color: '#000000' }} }},
                    tickfont: {{ family: 'Inter', size: 11, color: '#000000' }},
                    showgrid: true,
                    gridcolor: '#E2E8F0',
                    gridwidth: 1
                }},
                yaxis: {{
                    title: {{ text: 'Change (percentage points)', font: {{ size: 12, color: '#000000' }} }},
                    tickfont: {{ family: 'Inter', size: 11, color: '#000000' }},
                    ticksuffix: 'pp',
                    range: [minVal - padding, maxVal + padding],
                    zeroline: true,
                    zerolinewidth: 2,
                    zerolinecolor: '#000000',
                    showgrid: true,
                    gridcolor: '#E2E8F0',
                    gridwidth: 1
                }},
                margin: {{ t: 20, r: 40, b: 80, l: 70 }},
                font: {{ family: 'Inter, -apple-system, BlinkMacSystemFont, sans-serif', color: '#000000' }},
                plot_bgcolor: 'white',
                paper_bgcolor: 'white',
                legend: {{
                    orientation: 'h',
                    yanchor: 'top',
                    y: -0.2,
                    xanchor: 'center',
                    x: 0.5,
                    font: {{ size: 11, color: '#000000' }}
                }},
                shapes: [{{
                    type: 'line',
                    x0: years[0],
                    x1: years[years.length - 1],
                    y0: 0,
                    y1: 0,
                    line: {{ color: '#9CA3AF', width: 1, dash: 'dot' }}
                }}]
            }};

            const config = {{
                responsive: true,
                displayModeBar: false
            }};

            Plotly.react('chart', traces, layout, config);
        }}

        // Initial render
        updateChart();
    </script>
</body>
</html>'''

    output_path.write_text(html_content)
    print(f"  + Saved: {output_path}")


def create_constituency_map_html(df: pd.DataFrame, output_path: Path) -> None:
    """Create interactive D3.js constituency map.

    This creates a standalone HTML file with D3.js visualization,
    similar to the existing constituency_map.html pattern.
    """
    reform_data = df[df["reform_id"] == REFORM_ID].copy()

    # Prepare data by year
    data_by_year = {}
    for year in YEARS:
        year_label = YEAR_LABELS[YEARS.index(year)]
        year_data = reform_data[reform_data["year"] == year]
        data_by_year[year_label] = {
            row["constituency_code"]: {
                "name": row["constituency_name"],
                "avg_gain": round(row["average_gain"], 2),
            }
            for _, row in year_data.iterrows()
        }

    # Generate HTML with embedded D3.js
    html_template = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>UK Constituency Map - Combined Autumn Budget 2025 Impact</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        body {{ margin: 0; overflow: hidden; background: white; font-family: Inter, sans-serif; }}
        svg {{ display: block; }}
        .tooltip {{ position: fixed; background: white; padding: 10px 14px; border-radius: 6px; box-shadow: 0 2px 12px rgba(0,0,0,0.15); pointer-events: none; opacity: 0; font-size: 13px; z-index: 1001; }}
        .tooltip strong {{ display: block; margin-bottom: 4px; }}
        .tooltip .value {{ font-weight: 600; }}
        .gain {{ color: {COLORS["primary"]}; }}
        .loss {{ color: {COLORS["error"]}; }}
        .zoom-controls {{ position: absolute; top: 70px; left: 10px; display: flex; flex-direction: column; gap: 5px; }}
        .zoom-btn {{ width: 32px; height: 32px; border: 1px solid #ccc; background: white; border-radius: 4px; cursor: pointer; font-size: 18px; display: flex; align-items: center; justify-content: center; box-shadow: 0 1px 4px rgba(0,0,0,0.1); }}
        .zoom-btn:hover {{ background: #f0f0f0; }}
        .search-container {{ position: absolute; top: 10px; left: 10px; z-index: 1000; }}
        .search-input {{ width: 200px; padding: 8px 12px; border: 1px solid #ccc; border-radius: 6px; font-size: 13px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); outline: none; }}
        .search-input:focus {{ border-color: {COLORS["primary"]}; }}
        .search-results {{ position: absolute; top: 100%; left: 0; right: 0; background: white; border: 1px solid #ccc; border-top: none; border-radius: 0 0 6px 6px; max-height: 200px; overflow-y: auto; display: none; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }}
        .search-result-item {{ padding: 8px 12px; cursor: pointer; font-size: 12px; border-bottom: 1px solid #eee; }}
        .search-result-item:hover {{ background: #f5f5f5; }}
        .legend {{ position: absolute; top: 70px; right: 10px; padding: 5px; font-size: 12px; z-index: 1000; }}
        .legend-bar {{ width: 120px; height: 12px; border-radius: 2px; }}
        .legend-labels {{ display: flex; justify-content: space-between; font-size: 10px; color: #666; margin-top: 4px; }}
        .year-controls {{ position: absolute; top: 10px; right: 10px; background: white; padding: 10px 20px; border-radius: 8px; box-shadow: 0 2px 12px rgba(0,0,0,0.15); display: flex; align-items: center; gap: 15px; z-index: 1000; }}
        .play-btn {{ width: 36px; height: 36px; border: none; background: {COLORS["primary"]}; color: white; border-radius: 50%; cursor: pointer; font-size: 14px; display: flex; align-items: center; justify-content: center; }}
        .play-btn:hover {{ background: {COLORS["primary_dark"]}; }}
        .year-slider {{ width: 250px; height: 6px; -webkit-appearance: none; background: #e5e5e5; border-radius: 3px; outline: none; }}
        .year-slider::-webkit-slider-thumb {{ -webkit-appearance: none; width: 18px; height: 18px; background: {COLORS["primary"]}; border-radius: 50%; cursor: pointer; }}
        .year-marks {{ display: flex; justify-content: space-between; width: 250px; font-size: 10px; color: #666; margin-top: 5px; }}
    </style>
</head>
<body>
    <div class="year-controls">
        <button class="play-btn" id="play-btn" title="Play animation">&#9654;</button>
        <div>
            <input type="range" class="year-slider" id="year-slider" min="0" max="4" value="0" step="1">
            <div class="year-marks">
                {"".join(f"<span>{y}</span>" for y in YEAR_LABELS)}
            </div>
        </div>
    </div>
    <div class="search-container">
        <input type="text" class="search-input" id="search-input" placeholder="Search constituency..." autocomplete="off">
        <div class="search-results" id="search-results"></div>
    </div>
    <div class="zoom-controls">
        <button class="zoom-btn" id="zoom-in" title="Zoom In">+</button>
        <button class="zoom-btn" id="zoom-out" title="Zoom Out">−</button>
        <button class="zoom-btn" id="zoom-reset" title="Reset">⟲</button>
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

        // Initialize map visualization
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

        // Load GeoJSON and render
        d3.json("/data/uk_constituencies_2024.geojson").then(geojson => {{
            const projection = d3.geoMercator()
                .fitSize([width - 100, height - 100], geojson);

            const path = d3.geoPath().projection(projection);

            function updateMap() {{
                const yearLabel = years[currentYearIndex];
                const yearData = dataByYear[yearLabel] || {{}};

                const values = Object.values(yearData).map(d => d.avg_gain);
                const minVal = Math.min(...values);
                const maxVal = Math.max(...values);

                const colorScale = d3.scaleLinear()
                    .domain([minVal, 0, maxVal])
                    .range(["{COLORS["error"]}", "#f5f5f5", "{COLORS["primary"]}"]);

                // Update legend
                document.getElementById("legend-min").textContent = "£" + Math.round(minVal);
                document.getElementById("legend-max").textContent = "£" + Math.round(maxVal);
                document.getElementById("legend-bar").style.background =
                    `linear-gradient(to right, {COLORS["error"]}, #f5f5f5, {COLORS["primary"]})`;

                const paths = g.selectAll("path")
                    .data(geojson.features, d => d.properties.PCON24CD);

                paths.enter()
                    .append("path")
                    .attr("d", path)
                    .attr("stroke", "#fff")
                    .attr("stroke-width", 0.5)
                    .merge(paths)
                    .attr("fill", d => {{
                        const code = d.properties.PCON24CD;
                        const data = yearData[code];
                        return data ? colorScale(data.avg_gain) : "#ccc";
                    }})
                    .on("mouseover", function(event, d) {{
                        const code = d.properties.PCON24CD;
                        const data = yearData[code];
                        if (data) {{
                            const tooltip = document.getElementById("tooltip");
                            tooltip.innerHTML = `<strong>${{data.name}}</strong>` +
                                `<span class="${{data.avg_gain >= 0 ? 'gain' : 'loss'}} value">` +
                                `£${{data.avg_gain >= 0 ? '+' : ''}}${{data.avg_gain.toFixed(0)}}/year</span>`;
                            tooltip.style.opacity = 1;
                            tooltip.style.left = (event.clientX + 10) + "px";
                            tooltip.style.top = (event.clientY + 10) + "px";
                        }}
                        d3.select(this).attr("stroke", "#333").attr("stroke-width", 2);
                    }})
                    .on("mouseout", function() {{
                        document.getElementById("tooltip").style.opacity = 0;
                        d3.select(this).attr("stroke", "#fff").attr("stroke-width", 0.5);
                    }});
            }}

            updateMap();

            // Year slider
            document.getElementById("year-slider").addEventListener("input", function() {{
                currentYearIndex = parseInt(this.value);
                updateMap();
            }});

            // Play button
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

            // Zoom controls
            document.getElementById("zoom-in").addEventListener("click", () => svg.transition().call(zoom.scaleBy, 1.5));
            document.getElementById("zoom-out").addEventListener("click", () => svg.transition().call(zoom.scaleBy, 0.67));
            document.getElementById("zoom-reset").addEventListener("click", () => svg.transition().call(zoom.transform, d3.zoomIdentity));

            // Search functionality
            const searchInput = document.getElementById("search-input");
            const searchResults = document.getElementById("search-results");
            const allConstituencies = Object.entries(dataByYear[years[0]] || {{}})
                .map(([code, data]) => ({{ code, name: data.name }}));

            searchInput.addEventListener("input", function() {{
                const query = this.value.toLowerCase();
                if (query.length < 2) {{
                    searchResults.style.display = "none";
                    return;
                }}
                const matches = allConstituencies
                    .filter(c => c.name.toLowerCase().includes(query))
                    .slice(0, 10);

                if (matches.length > 0) {{
                    searchResults.innerHTML = matches.map(c =>
                        `<div class="search-result-item" data-code="${{c.code}}">${{c.name}}</div>`
                    ).join("");
                    searchResults.style.display = "block";
                }} else {{
                    searchResults.style.display = "none";
                }}
            }});

            searchResults.addEventListener("click", function(e) {{
                if (e.target.classList.contains("search-result-item")) {{
                    const code = e.target.dataset.code;
                    const feature = geojson.features.find(f => f.properties.PCON24CD === code);
                    if (feature) {{
                        const [[x0, y0], [x1, y1]] = path.bounds(feature);
                        svg.transition().duration(750).call(
                            zoom.transform,
                            d3.zoomIdentity
                                .translate(width / 2, height / 2)
                                .scale(4)
                                .translate(-(x0 + x1) / 2, -(y0 + y1) / 2)
                        );
                    }}
                    searchInput.value = e.target.textContent;
                    searchResults.style.display = "none";
                }}
            }});
        }});
    </script>
</body>
</html>'''

    output_path.write_text(html_template)
    print(f"  + Saved: {output_path}")


def main():
    """Generate all charts for combined reforms blog post."""
    data_dir = Path("public/data")
    output_dir = Path("public/combined_reforms")
    output_dir.mkdir(parents=True, exist_ok=True)

    print("Generating charts for combined Autumn Budget 2025 reforms...")
    print()

    # Load data
    distributional_df = pd.read_csv(data_dir / "distributional_impact.csv")
    winners_losers_df = pd.read_csv(data_dir / "winners_losers.csv")
    budgetary_df = pd.read_csv(data_dir / "budgetary_impact.csv")
    metrics_df = pd.read_csv(data_dir / "metrics.csv")
    constituency_df = pd.read_csv(data_dir / "constituency.csv")

    # Generate charts
    print("1. Distributional impact chart (relative %)...")
    fig = create_distributional_chart(distributional_df)
    save_plotly_html(fig, output_dir / "distributional.html", "Distributional Impact")

    print("2. Winners/losers chart (absolute £)...")
    fig = create_winners_losers_chart(winners_losers_df)
    save_plotly_html(fig, output_dir / "winners_losers.html", "Winners and Losers")

    print("3. Revenue trend chart...")
    fig = create_revenue_chart(budgetary_df)
    save_plotly_html(fig, output_dir / "revenue.html", "Revenue Impact")

    print("4. Poverty and inequality chart with toggles...")
    create_poverty_trend_html(output_dir / "poverty_inequality.html")

    print("5. Constituency map...")
    create_constituency_map_html(constituency_df, output_dir / "constituency_map.html")

    print()
    print(f"All charts saved to {output_dir}/")
    print()
    print("To embed in blog post, use iframe tags:")
    print('  <iframe src="https://uk-autumn-budget-dashboard.vercel.app/combined_reforms/distributional.html" width="100%" height="550" frameborder="0"></iframe>')


if __name__ == "__main__":
    main()
