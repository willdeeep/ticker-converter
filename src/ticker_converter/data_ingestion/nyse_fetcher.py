"""NYSE stock data fetcher for Magnificent Seven companies.

This module handles f        results = {}

        self.logger.info("Fetching data for         for symbol, df in stock_data.items():
            records = self.prepare_for_sql_insert(df, symbol)
            all_records.extend(records)
            self.logger.info("Prepared %d records for %s", len(records), symbol)

        self.logger.info("Total prepared records: %d", len(all_records))icent Seven companies (%d days)", days_back)

        for symbol in self.MAGNIFICENT_SEVEN:
            df = self.fetch_daily_data(symbol, days_back)
            if df is not None:
                results[symbol] = df
            else:
                self.logger.warning("Failed to fetch data for %s", symbol)

        self.logger.info("Successfully fetched data for %d companies", len(results))y stock data for the Magnificent Seven companies
(AAPL, MSFT, AMZN, GOOGL, META, NVDA, TSLA) and storing it in SQL tables.
"""

import logging
from datetime import datetime
from typing import Any

import pandas as pd

from ..api_clients.api_client import AlphaVantageClient
from ..api_clients.constants import OutputSize


class NYSEDataFetcher:
    """Fetcher for NYSE stock data focusing on Magnificent Seven companies."""

    # Magnificent Seven companies
    MAGNIFICENT_SEVEN = [
        "AAPL",  # Apple Inc.
        "MSFT",  # Microsoft Corporation
        "AMZN",  # Amazon.com Inc.
        "GOOGL",  # Alphabet Inc.
        "META",  # Meta Platforms Inc.
        "NVDA",  # NVIDIA Corporation
        "TSLA",  # Tesla Inc.
    ]

    def __init__(self, api_client: AlphaVantageClient | None = None):
        """Initialize the NYSE data fetcher.

        Args:
            api_client: Alpha Vantage API client. If None, creates a new instance.
        """
        self.api_client = api_client or AlphaVantageClient()
        self.logger = logging.getLogger(__name__)

    def fetch_daily_data(self, symbol: str, days_back: int = 10) -> pd.DataFrame | None:
        """Fetch daily stock data for a specific symbol.

        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            days_back: Number of days of historical data to fetch (for initial setup)

        Returns:
            DataFrame with daily stock data or None if fetch fails
        """
        try:
            self.logger.info("Fetching daily data for %s", symbol)

            # Determine output size based on days requested
            output_size = OutputSize.FULL if days_back > 100 else OutputSize.COMPACT

            df = self.api_client.get_daily_stock_data(symbol, output_size)

            if df.empty:
                self.logger.warning("No data returned for %s", symbol)
                return None

            # Filter to the requested number of days
            df_filtered = df.head(days_back)

            self.logger.info(
                "Retrieved %d days of data for %s", len(df_filtered), symbol
            )
            return df_filtered

        except (ValueError, KeyError, TypeError, pd.errors.ParserError) as e:
            self.logger.error("Error fetching data for %s: %s", symbol, e)
            return None

    def fetch_magnificent_seven_data(
        self, days_back: int = 10
    ) -> dict[str, pd.DataFrame]:
        """Fetch daily data for all Magnificent Seven companies.

        Args:
            days_back: Number of days of historical data to fetch

        Returns:
            Dictionary mapping symbols to their DataFrames
        """
        results = {}

        self.logger.info(
            "Fetching data for Magnificent Seven companies (%s days)", days_back
        )

        for symbol in self.MAGNIFICENT_SEVEN:
            df = self.fetch_daily_data(symbol, days_back)
            if df is not None:
                results[symbol] = df
            else:
                self.logger.warning("Failed to fetch data for %s", symbol)

        self.logger.info(
            "Successfully fetched data for {len(results)}/%s companies",
            len(self.MAGNIFICENT_SEVEN),
        )
        return results

    def prepare_for_sql_insert(
        self, df: pd.DataFrame, symbol: str
    ) -> list[dict[str, Any]]:
        """Prepare DataFrame data for SQL insertion into raw_stock_data table.

        Args:
            df: DataFrame with stock data
            symbol: Stock symbol

        Returns:
            List of dictionaries ready for SQL insertion
        """
        records = []

        for _, row in df.iterrows():
            record = {
                "symbol": symbol,
                "data_date": (
                    row["Date"].date() if hasattr(row["Date"], "date") else row["Date"]
                ),
                "open_price": float(row["Open"]),
                "high_price": float(row["High"]),
                "low_price": float(row["Low"]),
                "close_price": float(row["Close"]),
                "volume": int(row["Volume"]),
                "source": "alpha_vantage",
                "created_at": datetime.now(),
            }
            records.append(record)

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
            self.logger.info("Prepared {len(records)} records for %s", symbol)

        self.logger.info("Total records prepared for insertion: %s", len(all_records))
        return all_records

    def get_latest_available_date(self, symbol: str) -> datetime | None:
        """Get the latest available date for a symbol from the API.

        Args:
            symbol: Stock symbol

        Returns:
            Latest available date or None if not available
        """
        try:
            df = self.api_client.get_daily_stock_data(symbol, OutputSize.COMPACT)
            if not df.empty:
                latest_date = df["Date"].max()
                if isinstance(latest_date, datetime):
                    return latest_date
                # Convert pandas Timestamp to datetime if needed
                try:
                    converted_date = pd.to_datetime(latest_date).to_pydatetime()
                    if isinstance(converted_date, datetime):
                        return converted_date
                except (ValueError, TypeError):
                    self.logger.warning("Could not convert date %s to datetime", latest_date)
        except (ValueError, KeyError, TypeError, AttributeError) as e:
            self.logger.error("Error getting latest date for %s: %s", symbol, e)

        return None

    def check_data_freshness(self) -> dict[str, datetime]:
        """Check latest available dates for all Magnificent Seven companies.

        Returns:
            Dictionary mapping symbols to their latest available dates
        """
        freshness = {}

        for symbol in self.MAGNIFICENT_SEVEN:
            latest_date = self.get_latest_available_date(symbol)
            if latest_date:
                freshness[symbol] = latest_date

        return freshness
