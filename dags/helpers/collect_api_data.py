"""
Step 2: Collect API records - write to JSON raw_data.
"""

import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root / "src"))

from ticker_converter.data_ingestion.orchestrator import DataIngestionOrchestrator


def collect_api_data():
    """Collect API records and write to JSON raw_data."""
    print("🌐 Collecting data from APIs...")
    
    # Debug: print current working directory
    import os
    print(f"🔍 Current working directory: {os.getcwd()}")
    print(f"🔍 Project root: {project_root}")

    # Ensure directories exist
    raw_stocks_dir = project_root / "dags" / "raw_data" / "stocks"
    raw_exchange_dir = project_root / "dags" / "raw_data" / "exchange"

    raw_stocks_dir.mkdir(parents=True, exist_ok=True)
    raw_exchange_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Use the orchestrator to collect data
        orchestrator = DataIngestionOrchestrator()

        # Determine days_back (default to 10)
        days_back = 10

        # Extract stock data
        print("📈 Extracting stock data...")
        stock_records = orchestrator.nyse_fetcher.fetch_and_prepare_all_data(days_back)
        print(f"✅ Stock records prepared: {len(stock_records)}")

        # Extract exchange data
        print("💱 Extracting exchange rate data...")
        exchange_records = orchestrator.extract_exchange_rates(days_back)
        print(f"✅ Exchange records prepared: {len(exchange_records)}")

        # Write JSON files to raw_data directories (atomic write)
        import json
        from datetime import datetime

        ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        stock_file = raw_stocks_dir / f"stocks_{ts}.json"
        exchange_file = raw_exchange_dir / f"exchange_{ts}.json"

        # Write temp then rename for atomicity
        tmp_stock = stock_file.with_suffix(".tmp")
        tmp_exchange = exchange_file.with_suffix(".tmp")

        with open(tmp_stock, "w", encoding="utf-8") as f:
            json.dump(stock_records, f, indent=2, default=str)
        tmp_stock.replace(stock_file)

        with open(tmp_exchange, "w", encoding="utf-8") as f:
            json.dump(exchange_records, f, indent=2, default=str)
        tmp_exchange.replace(exchange_file)

        return {"stock_extraction": str(stock_file), "exchange_extraction": str(exchange_file)}

    except Exception as e:
        print(f"❌ API collection failed: {e}")
        # Raise the exception so Airflow marks the task as failed
        raise RuntimeError(f"API collection failed: {e}") from e
