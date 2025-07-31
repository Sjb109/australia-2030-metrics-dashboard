"""
dashboard.py
-------------

Streamlit application for the Australia‑2030 Metrics Dashboard.  The app reads
time‑series data for each metric from the `data/` directory, compares the
current value to a 2030 target, assigns a traffic‑light status and
displays interactive charts using Plotly.

Run locally with:

    streamlit run scripts/dashboard.py

"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Dict, Optional

import pandas as pd
import plotly.express as px
import streamlit as st

# Directory containing the CSV data series
DATA_DIR = Path(__file__).resolve().parents[1] / "data"

# Configuration for each metric
METRICS: Dict[str, Dict[str, object]] = {
    "gdp_growth": {
        "name": "Real GDP Growth",
        "category": "Macroeconomic",
        "target": 0.03,
        "higher_is_good": True,
        "format": "%.1f%%",
    },
    "unemployment_rate": {
        "name": "Unemployment Rate",
        "category": "Macroeconomic",
        "target": 0.05,
        "higher_is_good": False,
        "format": "%.1f%%",
    },
    "inflation": {
        "name": "Inflation (CPI)",
        "category": "Macroeconomic",
        "target": 0.025,
        "higher_is_good": False,
        "format": "%.1f%%",
    },
    "labour_productivity": {
        "name": "Labour Productivity Growth",
        "category": "Macroeconomic",
        "target": 0.015,
        "higher_is_good": True,
        "format": "%.1f%%",
    },
    # Additional metrics can be configured here.  Each entry should define:
    # - name: display name
    # - category: grouping
    # - target: numeric target for 2030 (e.g. 0.05 for 5%)
    # - higher_is_good: True if higher values represent improvement
    # - format: printf‑style format string for displaying current values
}


def load_metric_data(metric_id: str) -> Optional[pd.DataFrame]:
    """Load the data for a single metric from CSV.

    Returns
    -------
    DataFrame or None
        DataFrame with columns date, value, target.  If the file does not
        exist or is empty, returns None.
    """
    path = DATA_DIR / f"{metric_id}.csv"
    if not path.exists():
        return None
    df = pd.read_csv(path, parse_dates=["date"], dayfirst=False)
    if df.empty:
        return None
    return df


def compute_status(current: float, target: float, higher_is_good: bool) -> str:
    """Compute traffic light status based on current vs target.

    Returns "green", "amber" or "red".
    Thresholds are intentionally simple: within 5% of the target is green,
    within 20% of the target is amber, otherwise red.  For metrics where
    lower is better (higher_is_good=False), the difference is inverted.
    """
    if math.isnan(current) or math.isnan(target):
        return "grey"
    # Compute ratio of current to target (or target to current when lower is good)
    if higher_is_good:
        ratio = current / target if target != 0 else 0
    else:
        ratio = target / current if current != 0 else float('inf')
    # Determine status
    if ratio >= 0.95:
        return "green"
    elif ratio >= 0.80:
        return "amber"
    else:
        return "red"


def format_percentage(value: float) -> str:
    """Format a decimal value as a percentage string with one decimal place."""
    return f"{value * 100:.1f}%"


def main() -> None:
    st.set_page_config(page_title="Australia‑2030 Metrics Dashboard", layout="wide")
    st.title("Australia‑2030 Metrics Dashboard")
    st.markdown(
        """This dashboard tracks Australia’s economic, social and environmental indicators
        from 2025 to 2030.  Each metric shows its current value, the 2030 target,
        a trend chart and a traffic‑light status indicating progress.  Data is
        automatically updated via scheduled scripts and stored in this repository.
        """
    )

    # Build summary table
    summary_rows = []
    for metric_id, config in METRICS.items():
        df = load_metric_data(metric_id)
        if df is not None:
            latest_row = df.sort_values("date").iloc[-1]
            current_value = latest_row["value"]
            target = config["target"]
            status = compute_status(current_value, target, config["higher_is_good"])
            formatted = config["format"] % (current_value * 100) if "%" in config["format"] else config["format"] % current_value
            summary_rows.append({
                "Category": config["category"],
                "Metric": config["name"],
                "Current": formatted,
                "Target": format_percentage(target),
                "Status": status
            })
        else:
            summary_rows.append({
                "Category": config["category"],
                "Metric": config["name"],
                "Current": "No data",
                "Target": format_percentage(config["target"]),
                "Status": "grey"
            })
    summary_df = pd.DataFrame(summary_rows)

    # Display summary with colour coded status
    def status_color(val: str) -> str:
        colors = {
            "green": "background-color: #d4edda; color: #155724",
            "amber": "background-color: #fff3cd; color: #856404",
            "red": "background-color: #f8d7da; color: #721c24",
            "grey": "background-color: #e2e3e5; color: #6c757d",
        }
        return colors.get(val, "")

    st.subheader("Summary")
    styled_df = summary_df.style.applymap(lambda s: status_color(s) if s in ["green", "amber", "red", "grey"] else "")
    st.dataframe(styled_df, use_container_width=True)

    # Charts section
    st.subheader("Trend charts")
    for metric_id, config in METRICS.items():
        df = load_metric_data(metric_id)
        if df is None:
            st.info(f"No data available for {config['name']}.")
            continue
        df = df.dropna(subset=["value"])  # remove missing values
        # Convert value to percentage where appropriate
        chart_df = df.copy()
        chart_df["value_pct"] = chart_df["value"] * 100
        fig = px.line(chart_df, x="date", y="value_pct", title=config["name"], labels={"value_pct": "Value (%)", "date": "Date"})
        # Add target line
        fig.add_hline(y=config["target"] * 100, line_dash="dash", line_color="gray",
                      annotation_text=f"2030 Target: {format_percentage(config['target'])}",
                      annotation_position="top right")
        st.plotly_chart(fig, use_container_width=True)


if __name__ == "__main__":
    main()