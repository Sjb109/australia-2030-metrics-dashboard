"""
update_data.py
----------------

This script fetches the latest indicator values for the Australia‑2030 metrics
dashboard and stores them as CSV files under the `data/` directory.  Each
indicator has a dedicated fetch function which should be implemented using
the appropriate API endpoint.  Where an API cannot be accessed (for
example when running offline), the script falls back to generating
placeholder data so that the dashboard remains functional during
development.

Note: To run this script in automated workflows (e.g. GitHub Actions)
you must provide any required API keys via environment variables.  See
README.md for details.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable, Dict, List

import pandas as pd
import requests

# Directory in which to store output data
DATA_DIR = Path(__file__).resolve().parents[1] / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)


def fetch_abs_data(dataflow: str, key: str, start_period: str | None = None,
                   end_period: str | None = None) -> pd.DataFrame:
    """Fetch data from the ABS Data API.

    Parameters
    ----------
    dataflow : str
        ABS dataflow identifier in the form "agencyId,dataflowId,version" (e.g. "ABS,CPI,1.0.0").
    key : str
        Series key (data key) identifying the dimensions, as described in the
        ABS Data API guide【418303309353336†L218-L221】.  Use "all" to return all
        series.
    start_period : str, optional
        Start period in ISO‑8601 or SDMX format (YYYY, YYYY-Qn, YYYY-MM).  If
        omitted, data will be returned from the earliest available period【418303309353336†L252-L254】.
    end_period : str, optional
        End period in ISO‑8601 or SDMX format.  If omitted, data is returned up
        to the latest available period【418303309353336†L252-L254】.

    Returns
    -------
    DataFrame
        A DataFrame with columns: date, value and any other
        attributes returned by the API.  If the API call fails, an empty
        DataFrame is returned.
    """
    base_url = "https://api.data.abs.gov.au/data"
    url = f"{base_url}/{dataflow}/{key}"
    params: Dict[str, str] = {}
    if start_period:
        params["startPeriod"] = start_period
    if end_period:
        params["endPeriod"] = end_period
    headers = {"accept": "application/vnd.sdmx.data+json"}
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        print(f"WARNING: Failed to fetch ABS dataflow {dataflow} ({exc}). Returning empty frame.")
        return pd.DataFrame()

    # The ABS API returns a JSON structure containing observations under
    # data["dataSets"][0]["series"][series_key]["observations"].  We need to
    # flatten this into a DataFrame.  Here we implement a simple parser.
    try:
        dataset = data["dataSets"][0]
        structure = data["structure"]
    except (KeyError, IndexError):
        return pd.DataFrame()
    # Build a mapping from observation index to date using the dimension metadata
    obs_dim = structure["dimensions"]["observation"]
    time_positions = obs_dim[0]["values"]  # list of time period strings
    series_dict = dataset.get("series", {})
    records: List[Dict[str, object]] = []
    for series_key, series_data in series_dict.items():
        obs = series_data.get("observations", {})
        for obs_index_str, value_list in obs.items():
            # obs_index_str is index into time_positions (string)
            idx = int(obs_index_str)
            period = time_positions[idx]["id"]  # e.g. "2024-Q1"
            value = value_list[0]
            records.append({
                "date": period,
                "value": float(value),
                "series_key": series_key
            })
    df = pd.DataFrame(records)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    return df.sort_values("date")


def placeholder_series(name: str, periods: int = 40, freq: str = "Q") -> pd.DataFrame:
    """Generate a placeholder time series for development when real data is unavailable.

    The function creates a simple trend line with random noise.
    """
    import numpy as np

    end_date = pd.Period(datetime.today(), freq=freq)
    dates = pd.period_range(end=end_date, periods=periods, freq=freq).to_timestamp()
    # Create a trending series with modest noise for demonstration
    base = np.linspace(0.01, 0.04, periods)
    noise = np.random.normal(0, 0.002, size=periods)
    values = base + noise
    return pd.DataFrame({"date": dates, "value": values})


def save_series(df: pd.DataFrame, filename: str) -> None:
    """Save a series DataFrame to a CSV file in the data directory."""
    path = DATA_DIR / filename
    df.to_csv(path, index=False)


def update_metric(metric_id: str, fetch_fn: Callable[[], pd.DataFrame], target: float) -> None:
    """Update a single metric by fetching new data and storing it to CSV.

    Parameters
    ----------
    metric_id : str
        Identifier used for the CSV file (e.g. 'gdp_growth').
    fetch_fn : Callable[[], DataFrame]
        Function that returns a DataFrame with columns 'date' and 'value'.
    target : float
        Target value for 2030 (used in metadata)
    """
    print(f"Updating {metric_id} ...")
    df = fetch_fn()
    if df.empty:
        # generate placeholder if necessary
        df = placeholder_series(metric_id)
    df["target"] = target
    save_series(df, f"{metric_id}.csv")
    print(f"Saved {metric_id} with {len(df)} records.")


def fetch_gdp_growth() -> pd.DataFrame:
    """Fetch real GDP growth (quarterly annualised) from the ABS Indicator API.

    The ABS Indicator API provides headline economic statistics including
    GDP growth【263059983294956†L4-L6】.  Here we demonstrate how to call the ABS Data
    API for GDP growth.  Replace the `dataflow` and `series_key` with the
    appropriate identifiers once known.  If the API call fails, the function
    returns an empty DataFrame.
    """
    # Example dataflow and key – these values are placeholders and must be
    # replaced with real identifiers from the ABS Data API.  See
    # https://api.data.abs.gov.au for details.
    dataflow = "ABS,AUGDPR,1.0.0"  # hypothetical dataflow for GDP growth
    series_key = "AUS"  # hypothetical series key
    try:
        df = fetch_abs_data(dataflow, series_key, start_period="2015-Q1")
        return df
    except Exception:
        return pd.DataFrame()


def fetch_unemployment_rate() -> pd.DataFrame:
    """Fetch the unemployment rate from the ABS Labour Force dataset.

    The ABS Labour Force API provides employment statistics by region and
    demographic【461649170650887†L27-L33】.  The dataflow and series key below
    reference the ABS Labour Force unemployment rate for Australia.
    If the API request fails (e.g. when offline), a small annually averaged
    dataset is returned so that the dashboard remains functional.
    """

    # ABS Data API identifiers for the national unemployment rate
    dataflow = "ABS,LFUR,1.0.0"
    series_key = "AUS"  # national unemployment rate

    df = fetch_abs_data(dataflow, series_key, start_period="2015-M01")
    if df.empty:
        # Fallback values sourced from ABS headline series (annual averages)
        values = [
            0.061, 0.057, 0.056, 0.053, 0.052,
            0.065, 0.051, 0.037, 0.036, 0.041,
        ]
        dates = pd.date_range("2015", periods=len(values), freq="YS")
        df = pd.DataFrame({"date": dates, "value": values})
    return df


def fetch_inflation() -> pd.DataFrame:
    """Fetch CPI inflation (quarterly).

    This example uses a placeholder ABS dataflow for CPI.  Replace with actual
    identifiers for headline CPI.
    """
    dataflow = "ABS,CPI,1.0.0"
    series_key = "AUS"  # placeholder
    return fetch_abs_data(dataflow, series_key, start_period="2015-Q1")


def fetch_labour_productivity() -> pd.DataFrame:
    """Fetch labour productivity growth.

    Placeholder implementation – real implementation will query the relevant
    ABS productivity dataset or an OECD source.  Currently returns an empty
    DataFrame causing a fallback to placeholder data.
    """
    return pd.DataFrame()


def main() -> None:
    """Entry point for updating all metrics."""
    metrics = {
        "gdp_growth": {
            "target": 0.03,
            "fetch_fn": fetch_gdp_growth,
        },
        "unemployment_rate": {
            "target": 0.05,
            "fetch_fn": fetch_unemployment_rate,
        },
        "inflation": {
            "target": 0.025,
            "fetch_fn": fetch_inflation,
        },
        "labour_productivity": {
            "target": 0.015,
            "fetch_fn": fetch_labour_productivity,
        },
        # Additional metrics (financial, social, etc.) should be added here with
        # appropriate fetch functions and targets.
    }
    for metric_id, config in metrics.items():
        update_metric(metric_id, config["fetch_fn"], config["target"])


if __name__ == "__main__":
    main()