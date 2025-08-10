"""Core functionality for the Financial Market Data Analytics Pipeline."""

import logging
from typing import Any, Optional

import pandas as pd

from .api_client import AlphaVantageAPIError, AlphaVantageClient
from .pipeline_config import PipelineConfig


logger = logging.getLogger(__name__)


class FinancialDataPipeline:
    """Main pipeline class for financial data processing."""

    def __init__(
        self, 
        api_key: Optional[str] = None, 
        config: Optional[PipelineConfig] = None
    ) -> None:
        """Initialize the pipeline.

        Args:
            api_key: Optional API key for financial data services.
            config: Optional pipeline configuration.
        """
        self.config = config or PipelineConfig(api_key=api_key)
        self.api_key = api_key or self.config.api_key
        self.alpha_vantage = AlphaVantageClient(self.api_key)

    def fetch_stock_data(self, symbol: str, period: str = "1mo") -> pd.DataFrame:
        """Fetch stock data for a given symbol.

        Args:
            symbol: Stock symbol (e.g., 'AAPL').
            period: Time period for data retrieval ('1mo', '3mo', '1y', 'max').

        Returns:
            DataFrame containing stock data.
        """
        try:
            outputsize = self.config.get_outputsize(period)
            return self.alpha_vantage.get_daily_stock_data(symbol, outputsize)

        except AlphaVantageAPIError as e:
            return self._handle_api_error(f"Error fetching data for {symbol}: {e}")

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
            return self._handle_api_error(f"Error fetching intraday data for {symbol}: {e}")

    def get_company_info(self, symbol: str) -> dict[str, Any]:
        """Get company overview information.

        Args:
            symbol: Stock symbol (e.g., 'AAPL').

        Returns:
            Dictionary with company information.
        """
        try:
            return self.alpha_vantage.get_company_overview(symbol)
        except AlphaVantageAPIError as e:
            if self.config.log_errors:
                logger.error(f"Error fetching company info for {symbol}: {e}")
            if not self.config.suppress_api_errors:
                print(f"Error fetching company info for {symbol}: {e}")
            return {}

    def _handle_api_error(self, error_message: str) -> pd.DataFrame:
        """Handle API errors consistently.
        
        Args:
            error_message: Error message to log/print
            
        Returns:
            Empty DataFrame if configured to return empty on error
        """
        if self.config.log_errors:
            logger.error(error_message)
        if not self.config.suppress_api_errors:
            print(error_message)
        return pd.DataFrame() if self.config.return_empty_on_error else None

    def transform(self, data: pd.DataFrame) -> pd.DataFrame:
        """Transform raw financial data.

        Args:
            data: Raw financial data.

        Returns:
            Transformed data.
        """
        # Placeholder implementation - will be implemented in Issue #3
        return data
