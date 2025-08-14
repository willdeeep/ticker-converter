"""NYSE data fetcher for Magnificent Seven companies.

This module handles fetching daily stock data for the Magnificent Seven companies
(AAPL, MSFT, AMZN, GOOGL, META, NVDA, TSLA) and storing it in SQL tables.
"""

from datetime import date
from typing import Any, ClassVar

import pandas as pd

from ..api_clients.constants import OutputSize
from ..api_clients.exceptions import AlphaVantageAPIError
from .base_fetcher import BaseDataFetcher


class NYSEDataFetcher(BaseDataFetcher):
    """Fetcher for NYSE stock data focusing on Magnificent Seven companies."""

    # Magnificent Seven companies
    MAGNIFICENT_SEVEN: ClassVar[list[str]] = [
        "AAPL",  # Apple Inc.
        "MSFT",  # Microsoft Corporation
        "AMZN",  # Amazon.com Inc.
        "GOOGL",  # Alphabet Inc.
        "META",  # Meta Platforms Inc.
        "NVDA",  # NVIDIA Corporation
        "TSLA",  # Tesla Inc.
    ]

    # Required columns for stock data validation
    REQUIRED_COLUMNS: ClassVar[list[str]] = [
        "Date",
        "Open",
        "High",
        "Low",
        "Close",
        "Volume",
    ]

    def fetch_daily_data(self, symbol: str, days_back: int = 10) -> pd.DataFrame | None:
        """Fetch daily stock data for a specific symbol.

        Args:
            symbol: Stock symbol to fetch
            days_back: Number of days of historical data to fetch

        Returns:
            DataFrame with daily stock data or None if error
        """
        try:
            self.logger.info("Fetching %d days of data for %s", days_back, symbol)

            # Get data from Alpha Vantage
            df = self.api_client.get_daily_stock_data(symbol, OutputSize.COMPACT)

            if not self._validate_dataframe(df, self.REQUIRED_COLUMNS):
                return None

            # Filter to requested number of days
            df_filtered = df.tail(days_back) if days_back > 0 else df

            self.logger.info(
                "Retrieved %d days of data for %s", len(df_filtered), symbol
            )
            return df_filtered

        except AlphaVantageAPIError as e:
            self._handle_api_error(e, f"fetching data for {symbol}")
            return None
        except (ValueError, KeyError, TypeError, pd.errors.ParserError) as e:
            self._handle_data_error(e, f"fetching data for {symbol}")
            return None

    def fetch_magnificent_seven_data(
        self, days_back: int = 10
    ) -> dict[str, pd.DataFrame]:
        """Fetch data for all Magnificent Seven companies.

        Args:
            days_back: Number of days of historical data to fetch

        Returns:
            Dictionary mapping symbol to DataFrame
        """
        results = {}

        self.logger.info(
            f"Fetching data for Magnificent Seven companies ({days_back} days)"
        )

        for symbol in self.MAGNIFICENT_SEVEN:
            df = self.fetch_daily_data(symbol, days_back)
            if df is not None:
                results[symbol] = df
            else:
                self.logger.warning("Failed to fetch data for %s", symbol)

        self.logger.info("Successfully fetched data for %s companies", len(results))
        return results

    def prepare_for_sql_insert(
        self, df: pd.DataFrame, *args: Any
    ) -> list[dict[str, Any]]:
        """Prepare DataFrame data for SQL insertion into raw_stock_data table.

        Args:
            df: DataFrame with stock data
            *args: Should contain symbol as first argument

        Returns:
            List of dictionaries ready for SQL insertion
        """
        if not args:
            raise ValueError("Symbol must be provided as first argument")

        symbol = args[0]
        if not self._validate_dataframe(df, self.REQUIRED_COLUMNS):
            return []

        records = []
        base_record = self._create_base_record()

        for _, row in df.iterrows():
            try:
                record = {
                    "symbol": symbol,
                    "data_date": self._safe_date_conversion(row["Date"]),
                    "open_price": self._safe_float_conversion(
                        row["Open"], "open_price"
                    ),
                    "high_price": self._safe_float_conversion(
                        row["High"], "high_price"
                    ),
                    "low_price": self._safe_float_conversion(row["Low"], "low_price"),
                    "close_price": self._safe_float_conversion(
                        row["Close"], "close_price"
                    ),
                    "volume": self._safe_int_conversion(row["Volume"], "volume"),
                    **base_record,
                }
                records.append(record)
            except Exception as e:
                self.logger.warning("Skipping invalid row for %s: %s", symbol, e)
                continue

        return records

    def fetch_and_prepare_all_data(self, days_back: int = 10) -> list[dict[str, Any]]:
        """Fetch and prepare all Magnificent Seven data for SQL insertion.

        Args:
            days_back: Number of days of historical data to fetch

        Returns:
            List of all records ready for SQL insertion
        """
        all_records = []
        stock_data = self.fetch_magnificent_seven_data(days_back)

        for symbol, df in stock_data.items():
            records = self.prepare_for_sql_insert(df, symbol)
            all_records.extend(records)
            self.logger.info("Prepared %s records for %s", len(records), symbol)

        self.logger.info("Total records prepared for insertion: %s", len(all_records))
        return all_records

    def get_latest_available_date(self, symbol: str) -> date | None:
        """Get the latest available date for a symbol from the API.

        Args:
            symbol: Stock symbol

        Returns:
            Latest available date or None if error
        """
        try:
            df = self.fetch_daily_data(symbol, days_back=1)
            if df is not None and not df.empty:
                latest_date = df.iloc[-1]["Date"]
                return self._safe_date_conversion(latest_date)
            return None

        except (ValueError, KeyError, TypeError, IndexError) as e:
            self._handle_data_error(e, f"getting latest date for {symbol}")
            return None

    def check_data_freshness(self) -> dict[str, date]:
        """Check data freshness for all Magnificent Seven stocks.

        Returns:
            Dictionary mapping symbol to latest available date
        """
        freshness = {}

        for symbol in self.MAGNIFICENT_SEVEN:
            latest_date = self.get_latest_available_date(symbol)
            if latest_date:
                freshness[symbol] = latest_date

        return freshness
