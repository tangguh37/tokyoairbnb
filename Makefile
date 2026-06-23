.PHONY: setup download ingest dbt-run dbt-test dbt-docs dbt-docs-serve airflow dashboard clean all

export PATH := $(HOME)/.local/bin:$(PATH)

DBT_DIR = dbt/airbnb
DATA_DIR = data

setup:
	pip3 install --user --break-system-packages -r requirements.txt
	pip3 install --user --break-system-packages -r airflow/requirements.txt
	mkdir -p $(DATA_DIR)
	cp -n .env.example .env 2>/dev/null || true
	@echo "Setup complete. Run 'make download' to fetch data."

download:
	python3 scripts/download_data.py

ingest:
	python3 scripts/ingest_to_duckdb.py

dbt-run:
	cd $(DBT_DIR) && dbt run --profiles-dir .

dbt-test:
	cd $(DBT_DIR) && dbt test --profiles-dir .

dbt-docs:
	cd $(DBT_DIR) && dbt docs generate --profiles-dir .

dbt-docs-serve:
	cd $(DBT_DIR) && dbt docs serve --profiles-dir .

dbt-freshness:
	cd $(DBT_DIR) && dbt source freshness --profiles-dir .

airflow:
	mkdir -p airflow/logs
	export AIRFLOW_HOME=$(shell pwd)/airflow && \
	$$AIRFLOW_HOME/start.sh 2>/dev/null || \
	(airflow db init && \
	airflow users create --username admin --firstname Admin --lastname User --role Admin --email admin@example.com --password admin 2>/dev/null || true && \
	AIRFLOW_HOME=$(shell pwd)/airflow airflow standalone)

dashboard:
	streamlit run dashboard/app.py

clean:
	rm -rf $(DATA_DIR) airflow/airflow.db airflow/webserver_config.py airflow/logs 2>/dev/null || true
	@echo "Cleaned data, airflow db. Re-run 'make download' to refresh."

all: setup download ingest dbt-run dbt-test dbt-docs
	@echo ""
	@echo "========================================="
	@echo " All done! Start the dashboard with:"
	@echo "   make dashboard"
	@echo " Or generate dbt docs with:"
	@echo "   make dbt-docs-serve"
	@echo "========================================="
