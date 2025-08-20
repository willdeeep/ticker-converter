"""Currency data fetcher for USD/GBP conversion rates.

This module handles fetching daily USD/GBP exchange rates and storing them
in SQL tables for use with stock price conversions.
"""

from datetime import datetime
from typing import Any, ClassVar

import pandas as pd

from ..api_clients.constants import OutputSize
from ..api_clients.exceptions import AlphaVantageAPIError
from .base_fetcher import BaseDataFetcher


class CurrencyDataFetcher(BaseDataFetcher):
    """Fetcher for USD/GBP currency conversion data."""

    # Currency pair configuration
    FROM_CURRENCY: ClassVar[str] = "USD"
    TO_CURRENCY: ClassVar[str] = "GBP"

    # Required columns for currency data validation
    REQUIRED_COLUMNS: ClassVar[list[str]] = ["Date"]

    def fetch_current_exchange_rate(self) -> dict[str, Any] | None:
        """Fetch the current USD/GBP exchange rate.

        Returns:
            Dictionary with current exchange rate data or None if fetch fails
        """
        try:
            self.logger.info(
                "Fetching current %s/%s exchange rate",
                self.FROM_CURRENCY,
                self.TO_CURRENCY,
            )

            response = self.api_client.get_currency_exchange_rate(self.FROM_CURRENCY, self.TO_CURRENCY)

            # Handle None response
            if response is None:
                self.logger.error("API returned None response")
                return None

            # Extract the real-time exchange rate data
            rate_data = response.get("Realtime Currency Exchange Rate", {})

            if not rate_data:
                self.logger.error("No exchange rate data in response: %s", response)
                return None

            result = {
                "from_currency": rate_data.get("1. From_Currency Code", self.FROM_CURRENCY),
                "to_currency": rate_data.get("3. To_Currency Code", self.TO_CURRENCY),
                "exchange_rate": self._safe_float_conversion(rate_data.get("5. Exchange Rate", 0), "exchange_rate"),
                "last_refreshed": rate_data.get("6. Last Refreshed", ""),
                "timezone": rate_data.get("7. Time Zone", "UTC"),
                "bid_price": self._safe_float_conversion(rate_data.get("8. Bid Price", 0), "bid_price"),
                "ask_price": self._safe_float_conversion(rate_data.get("9. Ask Price", 0), "ask_price"),
            }

            self.logger.info(
                "Current %s/%s rate: %.6f",
                self.FROM_CURRENCY,
                self.TO_CURRENCY,
                result["exchange_rate"],
            )
            return result

        except AlphaVantageAPIError as e:
            self._handle_api_error(e, "fetching current exchange rate")
            return None
        except (ValueError, KeyError, TypeError) as e:
            self._handle_data_error(e, "processing current exchange rate")
            return None

    def fetch_daily_fx_data(self, days_back: int = 10) -> pd.DataFrame | None:
        """Fetch daily USD/GBP historical exchange rates.

        Args:
            days_back: Number of days of historical data to fetch

        Returns:
            DataFrame with daily FX data or None if fetch fails
        """
        try:
            self.logger.info(
                "Fetching daily {self.FROM_CURRENCY}/{self.TO_CURRENCY} data (%s days)",
                days_back,
            )

            # Determine output size based on days requested
            output_size = OutputSize.FULL if days_back > 100 else OutputSize.COMPACT

            df = self.api_client.get_forex_daily(self.FROM_CURRENCY, self.TO_CURRENCY, output_size)

            if df.empty:
                self.logger.warning("No FX data returned for {self.FROM_CURRENCY}/%s", self.TO_CURRENCY)
                return None

            # Limit to requested number of days if specified
            if days_back > 0:
                df = df.tail(days_back)

            self.logger.info("Successfully fetched %s days of FX data", len(df))
            return df

        except AlphaVantageAPIError as e:
            self.logger.error("API error fetching FX data: %s", e)
            return None
        except (ValueError, KeyError, TypeError, pd.errors.ParserError) as e:
            self.logger.error("Data processing error fetching FX data: %s", e)
            return None

    def prepare_for_sql_insert(self, df: pd.DataFrame, *args: Any) -> list[dict[str, Any]]:
        """Prepare DataFrame data for SQL insertion into raw_currency_data table.

        Args:
            df: DataFrame with FX data
            *args: Additional arguments (unused for currency data)

        Returns:
            List of dictionaries ready for SQL insertion
        """
        if not self._validate_dataframe(df, self.REQUIRED_COLUMNS):
            return []

        records = []
        base_record = self._create_base_record()

        for _, row in df.iterrows():
            try:
                # Handle different possible column names from Alpha Vantage
                exchange_rate = self._extract_exchange_rate(row, df.columns)

                if exchange_rate is None:
                    self.logger.warning("Could not determine exchange rate for row: %s", row)
                    continue

                record = {
                    "from_currency": self.FROM_CURRENCY,
                    "to_currency": self.TO_CURRENCY,
                    "data_date": self._safe_date_conversion(row["Date"]),
                    "exchange_rate": exchange_rate,
                    **base_record,
                }
                records.append(record)
            except Exception as e:
                self.logger.warning("Skipping invalid currency row: %s", e)
                continue

        return records

    def _extract_exchange_rate(self, row: pd.Series, columns: pd.Index) -> float | None:
        """Extract exchange rate from row, handling various column formats.

        Args:
            row: DataFrame row
            columns: Available columns

        Returns:
            Exchange rate as float or None if not found
        """
        # Try common column names in order of preference
        rate_columns = ["Close", "4. close", "close"]

        for col in rate_columns:
            if col in row:
                return self._safe_float_conversion(row[col], "exchange_rate")

        # Try to find any numeric column that could be the rate
        for col in columns:
            if col not in [
                "Date",
                "From_Symbol",
                "To_Symbol",
            ] and pd.api.types.is_numeric_dtype(row[col]):
                return self._safe_float_conversion(row[col], "exchange_rate")

        return None

    def prepare_current_rate_for_sql(self, rate_data: dict[str, Any]) -> dict[str, Any] | None:
        """Prepare current rate data for SQL insertion.

        Args:
            rate_data: Current exchange rate data

        Returns:
            Dictionary ready for SQL insertion or None if invalid
        """
        if not rate_data or rate_data.get("exchange_rate", 0) <= 0:
            return None

        # Parse the last refreshed date
        try:
            last_refreshed = rate_data.get("last_refreshed", "")
            if last_refreshed:
                # Try to parse the datetime string
                data_date = datetime.strptime(last_refreshed.split()[0], "%Y-%m-%d").date()
            else:
                data_date = datetime.now().date()
        except (ValueError, IndexError):
            data_date = datetime.now().date()

        return {
            "from_currency": self.FROM_CURRENCY,
            "to_currency": self.TO_CURRENCY,
            "data_date": data_date,
            "exchange_rate": rate_data["exchange_rate"],
            "source": "alpha_vantage",
            "created_at": datetime.now(),
        }

    def fetch_and_prepare_fx_data(self, days_back: int = 10) -> list[dict[str, Any]]:
        """Fetch and prepare FX data for SQL insertion.

        Args:
            days_back: Number of days of historical data to fetch

        Returns:
            List of records ready for SQL insertion
        """
        records = []

        # First try to get historical daily data
        df = self.fetch_daily_fx_data(days_back)
        if df is not None:
            records = self.prepare_for_sql_insert(df)
            self.logger.info("Prepared %s historical FX records", len(records))

        # If we don't have recent data, also fetch current rate
        if not records or len(records) < 2:
            current_rate = self.fetch_current_exchange_rate()
            if current_rate:
                current_record = self.prepare_current_rate_for_sql(current_rate)
                if current_record:
                    # Check if we already have this date
                    existing_dates = {r["data_date"] for r in records}
                    if current_record["data_date"] not in existing_dates:
                        records.append(current_record)
                        self.logger.info("Added current exchange rate to records")

        self.logger.info("Total FX records prepared for insertion: %s", len(records))
        return records

    def get_latest_available_rate(self) -> tuple[datetime, float] | None:
        """Get the latest available exchange rate.

        Returns:
            Tuple of (date, rate) or None if not available
        """
        try:
            # Try daily data first
            df = self.fetch_daily_fx_data(1)
            if df is not None and not df.empty:
                latest_row = df.iloc[-1]
                rate = float(latest_row["Close"]) if "Close" in latest_row else None
                if rate:
                    return latest_row["Date"], rate

            # Fall back to current rate
            current_rate = self.fetch_current_exchange_rate()
            if current_rate and current_rate.get("exchange_rate"):
                return datetime.now(), current_rate["exchange_rate"]

        except (ValueError, KeyError, TypeError, AttributeError) as e:
            self.logger.error("Error getting latest exchange rate: %s", e)

        return None
