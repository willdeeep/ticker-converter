"""
Step 2: Collect API records - write to JSON raw_data.
"""

import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root / "src"))

from ticker_converter.data_ingestion.orchestrator import DataIngestionOrchestrator


def collect_api_data(**context):
    """Collect API records and write to JSON raw_data."""
    print("🌐 Collecting data from APIs...")

    # Ensure directories exist
    raw_stocks_dir = project_root / "dags" / "raw_data" / "stocks"
    raw_exchange_dir = project_root / "dags" / "raw_data" / "exchange"

    raw_stocks_dir.mkdir(parents=True, exist_ok=True)
    raw_exchange_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Use the orchestrator to collect data
        orchestrator = DataIngestionOrchestrator()

        # Extract stock data
        print("📈 Extracting stock data...")
        stock_result = orchestrator.extract_stock_data()
        print(f"✅ Stock extraction: {stock_result}")

        # Extract exchange data
        print("💱 Extracting exchange rate data...")
        exchange_result = orchestrator.extract_exchange_rates()
        print(f"✅ Exchange extraction: {exchange_result}")

        return {"stock_extraction": str(stock_result), "exchange_extraction": str(exchange_result)}

    except Exception as e:
        print(f"❌ API collection failed: {e}")
        return {"stock_extraction": f"failed: {e}", "exchange_extraction": f"failed: {e}"}
