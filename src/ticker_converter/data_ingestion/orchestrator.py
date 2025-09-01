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

from ..exceptions import (
    APIConnectionException,
    APIRateLimitException,
    DatabaseConnectionException,
    DatabaseOperationException,
    DataIngestionException,
)
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
        self.logger.info("Starting initial database setup with %d days of data", days_back)

        results = self._create_base_result(days_back)

        try:
            # Fetch and insert stock data
            stock_result = self._process_stock_data(days_back)
            results.update(stock_result)

            # Fetch and insert currency data
            currency_result = self._process_currency_data(days_back)
            # Merge currency results without overwriting total_records_inserted
            for key, value in currency_result.items():
                if key == "total_records_inserted":
                    # Accumulate total records instead of overwriting
                    results[key] = results.get(key, 0) + value
                else:
                    results[key] = value

            results["setup_completed"] = datetime.now().isoformat()
            results["end_time"] = results["setup_completed"]  # Set end time for test compatibility
            self.logger.info(
                "Initial setup completed. Total records: %d",
                results["total_records_inserted"],
            )

        except (APIConnectionException, APIRateLimitException) as e:
            # API-related errors should fail the ingestion
            self.logger.error("API error during initial setup: %s", e)
            results["errors"].append(f"API error: {e}")
            results["success"] = False
            results["end_time"] = datetime.now().isoformat()
            raise DataIngestionException(f"Initial setup failed due to API error: {e}") from e
        except (DatabaseConnectionException, DatabaseOperationException) as e:
            # Database errors should fail the ingestion
            self.logger.error("Database error during initial setup: %s", e)
            results["errors"].append(f"Database error: {e}")
            results["success"] = False
            results["end_time"] = datetime.now().isoformat()
            raise DataIngestionException(f"Initial setup failed due to database error: {e}") from e
        except (ValueError, TypeError, AttributeError) as e:
            # Data processing errors
            self.logger.error("Data processing error during initial setup: %s", e)
            results["errors"].append(f"Data processing error: {e}")
            results["success"] = False
            results["end_time"] = datetime.now().isoformat()
        except Exception as e:
            # Only catch truly unexpected exceptions
            self.logger.error("Unexpected error during initial setup: %s", e)
            results["errors"].append("Unexpected error: %s" % str(e))  # pylint: disable=consider-using-f-string
            results["success"] = False
            results["end_time"] = datetime.now().isoformat()

        return results

    def _create_base_result(self, days_back: int) -> dict[str, Any]:
        """Create base result dictionary.

        Args:
            days_back: Number of days requested

        Returns:
            Base result dictionary
        """
        start_time = datetime.now().isoformat()
        return {
            "operation": "initial_setup",
            "success": True,
            "start_time": start_time,
            "end_time": None,  # Will be updated when operation completes
            "setup_started": start_time,  # Keep for backward compatibility
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

        stock_records = self.nyse_fetcher.fetch_and_prepare_all_data(days_back=days_back)
        if not stock_records:
            error_msg = "Failed to fetch stock data"
            self.logger.error(error_msg)
            return {"errors": [error_msg], "total_records_inserted": 0}

        stock_inserted = self.db_manager.insert_stock_data(stock_records)
        self.logger.info("Stock data setup complete: %d records inserted", stock_inserted)

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

        currency_records = self.currency_fetcher.fetch_and_prepare_fx_data(days_back=days_back)
        if not currency_records:
            error_msg = "Failed to fetch currency data"
            self.logger.error(error_msg)
            return {"errors": [error_msg]}

        currency_inserted = self.db_manager.insert_currency_data(currency_records)
        self.logger.info("Currency data setup complete: %d records inserted", currency_inserted)

        return {
            "currency_data": {
                "records_fetched": len(currency_records),
                "records_inserted": currency_inserted,
                "currency_pair": "%s/%s"
                % (
                    self.currency_fetcher.FROM_CURRENCY,
                    self.currency_fetcher.TO_CURRENCY,
                ),  # pylint: disable=consider-using-f-string
            },
            "total_records_inserted": currency_inserted,
        }

    def perform_daily_update(self, days_back: int = 3) -> dict[str, Any]:
        """Perform daily data update for current/recent data.

        Args:
            days_back: Number of days back to fetch (default 3 for safety)

        Returns:
            Dictionary with update results
        """
        self.logger.info("Starting daily data update with %d days back", days_back)

        results: dict[str, Any] = {
            "operation": "daily_update",
            "success": True,
            "update_started": datetime.now().isoformat(),
            "stock_updates": {},
            "currency_updates": {},
            "total_records_inserted": 0,
            "errors": [],
        }

        try:
            # 1. Update stock data (using configurable days_back parameter)
            self.logger.info("Updating stock data for Magnificent Seven")
            stock_records = self.nyse_fetcher.fetch_and_prepare_all_data(days_back=days_back)

            if stock_records:
                stock_inserted = self.db_manager.insert_stock_data(stock_records)
                results["stock_updates"] = {
                    "records_fetched": len(stock_records),
                    "records_inserted": stock_inserted,
                    "companies_updated": len({r["symbol"] for r in stock_records}),
                }
                results["total_records_inserted"] = results["total_records_inserted"] + stock_inserted
                self.logger.info("Stock data update complete: %d new records", stock_inserted)

            # 2. Update currency data (using configurable days_back parameter)
            self.logger.info("Updating USD/GBP currency data")
            currency_records = self.currency_fetcher.fetch_and_prepare_fx_data(days_back=days_back)

            if currency_records:
                currency_inserted = self.db_manager.insert_currency_data(currency_records)
                results["currency_updates"] = {
                    "records_fetched": len(currency_records),
                    "records_inserted": currency_inserted,
                }
                results["total_records_inserted"] = results["total_records_inserted"] + currency_inserted
                self.logger.info("Currency data update complete: %d new records", currency_inserted)

            # 3. Final status
            results["update_completed"] = datetime.now().isoformat()
            success_status = len(results["errors"]) == 0
            results["success"] = success_status

            self.logger.info(
                "Daily update completed: %d total new records",
                results["total_records_inserted"],
            )

        except (ValueError, TypeError, AttributeError, RuntimeError) as e:
            results["errors"].append(f"Daily update failed: {e}")
            results["success"] = False
            self.logger.error("Daily update failed: %s", str(e))

        return results

    def run_full_ingestion(self, days_back: int = 10) -> dict[str, Any]:
        """Run complete data ingestion process.

        This method:
        1. Checks if database is empty
        2. Performs initial setup if needed (with specified days of data)
        3. Otherwise performs daily update

        Args:
            days_back: Number of days of historical data for initial setup (default 10)

        Returns:
            Dictionary with complete ingestion results
        """
        self.logger.info("Starting full data ingestion process with %d days back", days_back)

        results: dict[str, Any] = {
            "ingestion_started": datetime.now().isoformat(),
            "database_status": None,
            "was_empty": None,
            "operation_performed": None,
            "results": {},
            "success": False,
            "total_records_inserted": 0,
        }

        try:
            # Check database status - moved inside try block to handle connection failures
            is_empty = self.db_manager.is_database_empty()
            db_health = self.db_manager.health_check()

            # Update results with database status
            results["database_status"] = db_health
            results["was_empty"] = is_empty

            if is_empty:
                self.logger.info("Database is empty - performing initial setup")
                results["operation_performed"] = "initial_setup"
                results["results"] = self.perform_initial_setup(days_back=days_back)
            else:
                self.logger.info("Database has data - performing daily update")
                results["operation_performed"] = "daily_update"
                results["results"] = self.perform_daily_update()

            results["success"] = results["results"].get("success", False)
            results["total_records_inserted"] = results["results"].get("total_records_inserted", 0)
            results["ingestion_completed"] = datetime.now().isoformat()

            if results["success"]:
                self.logger.info("Full ingestion completed successfully")
            else:
                self.logger.warning("Full ingestion completed with errors")

        except (ValueError, TypeError, AttributeError, RuntimeError) as e:
            results["error"] = str(e)
            results["success"] = False
            self.logger.error("Full ingestion failed: %s", str(e))
        except (APIConnectionException, APIRateLimitException) as e:
            # API-related errors should provide specific context
            results["error"] = f"API error: {e}"
            results["success"] = False
            self.logger.error("API error during full ingestion: %s", str(e))
        except (DatabaseConnectionException, DatabaseOperationException) as e:
            # Database errors should provide specific context
            results["error"] = f"Database error: {e}"
            results["success"] = False
            self.logger.error("Database error during full ingestion: %s", str(e))
        except Exception as e:
            # Handle any truly unexpected exceptions
            results["error"] = f"Unexpected error during ingestion: {e}"
            results["success"] = False
            self.logger.error("Unexpected error during full ingestion: %s", str(e))

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
                missing_dates = self.db_manager.get_missing_dates_for_symbol(symbol, days_back=5)
                if missing_dates:
                    missing_data[symbol] = len(missing_dates)

            return {
                "status_checked": datetime.now().isoformat(),
                "database_health": db_health,
                "stock_data_freshness": {
                    symbol: date.isoformat() if date else None for symbol, date in stock_freshness.items()
                },
                "currency_data_freshness": (
                    {
                        "date": (
                            currency_freshness[0].isoformat()
                            if currency_freshness and len(currency_freshness) > 0
                            else None
                        ),
                        "rate": (currency_freshness[1] if currency_freshness and len(currency_freshness) > 1 else None),
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

    def extract_exchange_rates(self, days_back: int = 1) -> list[dict[str, Any]]:
        """Extract exchange rates for the given number of days.

        Args:
            days_back: Number of days to fetch exchange rates for

        Returns:
            List of dictionaries containing exchange rate data
        """
        self.logger.info("Extracting exchange rates for the past %d days", days_back)

        try:
            # Fetch exchange rate data using the currency fetcher
            exchange_rate_data = self.currency_fetcher.fetch_and_prepare_fx_data(days_back=days_back)

            if not exchange_rate_data:
                self.logger.warning("No exchange rate data found for the past %d days", days_back)
                return []

            self.logger.info("Successfully extracted %d exchange rate records", len(exchange_rate_data))
            return exchange_rate_data

        except (APIConnectionException, APIRateLimitException) as e:
            self.logger.error("API error extracting exchange rates: %s", str(e))
            raise DataIngestionException(f"Failed to extract exchange rates due to API error: {e}") from e
        except (ValueError, TypeError, AttributeError) as e:
            self.logger.error("Data processing error extracting exchange rates: %s", str(e))
            return []  # Return empty list for data processing errors
        except Exception as e:
            self.logger.error("Unexpected error extracting exchange rates: %s", str(e))
            raise

    def check_data_status(self) -> dict[str, Any]:
        """Check the current status of data in the system.

        Returns:
            Dictionary with comprehensive data status information
        """
        self.logger.info("Checking data status")

        status_result: dict[str, Any] = {
            "status_checked": datetime.now().isoformat(),
            "data_freshness": {},
            "current_exchange_rate": None,
            "missing_recent_data": [],
            "companies_tracked": [],
            "currency_pair": None,
            "database_health": None,
            "errors": [],
        }

        try:
            # Check database health
            status_result["database_health"] = self.db_manager.health_check()

            # Check data freshness for stocks
            try:
                data_freshness = self.nyse_fetcher.check_data_freshness()
                status_result["data_freshness"] = data_freshness
                # Extract companies tracked from the data freshness results
                status_result["companies_tracked"] = list(data_freshness.keys())
            except Exception as e:
                self.logger.warning("Could not check stock data freshness: %s", e)
                status_result["errors"].append(f"Stock data freshness check failed: {e}")

            # Get current exchange rate and currency pair info
            try:
                current_rate = self.currency_fetcher.get_current_exchange_rate()
                status_result["current_exchange_rate"] = current_rate
                # Set currency pair information
                status_result["currency_pair"] = (
                    f"{self.currency_fetcher.FROM_CURRENCY}/{self.currency_fetcher.TO_CURRENCY}"
                )
            except Exception as e:
                self.logger.warning("Could not get current exchange rate: %s", e)
                status_result["errors"].append(f"Exchange rate check failed: {e}")
                # Set default currency pair even if rate fetch failed
                try:
                    status_result["currency_pair"] = (
                        f"{self.currency_fetcher.FROM_CURRENCY}/{self.currency_fetcher.TO_CURRENCY}"
                    )
                except AttributeError:
                    status_result["currency_pair"] = "USD/GBP"  # Default fallback

            # Identify missing recent data (if any stocks are more than 2 days old)
            from datetime import date, timedelta

            cutoff_date = date.today() - timedelta(days=2)
            for symbol, last_date in status_result["data_freshness"].items():
                if isinstance(last_date, date) and last_date < cutoff_date:
                    status_result["missing_recent_data"].append(symbol)

        except Exception as e:
            self.logger.error("Error during data status check: %s", e)
            status_result["errors"].append(f"Status check failed: {e}")

        return status_result
