#!/bin/bash
# Airflow configuration for ticker-converter project
export AIRFLOW__CORE__DAGS_FOLDER="/Users/willhuntleyclarke/repos/interests/ticker-converter/dags"
export AIRFLOW__CORE__LOAD_EXAMPLES=False
export AIRFLOW__WEBSERVER__EXPOSE_CONFIG=True

echo "✅ Airflow configured for ticker-converter project"
echo "📁 DAGs folder: $AIRFLOW__CORE__DAGS_FOLDER"
echo "🚀 Run 'airflow dags list' to see project DAGs"
