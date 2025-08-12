"""Currency data fetcher for USD/GBP conversion rates.

This module handles fetching daily USD/GBP exchange rates and storing them
in SQL tables for use with stock price conversions.
"""

import logging
from datetime import datetime
from typing import Any

import pandas as pd

from ..api_clients.api_client import AlphaVantageAPIError, AlphaVantageClient
from ..api_clients.constants import OutputSize


class CurrencyDataFetcher:
    """Fetcher for USD/GBP currency conversion data."""

    # Currency pair configuration
    FROM_CURRENCY = "USD"
    TO_CURRENCY = "GBP"

    def __init__(self, api_client: AlphaVantageClient | None = None):
        """Initialize the currency data fetcher.

        Args:
            api_client: Alpha Vantage API client. If None, creates a new instance.
        """
        self.api_client = api_client or AlphaVantageClient()
        self.logger = logging.getLogger(__name__)

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

            # Extract the real-time exchange rate data
            rate_data = response.get("Realtime Currency Exchange Rate", {})

            if not rate_data:
                self.logger.error("No exchange rate data in response: %s", response)
                return None

            result = {
                "from_currency": rate_data.get("1. From_Currency Code", self.FROM_CURRENCY),
                "to_currency": rate_data.get("3. To_Currency Code", self.TO_CURRENCY),
                "exchange_rate": float(rate_data.get("5. Exchange Rate", 0)),
                "last_refreshed": rate_data.get("6. Last Refreshed", ""),
                "timezone": rate_data.get("7. Time Zone", "UTC"),
                "bid_price": float(rate_data.get("8. Bid Price", 0)),
                "ask_price": float(rate_data.get("9. Ask Price", 0)),
            }

            self.logger.info(
                "Current %s/%s rate: %.6f",
                self.FROM_CURRENCY,
                self.TO_CURRENCY,
                result["exchange_rate"],
            )
            return result

        except AlphaVantageAPIError as e:
            self.logger.error("API error fetching exchange rate: %s", e)
            return None
        except (ValueError, KeyError, TypeError) as e:
            self.logger.error("Data processing error fetching exchange rate: %s", e)
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

    def prepare_for_sql_insert(self, df: pd.DataFrame) -> list[dict[str, Any]]:
        """Prepare DataFrame data for SQL insertion into raw_currency_data table.

        Args:
            df: DataFrame with FX data

        Returns:
            List of dictionaries ready for SQL insertion
        """
        records = []

        for _, row in df.iterrows():
            # Handle different possible column names from Alpha Vantage
            exchange_rate = None
            if "Close" in row:
                exchange_rate = float(row["Close"])
            elif "4. close" in row:
                exchange_rate = float(row["4. close"])
            else:
                # Try to find any numeric column that could be the rate
                for col in df.columns:
                    if col not in [
                        "Date",
                        "From_Symbol",
                        "To_Symbol",
                    ] and pd.api.types.is_numeric_dtype(df[col]):
                        exchange_rate = float(row[col])
                        break

            if exchange_rate is None:
                self.logger.warning("Could not determine exchange rate for row: %s", row)
                continue

            record = {
                "from_currency": self.FROM_CURRENCY,
                "to_currency": self.TO_CURRENCY,
                "data_date": (row["Date"].date() if hasattr(row["Date"], "date") else row["Date"]),
                "exchange_rate": exchange_rate,
                "source": "alpha_vantage",
                "created_at": datetime.now(),
            }
            records.append(record)

        return records

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
