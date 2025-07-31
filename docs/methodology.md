# Data collection methodology

This document explains how the **Australia‑2030 metrics dashboard** collects,
processes and presents data.  The aim is to be transparent about the
provenance of the data and the assumptions used to compute the traffic‑light
indicators.

## ABS Data API

Most macroeconomic, labour and demographic statistics are pulled from the
Australian Bureau of Statistics (ABS) **Data API**.  According to the ABS
user guide, the API offers two modes of operation: **data retrieval** (for
known series such as the unemployment rate) and **data discovery** (to explore
available datasets)【418303309353336†L186-L191】.  Data can be requested via the
path `/data/{dataflowIdentifier}/{dataKey}` with optional `startPeriod` and
`endPeriod` parameters【418303309353336†L195-L200】.  A *dataflow identifier*
identifies a dataset (e.g. CPI), while a *data key* filters dimensions such
as geography, measure and frequency【418303309353336†L218-L221】.  If no start
or end period is provided, the API returns the full historical series【418303309353336†L252-L254】.

For example, to retrieve the national unemployment rate we specify the
dataflow for the labour force survey and the series key representing the
Australian total.  The script `scripts/update_data.py` encapsulates these
details in functions like `fetch_unemployment_rate()`.

### Frequency and date formats

The ABS API uses ISO 8601 or SDMX reporting periods to specify dates.  Valid
formats include yearly (`YYYY`), quarterly (`YYYY-Q1`), monthly (`YYYY-MM`)
and weekly (`YYYY-W01`)【418303309353336†L247-L263】.  When retrieving a series
we choose the frequency that matches the indicator (e.g. quarterly for GDP
growth, monthly for unemployment).

### Response format

By setting the `accept` header to `application/vnd.sdmx.data+json`, the API
returns data in a JSON structure with observations keyed by time period
【418303309353336†L292-L299】.  The parser in `update_data.py` flattens this
structure into a tidy DataFrame with columns `date`, `value` and `series_key`.

## Other data sources

Where ABS does not provide an indicator (e.g. bank tier‑1 capital ratios,
PISA scores or cybersecurity rankings), the repository uses other publicly
accessible APIs.  For example, Trading Economics offers a comprehensive
collection of macroeconomic indicators for each country【263059983294956†L8-L11】.
Other potential sources include:

* **Reserve Bank of Australia (RBA)** – financial aggregates and household debt.
* **OECD / PISA** – education outcomes and international comparisons.
* **CSIRO / AEMO** – energy production, renewable share and emissions data.
* **Department of Defence / DFAT** – defence expenditure, trade balances and
  export concentration.

For each of these sources the corresponding fetch function should handle
authentication (if required) and convert the response into a tidy time‑series
format.

## Traffic‑light calculation

Each indicator has a 2030 target defined in `scripts/dashboard.py`.  During
the dashboard runtime the latest available value is compared to this target.
For metrics where “higher is better” (e.g. GDP growth), the ratio of
current to target is computed; for “lower is better” metrics (e.g.
unemployment), the ratio of target to current is used.  The status is then
assigned as follows:

* **Green** – within 5 % of the target or better.
* **Amber** – within 20 % of the target.
* **Red** – more than 20 % away from the target.

These thresholds are deliberately simple and can be refined in future.

## Data storage and versioning

All retrieved series are stored as CSV files in the `data/` directory.  Each
file contains the raw observations and a column `target` with the 2030 target
for that metric.  The GitHub Actions workflow commits updated data files on
each scheduled run, providing a clear history of how each series evolves over
time.