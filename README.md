# Australia‑2030 Metrics Dashboard

This repository implements a **live, interactive dashboard** for tracking Australia’s economic, financial, social, human‑capital, productive‑capacity, environmental and security indicators between **2025 and 2030**.  The goal is to provide timely, up‑to‑date metrics alongside long‑term targets set by policy makers, so that progress can be monitored transparently and data‑driven decisions can be made.

## 📈 What Does the Dashboard Track?

The dashboard covers six broad categories and their associated indicators (each with a 2030 target):

| Category | Key metrics & 2030 targets | Notes |
| --- | --- | --- |
| **Macroeconomic** | • **Real GDP growth** (~3% by 2030)  • **Unemployment rate** (<5%)  • **Inflation (CPI)** (~2.5%)  • **Labour productivity growth** (+1.5%) | Headline economic indicators are available through the Australian Bureau of Statistics (ABS) Indicator API.  The ABS Indicator API provides headline economic statistics such as GDP growth, unemployment and CPI【263059983294956†L4-L6】. |
| **Financial/Systemic** | • **Household debt‑to‑income ratio** (~150%)  • **Housing affordability index** (<6× income)  • **Government net debt** (<30% of GDP)  • **Bank tier‑1 capital ratios** (>11%) | Data will be sourced from the Reserve Bank of Australia (RBA) and the Treasury.  Where possible, the Trading Economics API is used because it offers a comprehensive view of macroeconomic indicators for each country【263059983294956†L8-L11】. |
| **Societal** | • **Gini coefficient** (≤0.33)  • **Indigenous life expectancy gap** (<6 years)  • **PISA scores** (top quartile)  • **Trust in government** (>60%) | These indicators draw on the ABS, OECD/PISA datasets and surveys from the Australian Electoral Study. |
| **Human capital** | • **Labour force participation rate** (~67%)  • **Tertiary education attainment** (>40%)  • **Apprenticeship completion rate** (>65%) | Sourced from the ABS Labour Force and Education data and Department of Education statistics. |
| **Productive capacity** | • **R&D intensity (% of GDP)** (~2.5%)  • **Business entrant rate** (>12%)  • **Manufacturing share of GDP** (~8%)  • **Digital adoption by firms** (>60%) | Data from ABS, CSIRO and industry surveys. |
| **Infrastructure & environment** | • **Renewable energy share** (~80%)  • **Emissions reduction** (–43% vs 2005)  • **Infrastructure investment (% of GDP)** (2–3%)  • **Average commute time** (stabilise or reduce) | AEMO, CSIRO and state transport agencies provide the source data.  |
| **External & security** | • **Export market concentration (Herfindahl index)** (<0.20)  • **Defence spending (% of GDP)** (2.3–2.5%)  • **Cybersecurity ranking** (top 5 globally)  • **Current account balance** (±2% of GDP) | The Department of Defence, DFAT and OECD are used for these measures.  |

Each metric will display:

* The **current value** (fetched via APIs whenever possible).
* The **2030 target**.
* A **trend graph** showing historical series and forecasts (when available).
* A **traffic‑light indicator** (green/amber/red) based on progress toward the target.

## 🛠️ Implementation

This repository contains the following key components:

### Data retrieval (`scripts/update_data.py`)

The `update_data.py` script defines functions to fetch each indicator from reliable sources.  Where possible we use official APIs such as:

* **ABS Data API** – The ABS Data API (Beta) provides machine‑to‑machine access to ABS statistics.  It offers *data retrieval* (when you know the series ID, e.g. unemployment rate) and *data discovery* (to browse available datasets)【418303309353336†L186-L191】.  Data is requested via a `/data/{dataflowIdentifier}/{dataKey}` path with optional start and end periods【418303309353336†L195-L200】.
* **ABS Indicator API** – Provides headline economic statistics including GDP growth, unemployment and CPI【263059983294956†L4-L6】.
* **Trading Economics API** – Used for some financial indicators because it aggregates a wide range of macroeconomic data for each country【263059983294956†L8-L11】.
* **Other sources** – RBA statistics, OECD PISA scores, CSIRO energy data and AEMO renewables data.  API access credentials (when required) should be stored as environment variables in the GitHub repository’s secrets.

The script writes each indicator’s historical series to `data/` as a CSV or JSON file and logs metadata (source, last update time, etc.).  It is designed to be run on a schedule via GitHub Actions.

### Dashboard (`scripts/dashboard.py`)

The interactive dashboard is built with **Streamlit**, **Pandas** and **Plotly**.  When you run `streamlit run scripts/dashboard.py` locally or on Streamlit Cloud, the app will:

1. Read the latest data files from the `data/` directory.
2. Compute traffic light statuses based on each metric’s current value relative to its 2030 target.
3. Display a clean summary table and interactive charts for each category.
4. Offer options to download quarterly snapshots of the underlying data as CSV or PDF.

### Automation (GitHub Actions)

The repository includes a GitHub Actions workflow (`.github/workflows/update_data.yml`) that runs weekly to fetch new data.  It checks out the repository, installs Python dependencies, runs `update_data.py`, commits any updated data files and pushes them back to the repository.  Over time this builds a historical record of each series.

### File structure

```
.
├── README.md                # Project overview and setup instructions
├── requirements.txt         # Python dependencies
├── data/                    # Stored indicator series (CSV/JSON)
├── scripts/                 # Python scripts for data updating and dashboard
├── visualizations/          # Static images or pre-rendered graphs (optional)
├── docs/                    # Additional documentation and methodology notes
└── .github/
    └── workflows/
        └── update_data.yml  # GitHub Actions workflow for automatic updates
```

## 🚀 Getting started

1. **Clone this repository** and install Python dependencies:

   ```bash
   git clone https://github.com/your‑username/australia‑2030‑metrics‑dashboard.git
   cd australia‑2030‑metrics‑dashboard
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Run the dashboard locally**:

   ```bash
   streamlit run scripts/dashboard.py
   ```

   The app will read data from the `data/` folder.  If no data is present, it will show placeholder values until `update_data.py` is executed.

3. **Updating data manually**:

   ```bash
   python scripts/update_data.py
   ```

   This script fetches the latest values from the APIs and saves them to `data/`.

4. **Automation via GitHub Actions**:  The repository includes a workflow that runs on a weekly schedule.  For this to work you must set any required API keys (e.g., Trading Economics, OECD) as encrypted secrets in the GitHub repository (via the Settings → Secrets page).

## 🤝 Contributing

Contributions are welcome!  To add new metrics, update existing sources or improve the visualizations, please submit a pull request.  See `docs/methodology.md` for guidance on how to select appropriate data sources and how to maintain data quality.

## 📄 License

This project is released under the MIT License.  See the `LICENSE` file for details.