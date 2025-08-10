"""Core functionality for the Financial Market Data Analytics Pipeline."""

import logging
from typing import Any
from typing import Optional

import pandas as pd

from .api_client import AlphaVantageAPIError
from .api_client import AlphaVantageClient
from .pipeline_config import PipelineConfig

logger = logging.getLogger(__name__)


class FinancialDataPipeline:
    """Main pipeline class for financial data processing."""

    def __init__(
        self, api_key: Optional[str] = None, config: Optional[PipelineConfig] = None
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
            return self._handle_api_error(
                f"Error fetching intraday data for {symbol}: {e}"
            )

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
                logger.error("Error fetching company info for %s: %s", symbol, e)
            if not self.config.suppress_api_errors:
                print(f"Error fetching company info for {symbol}: {e}")
            return {}

    def _handle_api_error(self, error_message: str) -> pd.DataFrame:
        """Handle API errors based on configuration.

        Args:
            error_message: The error message to log/display

        Returns:
            Empty DataFrame if return_empty_on_error is True, None otherwise
        """
        if self.config.log_errors:
            logger.error(error_message)
        if not self.config.suppress_api_errors:
            print(error_message)
        if self.config.return_empty_on_error:
            return pd.DataFrame()
        else:
            # MyPy requires consistent return type - raise exception instead of returning None
            raise RuntimeError(error_message)

    def transform(self, data: pd.DataFrame, symbol: str = "UNKNOWN") -> pd.DataFrame:
        """Transform raw financial data using cleaning and feature engineering pipeline.

        Args:
            data: Raw financial data.
            symbol: Stock symbol for the data.

        Returns:
            Transformed data with engineered features.
        """
        from .data_models.market_data import MarketDataPoint
        from .data_models.market_data import RawMarketData
        from .etl_modules import DataCleaner
        from .etl_modules import FeatureEngineer
        from .etl_modules import QualityValidator

        try:
            # Convert DataFrame to RawMarketData model
            data_points = []
            for idx, row in data.iterrows():
                point = MarketDataPoint(
                    timestamp=(
                        idx if isinstance(idx, pd.Timestamp) else pd.Timestamp(idx)
                    ),
                    symbol=row.get("Symbol", symbol),
                    open=float(row["Open"]),
                    high=float(row["High"]),
                    low=float(row["Low"]),
                    close=float(row["Close"]),
                    volume=int(row["Volume"]),
                )
                data_points.append(point)

            raw_data = RawMarketData(
                data_points=data_points,
                source="alpha_vantage",
                symbol=symbol,
                data_type="daily",
            )

            # Initialize pipeline components
            cleaner = DataCleaner()
            feature_engineer = FeatureEngineer()
            validator = QualityValidator()

            # Validate input data
            validation_result = validator.validate(data, symbol)
            if not validation_result.is_valid:
                logger.warning(
                    f"Data validation issues for {symbol}: {validation_result.errors}"
                )

            # Clean the data
            cleaned_data = cleaner.clean(raw_data)

            # Engineer features
            feature_data = feature_engineer.engineer_features(cleaned_data)

            # Convert back to DataFrame with features from feature_data
            df_with_features = feature_data.to_dataframe()

            # Use the engineered features from feature_data
            # For now, return the original transformed data
            logger.info(f"Data transformation completed for {symbol}")
            return df_with_features

        except Exception as e:
            logger.error(f"Error during data transformation for {symbol}: {e}")
            return data
