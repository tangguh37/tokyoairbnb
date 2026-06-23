import os
import sys
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator

DEFAULT_ARGS = {
    "owner": "airbnb_analytics",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
DBT_DIR = os.path.join(PROJECT_ROOT, "dbt/airbnb")
PYTHON = sys.executable
DBT_CMD = f"cd {DBT_DIR} && {PYTHON} -m dbt"


def check_data_quality(**context):
    import duckdb
    db_path = os.path.join(PROJECT_ROOT, "data/tokyo_airbnb.duckdb")
    con = duckdb.connect(str(db_path))

    checks = [
        ("Listings with price > 0", f"SELECT COUNT(*) FROM main_marts.dim_listing WHERE price > 0"),
        ("Listings with reviews", f"SELECT COUNT(*) FROM main_marts.dim_listing WHERE number_of_reviews > 0"),
        ("Neighbourhoods", f"SELECT COUNT(DISTINCT neighbourhood) FROM main_marts.dim_listing"),
        ("Total reviews", f"SELECT COUNT(*) FROM main_marts.fct_reviews"),
        ("Calendar date range", f"SELECT MIN(calendar_date), MAX(calendar_date) FROM main_marts.fct_calendar"),
    ]

    results = []
    for name, query in checks:
        try:
            result = con.execute(query).fetchone()
            results.append({"check": name, "result": str(result), "status": "PASS"})
        except Exception as e:
            results.append({"check": name, "result": str(e), "status": "FAIL"})

    con.close()

    for r in results:
        print(f"  [{r['status']}] {r['check']}: {r['result']}")

    failures = [r for r in results if r["status"] == "FAIL"]
    if failures:
        raise ValueError(f"Data quality checks failed: {[f['check'] for f in failures]}")


with DAG(
    dag_id="airbnb_pipeline",
    default_args=DEFAULT_ARGS,
    description="Run dbt models and tests for Tokyo Airbnb analytics",
    schedule="0 * * * *",
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=["airbnb", "dbt"],
) as dag:

    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command=f"{DBT_CMD} run --profiles-dir .",
    )

    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command=f"{DBT_CMD} test --profiles-dir .",
    )

    quality_check = PythonOperator(
        task_id="quality_check",
        python_callable=check_data_quality,
    )

    dbt_docs = BashOperator(
        task_id="dbt_docs_generate",
        bash_command=f"{DBT_CMD} docs generate --profiles-dir .",
    )

    dbt_run >> dbt_test >> quality_check >> dbt_docs
