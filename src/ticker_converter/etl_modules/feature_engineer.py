"""Feature engineering module for market data."""

import logging
from typing import Optional

import pandas as pd
from pydantic import BaseModel
from pydantic import Field

from ..data_models.market_data import CleanedMarketData
from ..data_models.market_data import FeatureEngineeredData
from ..data_models.market_data import VolatilityFlag
from .constants import FeatureConstants
from .constants import MarketDataColumns
from .constants import TechnicalIndicatorConstants
from .utils import FeatureEngineering

logger = logging.getLogger(__name__)


class FeatureConfig(BaseModel):
    """Configuration for feature engineering operations."""

    moving_averages: list[int] = Field(
        default=FeatureConstants.DEFAULT_MA_PERIODS,
        description="Moving average periods",
    )
    calculate_returns: bool = Field(default=True, description="Calculate price returns")
    calculate_volatility: bool = Field(
        default=True, description="Calculate volatility metrics"
    )
    volatility_window: int = Field(
        default=FeatureConstants.DEFAULT_VOLATILITY_WINDOW,
        description="Window for volatility calculations",
    )

    # Volatility thresholds
    volatility_threshold_low: float = Field(
        default=FeatureConstants.VOLATILITY_LOW_THRESHOLD,
        description="Low volatility threshold",
    )
    volatility_threshold_moderate: float = Field(
        default=FeatureConstants.VOLATILITY_MODERATE_THRESHOLD,
        description="Moderate volatility threshold",
    )
    volatility_threshold_high: float = Field(
        default=FeatureConstants.VOLATILITY_HIGH_THRESHOLD,
        description="High volatility threshold",
    )

    # Technical indicators
    calculate_rsi: bool = Field(default=True, description="Calculate RSI indicator")
    rsi_period: int = Field(
        default=FeatureConstants.DEFAULT_RSI_PERIOD,
        description="RSI calculation period",
    )

    calculate_bollinger_bands: bool = Field(
        default=True, description="Calculate Bollinger Bands"
    )
    bollinger_period: int = Field(
        default=TechnicalIndicatorConstants.BB_DEFAULT_PERIOD,
        description="Bollinger Bands period",
    )
    bollinger_std: float = Field(
        default=TechnicalIndicatorConstants.BB_DEFAULT_STD,
        description="Bollinger Bands standard deviation",
    )


class FeatureEngineer:
    """Creates features for market data analysis."""

    def __init__(self, config: Optional[FeatureConfig] = None):
        """Initialize the feature engineer.

        Args:
            config: Feature engineering configuration
        """
        self.config = config or FeatureConfig()
        self.features_created: list[str] = []

    def engineer_features(
        self, cleaned_data: CleanedMarketData
    ) -> FeatureEngineeredData:
        """Engineer features from cleaned market data.

        Args:
            cleaned_data: Cleaned market data

        Returns:
            FeatureEngineeredData with engineered features
        """
        logger.info(f"Starting feature engineering for {cleaned_data.raw_data.symbol}")

        # Reset features list
        self.features_created = []

        # Get DataFrame from cleaned data
        df = cleaned_data.raw_data.to_dataframe()

        logger.info(f"Input data shape: {df.shape}")

        # Apply feature engineering operations
        df = self._calculate_returns(df)
        df = self._calculate_moving_averages(df)
        df = self._calculate_volatility_metrics(df)
        df = self._calculate_volatility_flags(df)
        df = self._calculate_technical_indicators(df)
        df = self._calculate_price_features(df)

        logger.info(f"Feature engineered data shape: {df.shape}")
        logger.info(f"Features created: {self.features_created}")

        # Create feature engineered data object
        feature_data = FeatureEngineeredData(
            cleaned_data=cleaned_data,
            ma_periods=self.config.moving_averages.copy(),
            volatility_threshold_low=self.config.volatility_threshold_low,
            volatility_threshold_moderate=self.config.volatility_threshold_moderate,
            volatility_threshold_high=self.config.volatility_threshold_high,
            features_created=self.features_created.copy(),
        )

        return feature_data

    def _calculate_returns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate price returns."""
        if not self.config.calculate_returns:
            return df

        try:
            df = FeatureEngineering.calculate_returns(df, MarketDataColumns.CLOSE)
            self.features_created.extend(
                ["Daily_Return", "Log_Return", "Cumulative_Return"]
            )
            logger.debug("Calculated return features")

        except Exception as e:
            logger.warning(f"Error calculating returns: {e}")

        return df

    def _calculate_moving_averages(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate moving averages for specified periods."""
        try:
            for period in self.config.moving_averages:
                col_name = f"MA_{period}"
                df[col_name] = FeatureEngineering.calculate_moving_average(
                    df, MarketDataColumns.CLOSE, period
                )
                self.features_created.append(col_name)

                # Calculate ratio of current price to moving average
                ratio_col = f"Price_to_MA_{period}_Ratio"
                df[ratio_col] = df[MarketDataColumns.CLOSE] / df[col_name]
                self.features_created.append(ratio_col)

            logger.debug(
                f"Calculated moving averages for periods: {self.config.moving_averages}"
            )

        except Exception as e:
            logger.warning(f"Error calculating moving averages: {e}")

        return df

    def _calculate_volatility_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate volatility metrics."""
        if not self.config.calculate_volatility:
            return df

        try:
            window = self.config.volatility_window

            # Rolling volatility (standard deviation of returns)
            df["Volatility"] = (
                df["Daily_Return"].rolling(window=window, min_periods=1).std()
            )
            self.features_created.append("Volatility")

            # True Range for ATR calculation
            df["True_Range"] = self._calculate_true_range(df)
            self.features_created.append("True_Range")

            # Average True Range (ATR)
            df["ATR"] = df["True_Range"].rolling(window=window, min_periods=1).mean()
            self.features_created.append("ATR")

            # High-Low range as percentage of close
            df["HL_Range_Pct"] = ((df["High"] - df["Low"]) / df["Close"]) * 100
            self.features_created.append("HL_Range_Pct")

            logger.debug("Calculated volatility metrics")

        except Exception as e:
            logger.warning(f"Error calculating volatility metrics: {e}")

        return df

    def _calculate_true_range(self, df: pd.DataFrame) -> pd.Series:
        """Calculate True Range for ATR."""
        return FeatureEngineering.calculate_true_range(df)

    def _calculate_volatility_flags(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate volatility flags based on thresholds."""
        try:
            if "Volatility" not in df.columns:
                return df

            def classify_volatility(vol):
                if pd.isna(vol):
                    return VolatilityFlag.LOW.value
                elif vol < self.config.volatility_threshold_low:
                    return VolatilityFlag.LOW.value
                elif vol < self.config.volatility_threshold_moderate:
                    return VolatilityFlag.MODERATE.value
                elif vol < self.config.volatility_threshold_high:
                    return VolatilityFlag.HIGH.value
                else:
                    return VolatilityFlag.EXTREME.value

            df["Volatility_Flag"] = df["Volatility"].apply(classify_volatility)
            self.features_created.append("Volatility_Flag")

            # Binary flags for each volatility level
            for flag in VolatilityFlag:
                col_name = f"Is_{flag.value.title()}_Volatility"
                df[col_name] = (df["Volatility_Flag"] == flag.value).astype(int)
                self.features_created.append(col_name)

            logger.debug("Calculated volatility flags")

        except Exception as e:
            logger.warning(f"Error calculating volatility flags: {e}")

        return df

    def _calculate_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate technical indicators."""
        try:
            # RSI (Relative Strength Index)
            if self.config.calculate_rsi:
                df = self._calculate_rsi(df)

            # Bollinger Bands
            if self.config.calculate_bollinger_bands:
                df = self._calculate_bollinger_bands(df)

        except Exception as e:
            logger.warning(f"Error calculating technical indicators: {e}")

        return df

    def _calculate_rsi(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate RSI indicator."""
        try:
            period = self.config.rsi_period
            delta = df[MarketDataColumns.CLOSE].diff()

            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)

            avg_gain = gain.rolling(window=period, min_periods=1).mean()
            avg_loss = loss.rolling(window=period, min_periods=1).mean()

            rs = avg_gain / avg_loss
            df["RSI"] = 100 - (100 / (1 + rs))
            self.features_created.append("RSI")

            # RSI signals using constants
            df["RSI_Oversold"] = (
                df["RSI"] < TechnicalIndicatorConstants.RSI_OVERSOLD_THRESHOLD
            ).astype(int)
            df["RSI_Overbought"] = (
                df["RSI"] > TechnicalIndicatorConstants.RSI_OVERBOUGHT_THRESHOLD
            ).astype(int)
            self.features_created.extend(["RSI_Oversold", "RSI_Overbought"])

            logger.debug("Calculated RSI indicator")

        except Exception as e:
            logger.warning(f"Error calculating RSI: {e}")

        return df

    def _calculate_bollinger_bands(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate Bollinger Bands."""
        try:
            period = self.config.bollinger_period
            std_dev = self.config.bollinger_std

            # Middle band (SMA)
            df["BB_Middle"] = (
                df[MarketDataColumns.CLOSE].rolling(window=period, min_periods=1).mean()
            )

            # Standard deviation
            rolling_std = (
                df[MarketDataColumns.CLOSE].rolling(window=period, min_periods=1).std()
            )

            # Upper and lower bands
            df["BB_Upper"] = df["BB_Middle"] + (rolling_std * std_dev)
            df["BB_Lower"] = df["BB_Middle"] - (rolling_std * std_dev)

            # Band width
            df["BB_Width"] = df["BB_Upper"] - df["BB_Lower"]

            # Position within bands
            df["BB_Position"] = (df[MarketDataColumns.CLOSE] - df["BB_Lower"]) / (
                df["BB_Upper"] - df["BB_Lower"]
            )

            # Signals
            df["BB_Squeeze"] = (
                df["BB_Width"] < df["BB_Width"].rolling(window=20, min_periods=1).mean()
            ).astype(int)

            self.features_created.extend(
                [
                    "BB_Middle",
                    "BB_Upper",
                    "BB_Lower",
                    "BB_Width",
                    "BB_Position",
                    "BB_Squeeze",
                ]
            )

            logger.debug("Calculated Bollinger Bands")

        except Exception as e:
            logger.warning(f"Error calculating Bollinger Bands: {e}")

        return df

    def _calculate_price_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate additional price-based features."""
        try:
            # Price gaps
            df["Gap_Up"] = (
                (df["Open"] > df["Close"].shift(1)) & (df["Low"] > df["High"].shift(1))
            ).astype(int)
            df["Gap_Down"] = (
                (df["Open"] < df["Close"].shift(1)) & (df["High"] < df["Low"].shift(1))
            ).astype(int)

            # Doji patterns (Open ≈ Close)
            body_size = abs(df["Close"] - df["Open"]) / df["Close"]
            df["Is_Doji"] = (body_size < 0.01).astype(int)

            # Price momentum
            df["Price_Momentum_5"] = df["Close"] / df["Close"].shift(5) - 1
            df["Price_Momentum_10"] = df["Close"] / df["Close"].shift(10) - 1

            # Volume features
            if "Volume" in df.columns:
                df["Volume_MA_20"] = (
                    df["Volume"].rolling(window=20, min_periods=1).mean()
                )
                df["Volume_Ratio"] = df["Volume"] / df["Volume_MA_20"]
                df["High_Volume"] = (df["Volume_Ratio"] > 1.5).astype(int)

                self.features_created.extend(
                    ["Volume_MA_20", "Volume_Ratio", "High_Volume"]
                )

            self.features_created.extend(
                [
                    "Gap_Up",
                    "Gap_Down",
                    "Is_Doji",
                    "Price_Momentum_5",
                    "Price_Momentum_10",
                ]
            )

            logger.debug("Calculated price features")

        except Exception as e:
            logger.warning(f"Error calculating price features: {e}")

        return df
