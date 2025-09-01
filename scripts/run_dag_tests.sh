#!/bin/bash
# Manual DAG Execution Integration Test Runner
# This script runs the DAG execution integration tests independently

set -e

echo "🚀 DAG Execution Integration Test Runner"
echo "========================================"

# Check if we're in the right directory
if [ ! -f "pytest.ini" ]; then
    echo "❌ Error: Must be run from project root directory"
    exit 1
fi

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  Warning: Virtual environment not detected. Attempting to activate..."
    if [ -f ".venv/bin/activate" ]; then
        source .venv/bin/activate
        echo "✅ Virtual environment activated"
    else
        echo "❌ Error: Virtual environment not found. Please activate manually."
        exit 1
    fi
fi

# Verify Airflow is available
echo "🔍 Checking Airflow availability..."
if ! command -v airflow &> /dev/null; then
    echo "❌ Error: Airflow CLI not available. Please ensure Airflow is installed and in PATH."
    exit 1
fi

# Check Airflow version
AIRFLOW_VERSION=$(airflow version 2>/dev/null || echo "unknown")
echo "📋 Airflow version: $AIRFLOW_VERSION"

# Check if Airflow is configured
if [ -z "$AIRFLOW__CORE__DAGS_FOLDER" ]; then
    echo "⚠️  Warning: AIRFLOW__CORE__DAGS_FOLDER not set. Checking .env..."
    if [ -f ".env" ]; then
        source .env
        echo "✅ Environment variables loaded from .env"
    else
        echo "❌ Error: AIRFLOW__CORE__DAGS_FOLDER not configured and no .env file found"
        exit 1
    fi
fi

echo "📁 DAGs folder: $AIRFLOW__CORE__DAGS_FOLDER"

# Initialize Airflow database if needed
echo "🗄️  Ensuring Airflow database is initialized..."
airflow db init > /dev/null 2>&1 || echo "ℹ️  Database already initialized"

# Check if test_etl_dag is available
echo "🔍 Checking for test_etl_dag..."
if airflow dags list 2>/dev/null | grep -q "test_etl_dag"; then
    echo "✅ test_etl_dag found and loaded"
else
    echo "⚠️  test_etl_dag not found in DAG list. This may be normal for a fresh setup."
    echo "🔄 Attempting to refresh DAGs..."
    airflow dags reserialize > /dev/null 2>&1 || echo "ℹ️  DAG refresh completed"
fi

# Run the DAG execution integration tests
echo ""
echo "🧪 Running DAG Execution Integration Tests..."
echo "============================================="

# Run only the DAG execution integration tests
pytest -v -s \
    --tb=short \
    --disable-warnings \
    -m "integration" \
    tests/integration/test_dag_execution_integration.py \
    "$@"

PYTEST_EXIT_CODE=$?

echo ""
echo "📊 Test Results Summary"
echo "======================"

if [ $PYTEST_EXIT_CODE -eq 0 ]; then
    echo "✅ All DAG execution tests passed!"
    echo "🎉 DAG integration testing successful"
elif [ $PYTEST_EXIT_CODE -eq 5 ]; then
    echo "⏭️  Tests were skipped (likely due to Airflow not being available)"
    echo "ℹ️  This is expected if Airflow is not running or not fully configured"
else
    echo "❌ Some tests failed or encountered errors"
    echo "🔍 Check the output above for details"
fi

echo ""
echo "💡 Tips:"
echo "   • To run a specific test: $0 -k test_name"
echo "   • To see more details: $0 -vv"
echo "   • To run all integration tests: pytest -m integration"

exit $PYTEST_EXIT_CODE
