"""Main data ingestion orchestrator for Issue #13.

This module coordinates the complete data ingestion process:
1. Check if database needs initial setup (10 days of data)
2. Fetch Magnificent Seven stock data
3. Fetch USD/GBP currency conversion data
4. Store everything in SQL tables
"""

import logging
from datetime import datetime
from typing import Any

from .currency_fetcher import CurrencyDataFetcher
from .database_manager import DatabaseManager
from .nyse_fetcher import NYSEDataFetcher


class DataIngestionOrchestrator:
    """Main orchestrator for data ingestion operations."""

    def __init__(
        self,
        db_manager: DatabaseManager | None = None,
        nyse_fetcher: NYSEDataFetcher | None = None,
        currency_fetcher: CurrencyDataFetcher | None = None,
    ) -> None:
        """Initialize the data ingestion orchestrator.

        Args:
            db_manager: Database manager instance
            nyse_fetcher: NYSE data fetcher instance
            currency_fetcher: Currency data fetcher instance
        """
        self.db_manager = db_manager or DatabaseManager()
        self.nyse_fetcher = nyse_fetcher or NYSEDataFetcher()
        self.currency_fetcher = currency_fetcher or CurrencyDataFetcher()
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

        results = self._create_base_result(days_back)

        try:
            # Fetch and insert stock data
            stock_result = self._process_stock_data(days_back)
            results.update(stock_result)

            # Fetch and insert currency data
            currency_result = self._process_currency_data(days_back)
            results.update(currency_result)

            results["setup_completed"] = datetime.now().isoformat()
            self.logger.info(
                "Initial setup completed. Total records: %d", results['total_records_inserted']
            )

        except Exception as e:
            self.logger.error("Unexpected error during initial setup: %s", e)
            results["errors"].append(f"Unexpected error: {e}")

        return results

    def _create_base_result(self, days_back: int) -> dict[str, Any]:
        """Create base result dictionary.

        Args:
            days_back: Number of days requested

        Returns:
            Base result dictionary
        """
        return {
            "setup_started": datetime.now().isoformat(),
            "days_requested": days_back,
            "stock_data": {},
            "currency_data": {},
            "total_records_inserted": 0,
            "errors": [],
        }

    def _process_stock_data(self, days_back: int) -> dict[str, Any]:
        """Process stock data fetching and insertion.

        Args:
            days_back: Number of days to fetch

        Returns:
            Dictionary with stock processing results
        """
        self.logger.info("Fetching stock data for Magnificent Seven companies")

        stock_records = self.nyse_fetcher.fetch_and_prepare_all_data(days_back)
        if not stock_records:
            error_msg = "Failed to fetch stock data"
            self.logger.error(error_msg)
            return {"errors": [error_msg], "total_records_inserted": 0}

        stock_inserted = self.db_manager.insert_stock_data(stock_records)
        self.logger.info(
            "Stock data setup complete: %d records inserted", stock_inserted
        )

        return {
            "stock_data": {
                "records_fetched": len(stock_records),
                "records_inserted": stock_inserted,
                "companies": self.nyse_fetcher.MAGNIFICENT_SEVEN,
            },
            "total_records_inserted": stock_inserted,
        }

    def _process_currency_data(self, days_back: int) -> dict[str, Any]:
        """Process currency data fetching and insertion.

        Args:
            days_back: Number of days to fetch

        Returns:
            Dictionary with currency processing results
        """
        self.logger.info("Fetching USD/GBP currency conversion data")

        currency_records = self.currency_fetcher.fetch_and_prepare_fx_data(days_back)
        if not currency_records:
            error_msg = "Failed to fetch currency data"
            self.logger.error(error_msg)
            return {"errors": [error_msg]}

        currency_inserted = self.db_manager.insert_currency_data(currency_records)
        self.logger.info(
            "Currency data setup complete: %d records inserted", currency_inserted
        )

        return {
            "currency_data": {
                "records_fetched": len(currency_records),
                "records_inserted": currency_inserted,
                "currency_pair": f"{self.currency_fetcher.FROM_CURRENCY}/{self.currency_fetcher.TO_CURRENCY}",
            },
            "total_records_inserted": currency_inserted,
        }

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

            # Get data freshness information
            stock_freshness = self.nyse_fetcher.check_data_freshness()
            currency_freshness = self.currency_fetcher.get_latest_available_rate()

            # Check for any missing recent data
            missing_data = {}
            for symbol in self.nyse_fetcher.MAGNIFICENT_SEVEN:
                missing_dates = self.db_manager.get_missing_dates_for_symbol(
                    symbol, days_back=5
                )
                if missing_dates:
                    missing_data[symbol] = len(missing_dates)

            return {
                "status_checked": datetime.now().isoformat(),
                "database_health": db_health,
                "stock_data_freshness": {
                    symbol: date.isoformat() if date else None
                    for symbol, date in stock_freshness.items()
                },
                "currency_data_freshness": (
                    {
                        "date": (
                            currency_freshness[0].isoformat()
                            if currency_freshness and len(currency_freshness) > 0
                            else None
                        ),
                        "rate": (
                            currency_freshness[1]
                            if currency_freshness and len(currency_freshness) > 1
                            else None
                        ),
                    }
                    if currency_freshness
                    else None
                ),
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
