"""Main data ingestion orchestrator for Issue #13.

This module coordinates the complete data ingestion process:
1. Check if database needs initial setup (10 days of data)
2. Fetch Magnificent Seven stock data
3. Fetch USD/GBP currency conversion data
4. Store everything in SQL tables
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from .currency_fetcher import CurrencyDataFetcher
from .database_manager import DatabaseManager
from .nyse_fetcher import NYSEDataFetcher
from .airflow_manager import AirflowManager


class DataIngestionOrchestrator:
    """Main orchestrator for data ingestion operations."""

    def __init__(self):
        """Initialize the data ingestion orchestrator."""
        self.db_manager = DatabaseManager()
        self.airflow_manager = AirflowManager()
        self.nyse_fetcher = NYSEDataFetcher()
        self.currency_fetcher = CurrencyDataFetcher()
        self.logger = logging.getLogger(__name__)

    def perform_initial_setup(self, days_back: int = 10) -> dict[str, Any]:
        """Perform initial database setup with historical data.

        Args:
            days_back: Number of days of historical data to fetch

        Returns:
            Dictionary with setup results
        """
        self.logger.info(
            "Starting initial database setup with %d days of data", days_back
        )

        results: dict[str, Any] = {
            "setup_started": datetime.now().isoformat(),
            "days_requested": days_back,
            "stock_data": {},
            "currency_data": {},
            "total_records_inserted": 0,
            "errors": [],
        }

        try:
            # 1. Fetch stock data for Magnificent Seven
            self.logger.info("Fetching stock data for Magnificent Seven companies")
            stock_records = self.nyse_fetcher.fetch_and_prepare_all_data(days_back)

            if stock_records:
                stock_inserted = self.db_manager.insert_stock_data(stock_records)
                results["stock_data"] = {
                    "records_fetched": len(stock_records),
                    "records_inserted": stock_inserted,
                    "companies": self.nyse_fetcher.MAGNIFICENT_SEVEN,
                }
                results["total_records_inserted"] = (
                    results["total_records_inserted"] + stock_inserted
                )
                self.logger.info(
                    "Stock data setup complete: %d records inserted", stock_inserted
                )
            else:
                results["errors"].append("Failed to fetch stock data")
                self.logger.error("Failed to fetch any stock data")

            # 2. Fetch currency conversion data
            self.logger.info("Fetching USD/GBP currency conversion data")
            currency_records = self.currency_fetcher.fetch_and_prepare_fx_data(
                days_back
            )

            if currency_records:
                currency_inserted = self.db_manager.insert_currency_data(
                    currency_records
                )
                results["currency_data"] = {
                    "records_fetched": len(currency_records),
                    "records_inserted": currency_inserted,
                    "currency_pair": f"{self.currency_fetcher.FROM_CURRENCY}/{self.currency_fetcher.TO_CURRENCY}",
                }
                results["total_records_inserted"] = (
                    results["total_records_inserted"] + currency_inserted
                )
                self.logger.info(
                    "Currency data setup complete: %d records inserted",
                    currency_inserted,
                )
            else:
                results["errors"].append("Failed to fetch currency data")
                self.logger.error("Failed to fetch currency data")

            # 3. Final status
            results["setup_completed"] = datetime.now().isoformat()
            success_status = len(results["errors"]) == 0
            results["success"] = success_status

            if success_status:
                self.logger.info(
                    "Initial setup completed successfully: %d total records",
                    results["total_records_inserted"],
                )
            else:
                self.logger.warning(
                    "Initial setup completed with errors: %s", results["errors"]
                )

        except (ValueError, TypeError, AttributeError, RuntimeError) as e:
            results["errors"].append(f"Setup failed: {str(e)}")
            results["success"] = False
            self.logger.error("Initial setup failed: %s", str(e))

        return results

    def perform_daily_update(self) -> dict[str, Any]:
        """Perform daily data update for current/recent data.

        Returns:
            Dictionary with update results
        """
        self.logger.info("Starting daily data update")

        results: dict[str, Any] = {
            "update_started": datetime.now().isoformat(),
            "stock_updates": {},
            "currency_updates": {},
            "total_records_inserted": 0,
            "errors": [],
        }

        try:
            # 1. Update stock data (last 2-3 days to catch any missed data)
            self.logger.info("Updating stock data for Magnificent Seven")
            stock_records = self.nyse_fetcher.fetch_and_prepare_all_data(days_back=3)

            if stock_records:
                stock_inserted = self.db_manager.insert_stock_data(stock_records)
                results["stock_updates"] = {
                    "records_fetched": len(stock_records),
                    "records_inserted": stock_inserted,
                    "companies_updated": len({r["symbol"] for r in stock_records}),
                }
                results["total_records_inserted"] = (
                    results["total_records_inserted"] + stock_inserted
                )
                self.logger.info(
                    "Stock data update complete: %d new records", stock_inserted
                )

            # 2. Update currency data (last 2-3 days)
            self.logger.info("Updating USD/GBP currency data")
            currency_records = self.currency_fetcher.fetch_and_prepare_fx_data(
                days_back=3
            )

            if currency_records:
                currency_inserted = self.db_manager.insert_currency_data(
                    currency_records
                )
                results["currency_updates"] = {
                    "records_fetched": len(currency_records),
                    "records_inserted": currency_inserted,
                }
                results["total_records_inserted"] = (
                    results["total_records_inserted"] + currency_inserted
                )
                self.logger.info(
                    "Currency data update complete: %d new records", currency_inserted
                )

            # 3. Final status
            results["update_completed"] = datetime.now().isoformat()
            success_status = len(results["errors"]) == 0
            results["success"] = success_status

            self.logger.info(
                "Daily update completed: %d total new records",
                results["total_records_inserted"],
            )

        except (ValueError, TypeError, AttributeError, RuntimeError) as e:
            results["errors"].append(f"Daily update failed: {str(e)}")
            results["success"] = False
            self.logger.error("Daily update failed: %s", str(e))

        return results

    def run_full_ingestion(self) -> dict[str, Any]:
        """Run complete data ingestion process.

        This method:
        1. Checks if database is empty
        2. Performs initial setup if needed (10 days of data)
        3. Otherwise performs daily update

        Returns:
            Dictionary with complete ingestion results
        """
        self.logger.info("Starting full data ingestion process")

        # Check database status
        is_empty = self.db_manager.is_database_empty()
        db_health = self.db_manager.health_check()

        results: dict[str, Any] = {
            "ingestion_started": datetime.now().isoformat(),
            "database_status": db_health,
            "was_empty": is_empty,
            "operation_performed": None,
            "results": {},
            "success": False,
        }

        try:
            if is_empty:
                self.logger.info("Database is empty - performing initial setup")
                results["operation_performed"] = "initial_setup"
                results["results"] = self.perform_initial_setup(days_back=10)
            else:
                self.logger.info("Database has data - performing daily update")
                results["operation_performed"] = "daily_update"
                results["results"] = self.perform_daily_update()

            results["success"] = results["results"].get("success", False)
            results["ingestion_completed"] = datetime.now().isoformat()

            if results["success"]:
                self.logger.info("Full ingestion completed successfully")
            else:
                self.logger.warning("Full ingestion completed with errors")

        except (ValueError, TypeError, AttributeError, RuntimeError) as e:
            results["error"] = str(e)
            results["success"] = False
            self.logger.error("Full ingestion failed: %s", str(e))

        return results

    def get_ingestion_status(self) -> dict[str, Any]:
        """Get current status of data ingestion.

        Returns:
            Dictionary with current status information
        """
        try:
            db_health = self.db_manager.health_check()

            # Get Airflow status
            airflow_manager = AirflowManager()
            airflow_status = airflow_manager.get_airflow_status()

            # Check for any missing recent data (only if database is accessible)
            missing_data = {}
            if db_health.get("status") == "online":
                try:
                    for symbol in self.nyse_fetcher.MAGNIFICENT_SEVEN:
                        missing_dates = self.db_manager.get_missing_dates_for_symbol(
                            symbol, days_back=5
                        )
                        if missing_dates:
                            missing_data[symbol] = len(missing_dates)
                except Exception as e:
                    self.logger.warning("Could not check missing data: %s", str(e))

            return {
                "status_checked": datetime.now().isoformat(),
                "database_health": db_health,
                "airflow_status": airflow_status,
                "missing_recent_data": missing_data,
                "companies_tracked": self.nyse_fetcher.MAGNIFICENT_SEVEN,
                "currency_pair": f"{self.currency_fetcher.FROM_CURRENCY}/{self.currency_fetcher.TO_CURRENCY}",
            }

        except (ValueError, TypeError, AttributeError, RuntimeError) as e:
            return {
                "status_checked": datetime.now().isoformat(),
                "error": str(e),
                "success": False,
            }

    def perform_smart_initial_setup(self) -> dict[str, Any]:
        """Perform intelligent initial database setup using local data when available.

        Priority order:
        1. If real data exists in raw_data/stocks/ and raw_data/exchange/, use all of it
        2. If only dummy data exists, use one day from dummy data (for testing)
        3. If no data exists, fetch one day from API

        Returns:
            Dictionary with setup results
        """
        self.logger.info("Starting smart initial database setup")

        results: dict[str, Any] = {
            "setup_started": datetime.now().isoformat(),
            "data_source": None,
            "stock_data": {},
            "currency_data": {},
            "total_records_inserted": 0,
            "errors": [],
        }

        try:
            # Determine data source and strategy
            raw_data_path = Path("raw_data")
            real_stocks_path = raw_data_path / "stocks"
            real_exchange_path = raw_data_path / "exchange"
            dummy_stocks_path = raw_data_path / "dummy_stocks"
            dummy_exchange_path = raw_data_path / "dummy_exchange"

            # Check for real data
            has_real_stock_data = real_stocks_path.exists() and any(
                real_stocks_path.glob("*.json")
            )
            has_real_exchange_data = real_exchange_path.exists() and any(
                real_exchange_path.glob("*.json")
            )

            if has_real_stock_data and has_real_exchange_data:
                # Use all real data
                results["data_source"] = "real_local_data"
                self.logger.info("Using real data from raw_data/ directory")
                self._load_real_data(results, real_stocks_path, real_exchange_path)

            elif dummy_stocks_path.exists() and dummy_exchange_path.exists():
                # Use one day from dummy data
                results["data_source"] = "dummy_data_one_day"
                self.logger.info("Using one day from dummy data for testing")
                self._load_dummy_data_one_day(
                    results, dummy_stocks_path, dummy_exchange_path
                )

            else:
                # Fetch from API (minimal - just Apple + USD/GBP)
                results["data_source"] = "api_minimal"
                self.logger.info("No local data found, fetching minimal data from API")
                self._fetch_minimal_api_data(results)

        except Exception as e:
            results["errors"].append(f"Setup failed: {str(e)}")
            self.logger.error("Smart initial setup failed: %s", str(e))

        results["setup_completed"] = datetime.now().isoformat()
        results["success"] = len(results["errors"]) == 0
        return results

    def _load_real_data(
        self, results: dict[str, Any], stocks_path: Path, exchange_path: Path
    ) -> None:
        """Load all real data from local files."""
        # Load stock data
        stock_records = []
        for json_file in stocks_path.glob("*.json"):
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                records = self._parse_stock_json(data)
                stock_records.extend(records)

        if stock_records:
            stock_inserted = self.db_manager.insert_stock_data(stock_records)
            results["stock_data"] = {
                "records_inserted": stock_inserted,
                "source": "real_local_files",
            }
            results["total_records_inserted"] += stock_inserted

        # Load exchange data
        currency_records = []
        for json_file in exchange_path.glob("*.json"):
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                records = self._parse_currency_json(data)
                currency_records.extend(records)

        if currency_records:
            currency_inserted = self.db_manager.insert_currency_data(currency_records)
            results["currency_data"] = {
                "records_inserted": currency_inserted,
                "source": "real_local_files",
            }
            results["total_records_inserted"] += currency_inserted

    def _load_dummy_data_one_day(
        self, results: dict[str, Any], stocks_path: Path, exchange_path: Path
    ) -> None:
        """Load one day of data from dummy files (for testing)."""
        # Load one stock (Apple) - just the first day
        apple_file = stocks_path / "dummy_data_stock_AAPL.json"
        if apple_file.exists():
            with open(apple_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                records = self._parse_stock_json(data, limit_days=1)

                if records:
                    stock_inserted = self.db_manager.insert_stock_data(records)
                    results["stock_data"] = {
                        "records_inserted": stock_inserted,
                        "source": "dummy_data_one_day",
                        "symbol": "AAPL",
                    }
                    results["total_records_inserted"] += stock_inserted

        # Load one day of USD/GBP exchange data
        usdgbp_file = exchange_path / "dummy_data_fx_daily_USDGBP.json"
        if usdgbp_file.exists():
            with open(usdgbp_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                records = self._parse_currency_json(data, limit_days=1)

                if records:
                    currency_inserted = self.db_manager.insert_currency_data(records)
                    results["currency_data"] = {
                        "records_inserted": currency_inserted,
                        "source": "dummy_data_one_day",
                        "pair": "USD/GBP",
                    }
                    results["total_records_inserted"] += currency_inserted

    def _fetch_minimal_api_data(self, results: dict[str, Any]) -> None:
        """Fetch minimal data from API (Apple + USD/GBP for one day)."""
        # Fetch Apple stock data (1 day)
        aapl_df = self.nyse_fetcher.fetch_daily_data("AAPL", days_back=1)
        stock_records = []
        if aapl_df is not None and not aapl_df.empty:
            # Convert DataFrame to records format
            for _, row in aapl_df.iterrows():
                stock_records.append(
                    {
                        "symbol": "AAPL",
                        "data_date": row.get("date", datetime.now().date()),
                        "open_price": float(row.get("open", 0)),
                        "high_price": float(row.get("high", 0)),
                        "low_price": float(row.get("low", 0)),
                        "close_price": float(row.get("close", 0)),
                        "volume": int(row.get("volume", 0)),
                        "source": "api_minimal",
                        "created_at": datetime.now(),
                    }
                )

        if stock_records:
            stock_inserted = self.db_manager.insert_stock_data(stock_records)
            results["stock_data"] = {
                "records_inserted": stock_inserted,
                "source": "api_minimal",
                "symbol": "AAPL",
            }
            results["total_records_inserted"] += stock_inserted

        # Fetch USD/GBP exchange data (1 day)
        currency_records = self.currency_fetcher.fetch_and_prepare_fx_data(days_back=1)
        if currency_records:
            currency_inserted = self.db_manager.insert_currency_data(currency_records)
            results["currency_data"] = {
                "records_inserted": currency_inserted,
                "source": "api_minimal",
                "pair": "USD/GBP",
            }
            results["total_records_inserted"] += currency_inserted

    def _parse_stock_json(
        self, data: dict, limit_days: int | None = None
    ) -> list[dict]:
        """Parse stock JSON data into database records."""
        records = []
        symbol = data.get("Meta Data", {}).get("2. Symbol", "UNKNOWN")
        time_series = data.get("Time Series (Daily)", {})

        for date_str, values in list(time_series.items())[:limit_days]:
            records.append(
                {
                    "symbol": symbol,
                    "date": date_str,
                    "open_price": float(values["1. open"]),
                    "high_price": float(values["2. high"]),
                    "low_price": float(values["3. low"]),
                    "close_price": float(values["4. close"]),
                    "volume": int(values["5. volume"]),
                }
            )

        return records

    def _parse_currency_json(
        self, data: dict, limit_days: int | None = None
    ) -> list[dict]:
        """Parse currency JSON data into database records."""
        records = []
        meta_data = data.get("Meta Data", {})
        from_currency = meta_data.get("2. From Symbol", "USD")
        to_currency = meta_data.get("3. To Symbol", "GBP")
        time_series = data.get("Time Series (FX Daily)", {})

        for date_str, values in list(time_series.items())[:limit_days]:
            records.append(
                {
                    "from_currency": from_currency,
                    "to_currency": to_currency,
                    "date": date_str,
                    "open_rate": float(values["1. open"]),
                    "high_rate": float(values["2. high"]),
                    "low_rate": float(values["3. low"]),
                    "close_rate": float(values["4. close"]),
                }
            )

        return records

    def perform_schema_only_setup(self) -> dict[str, Any]:
        """Initialize database schema without loading any data.

        Returns:
            Dictionary with schema setup results
        """
        self.logger.info("Starting schema-only database setup")

        results: dict[str, Any] = {
            "setup_started": datetime.now().isoformat(),
            "setup_type": "schema_only",
            "schema_creation": {},
            "total_records_inserted": 0,
            "errors": [],
        }

        try:
            # Create database schema
            schema_results = self.db_manager.create_database_schema()
            results["schema_creation"] = schema_results

            if schema_results.get("success"):
                self.logger.info("Schema created successfully")
                results["success"] = True
            else:
                results["errors"].extend(schema_results.get("errors", []))
                self.logger.error("Schema creation failed")
                results["success"] = False

        except Exception as e:
            error_msg = f"Schema setup failed: {str(e)}"
            results["errors"].append(error_msg)
            results["success"] = False
            self.logger.error(error_msg)

        results["setup_completed"] = datetime.now().isoformat()
        return results

    def perform_database_teardown(self) -> dict[str, Any]:
        """Teardown database schema and all objects.

        Returns:
            Dictionary with teardown results
        """
        self.logger.info("Starting database teardown")

        results: dict[str, Any] = {
            "teardown_started": datetime.now().isoformat(),
            "teardown_type": "full_schema",
            "schema_teardown": {},
            "objects_dropped": 0,
            "errors": [],
        }

        try:
            # Teardown database schema
            teardown_results = self.db_manager.teardown_database_schema()
            results["schema_teardown"] = teardown_results

            if teardown_results.get("success"):
                objects_dropped = teardown_results.get("objects_dropped", [])
                results["objects_dropped"] = len(objects_dropped)
                self.logger.info(
                    "Database teardown completed successfully: %d objects dropped",
                    len(objects_dropped),
                )
                results["success"] = True
            else:
                results["errors"].extend(teardown_results.get("errors", []))
                self.logger.error("Database teardown failed")
                results["success"] = False

        except Exception as e:
            error_msg = f"Teardown failed: {str(e)}"
            results["errors"].append(error_msg)
            results["success"] = False
            self.logger.error(error_msg)

        results["teardown_completed"] = datetime.now().isoformat()
        return results

    def perform_airflow_setup(self) -> dict[str, Any]:
        """Setup Apache Airflow with database initialization, user creation, and service startup.

        Returns:
            Dictionary with Airflow setup results
        """
        self.logger.info("Starting Airflow setup")

        results: dict[str, Any] = {
            "setup_started": datetime.now().isoformat(),
            "setup_type": "airflow_complete",
            "airflow_setup": {},
            "services_started": [],
            "errors": [],
        }

        try:
            # Complete Airflow setup
            airflow_results = self.airflow_manager.setup_airflow_complete()
            results["airflow_setup"] = airflow_results

            if airflow_results.get("success"):
                operations = airflow_results.get("operations_completed", [])
                results["services_started"] = operations
                self.logger.info(
                    "Airflow setup completed successfully: %s", ", ".join(operations)
                )
                results["success"] = True
            else:
                results["errors"].extend(airflow_results.get("errors", []))
                self.logger.error("Airflow setup failed")
                results["success"] = False

        except Exception as e:
            error_msg = f"Airflow setup failed: {str(e)}"
            results["errors"].append(error_msg)
            results["success"] = False
            self.logger.error(error_msg)

        results["setup_completed"] = datetime.now().isoformat()
        return results

    def perform_airflow_teardown(self) -> dict[str, Any]:
        """Teardown Apache Airflow services.

        Returns:
            Dictionary with Airflow teardown results
        """
        self.logger.info("Starting Airflow teardown")

        results: dict[str, Any] = {
            "teardown_started": datetime.now().isoformat(),
            "teardown_type": "airflow_services",
            "airflow_teardown": {},
            "services_stopped": [],
            "errors": [],
        }

        try:
            # Teardown Airflow
            airflow_results = self.airflow_manager.teardown_airflow()
            results["airflow_teardown"] = airflow_results

            if airflow_results.get("success"):
                operations = airflow_results.get("operations_completed", [])
                results["services_stopped"] = operations
                self.logger.info(
                    "Airflow teardown completed successfully: %s", ", ".join(operations)
                )
                results["success"] = True
            else:
                results["errors"].extend(airflow_results.get("errors", []))
                self.logger.error("Airflow teardown failed")
                results["success"] = False

        except Exception as e:
            error_msg = f"Airflow teardown failed: {str(e)}"
            results["errors"].append(error_msg)
            results["success"] = False
            self.logger.error(error_msg)

        results["teardown_completed"] = datetime.now().isoformat()
        return results

    def get_airflow_status(self) -> dict[str, Any]:
        """Get current Airflow status and service information.

        Returns:
            Dictionary with Airflow status
        """
        self.logger.info("Checking Airflow status")

        try:
            status = self.airflow_manager.get_airflow_status()
            return {
                "status_checked": datetime.now().isoformat(),
                "airflow_status": status,
                "success": True,
            }
        except Exception as e:
            error_msg = f"Airflow status check failed: {str(e)}"
            self.logger.error(error_msg)
            return {
                "status_checked": datetime.now().isoformat(),
                "success": False,
                "error": error_msg,
            }
