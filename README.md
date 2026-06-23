# Tokyo Airbnb Analytics

End-to-end data analytics pipeline for Tokyo Airbnb listings using **dbt**, **DuckDB**, **Airflow**, and **Streamlit**.

## Architecture

```
Inside Airbnb (Tokyo, Sept 2025)
        ↓
  scripts/download_data.py
        ↓
  DuckDB (raw tables)
        ↓
  dbt-duckdb (staging → intermediate → marts)
        ↓
  DuckDB (analytics marts)
        ↓
  Streamlit dashboard
        ↑
  Airflow orchestrates
```

## Project Structure

```
tokyoairbnb/
├── scripts/
│   ├── download_data.py          # Download Tokyo CSVs from Inside Airbnb
│   └── ingest_to_duckdb.py       # Load CSVs into DuckDB
├── dbt/airbnb/
│   ├── dbt_project.yml
│   ├── profiles.yml
│   └── models/
│       ├── sources.yml           # Source definitions + freshness
│       ├── staging/              # Clean & type raw data
│       ├── intermediate/         # Business logic & joins
│       └── marts/                # Star schema (dim + fact + aggregates)
├── airflow/dags/
│   ├── airbnb_pipeline.py        # dbt run → test → quality check
│   └── data_freshness.py         # Source freshness monitoring
├── dashboard/
│   └── app.py                    # Streamlit dashboard
├── Makefile                      # One-command setup & run
└── requirements.txt
```

## Quick Start

```bash
# 1. Setup environment
make setup

# 2. Download Airbnb data
make download

# 3. Load into DuckDB
make ingest

# 4. Run dbt transformations
make dbt-run

# 5. Run dbt tests
make dbt-test

# 6. Launch dashboard
make dashboard

# 7. (Optional) Start Airflow
make airflow
```

## Data Model

### Star Schema

| Layer | Table | Type |
|-------|-------|------|
| Source | `raw_listings`, `raw_reviews`, `raw_calendar`, `raw_neighbourhoods` | Raw CSV |
| Staging | `stg_listings`, `stg_reviews`, `stg_calendar` | View |
| Intermediate | `int_listings_enriched`, `int_host_metrics` | View |
| Dimension | `dim_listing`, `dim_host`, `dim_neighbourhood` | Table |
| Fact | `fct_reviews` (incremental), `fct_calendar` (incremental) | Incremental |
| Aggregate | `monthly_occupancy`, `pricing_analysis` | Table |

### dbt Features Used

- Source freshness checks
- Generic tests (not_null, unique, accepted_range)
- Singular tests (custom SQL assertions)
- Incremental models (append strategy for reviews & calendar)
- Exposures (linking to Streamlit dashboard)
- Auto-generated documentation (`make dbt-docs`)

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Storage | DuckDB |
| Transformation | dbt-core + dbt-duckdb |
| Orchestration | Apache Airflow |
| Dashboard | Streamlit + Plotly |
| Data Source | Inside Airbnb |
| Language | Python 3 |

## License

Data licensed under Creative Commons Attribution 4.0 International License by Inside Airbnb.
Project code is MIT.
