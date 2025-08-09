"""Core functionality for the Financial Market Data Analytics Pipeline."""

from typing import Optional
import pandas as pd
from .api_client import AlphaVantageClient, AlphaVantageAPIError


class FinancialDataPipeline:
    """Main pipeline class for financial data processing."""

    def __init__(self, api_key: Optional[str] = None) -> None:
        """Initialize the pipeline.

        Args:
            api_key: Optional API key for financial data services.
        """
        self.api_key = api_key
        self.alpha_vantage = AlphaVantageClient(api_key)

    def fetch_stock_data(self, symbol: str, period: str = "1mo") -> pd.DataFrame:
        """Fetch stock data for a given symbol.

        Args:
            symbol: Stock symbol (e.g., 'AAPL').
            period: Time period for data retrieval ('1mo', '3mo', '1y', 'max').
            
        Returns:
            DataFrame containing stock data.
        """
        try:
            # Map period to Alpha Vantage outputsize
            if period in ["1mo", "3mo"]:
                outputsize = "compact"  # Last 100 data points
            else:
                outputsize = "full"     # All available data
            
            return self.alpha_vantage.get_daily_stock_data(symbol, outputsize)
            
        except AlphaVantageAPIError as e:
            print(f"Error fetching data for {symbol}: {e}")
            return pd.DataFrame()

    def fetch_intraday_data(self, symbol: str, interval: str = "5min") -> pd.DataFrame:
        """Fetch intraday stock data for a given symbol.

        Args:
            symbol: Stock symbol (e.g., 'AAPL').
            interval: Time interval ('1min', '5min', '15min', '30min', '60min').
            
        Returns:
            DataFrame containing intraday stock data.
        """
        try:
            return self.alpha_vantage.get_intraday_stock_data(symbol, interval)
        except AlphaVantageAPIError as e:
            print(f"Error fetching intraday data for {symbol}: {e}")
            return pd.DataFrame()

    def get_company_info(self, symbol: str) -> dict:
        """Get company overview information.

        Args:
            symbol: Stock symbol (e.g., 'AAPL').
            
        Returns:
            Dictionary with company information.
        """
        try:
            return self.alpha_vantage.get_company_overview(symbol)
        except AlphaVantageAPIError as e:
            print(f"Error fetching company info for {symbol}: {e}")
            return {}

    def transform(self, data: pd.DataFrame) -> pd.DataFrame:
        """Transform raw financial data.

        Args:
            data: Raw financial data.
            
        Returns:
            Transformed data.
        """
        # Placeholder implementation - will be implemented in Issue #3
        return data
