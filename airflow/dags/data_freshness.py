import os
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.sensors.time_delta import TimeDeltaSensor

DEFAULT_ARGS = {
    "owner": "airbnb_analytics",
    "depends_on_past": False,
    "email_on_failure": True,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
DBT_DIR = os.path.join(PROJECT_ROOT, "dbt/airbnb")
VENV_PYTHON = os.path.join(PROJECT_ROOT, ".venv/bin/python")
DBT_CMD = f"cd {DBT_DIR} && {VENV_PYTHON} -m dbt"


def report_freshness():
    import json
    import duckdb

    db_path = os.path.join(PROJECT_ROOT, "data/tokyo_airbnb.duckdb")
    con = duckdb.connect(str(db_path))

    freshness_checks = [
        ("Listings (last_scraped)", "SELECT MAX(last_scraped_date) FROM main.marts_dim_listing"),
        ("Reviews (most recent)", "SELECT MAX(review_date) FROM main.marts_fct_reviews"),
        ("Calendar (latest date)", "SELECT MAX(calendar_date) FROM main.marts_fct_calendar"),
    ]

    all_fresh = True
    for name, query in freshness_checks:
        result = con.execute(query).fetchone()[0]
        days_ago = (datetime.now().date() - result).days if result else 999
        status = "OK" if days_ago < 365 else "STALE"
        print(f"  [{status}] {name}: {result} ({days_ago} days ago)")
        if status == "STALE":
            all_fresh = False

    con.close()

    if not all_fresh:
        print("WARNING: Some data sources are stale!")


with DAG(
    dag_id="data_freshness",
    default_args=DEFAULT_ARGS,
    description="Monitor freshness of Airbnb data sources",
    schedule="0 6 * * *",
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=["airbnb", "monitoring"],
) as dag:

    freshness_check = PythonOperator(
        task_id="freshness_check",
        python_callable=report_freshness,
    )

    dbt_source_freshness = BashOperator(
        task_id="dbt_source_freshness",
        bash_command=f"{DBT_CMD} source freshness --profiles-dir .",
    )

    freshness_check >> dbt_source_freshness
