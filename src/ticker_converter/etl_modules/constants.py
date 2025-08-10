"""Constants for ETL modules."""

from typing import List, Final

# Column names for market data
class MarketDataColumns:
    """Standard column names for market data."""
    OPEN: Final[str] = "Open"
    HIGH: Final[str] = "High"
    LOW: Final[str] = "Low"
    CLOSE: Final[str] = "Close"
    VOLUME: Final[str] = "Volume"
    SYMBOL: Final[str] = "Symbol"
    DATE: Final[str] = "Date"
    
    # Price columns for easy iteration
    PRICE_COLUMNS: Final[List[str]] = [OPEN, HIGH, LOW, CLOSE]
    NUMERIC_COLUMNS: Final[List[str]] = [OPEN, HIGH, LOW, CLOSE, VOLUME]

# Technical indicator constants
class TechnicalIndicatorConstants:
    """Constants for technical indicators."""
    
    # RSI constants
    RSI_OVERSOLD_THRESHOLD: Final[float] = 30.0
    RSI_OVERBOUGHT_THRESHOLD: Final[float] = 70.0
    
    # Bollinger Bands defaults
    BB_DEFAULT_PERIOD: Final[int] = 20
    BB_DEFAULT_STD: Final[float] = 2.0
    
    # Volume analysis
    HIGH_VOLUME_RATIO_THRESHOLD: Final[float] = 1.5
    
    # Price pattern detection
    DOJI_BODY_SIZE_THRESHOLD: Final[float] = 0.01

# Data validation constants
class ValidationConstants:
    """Constants for data validation."""
    
    # Default thresholds
    MIN_COMPLETENESS_SCORE: Final[float] = 0.95
    MIN_CONSISTENCY_SCORE: Final[float] = 0.90
    MIN_VALIDITY_SCORE: Final[float] = 0.95
    
    # Price validation
    MAX_DAILY_PRICE_CHANGE: Final[float] = 0.20  # 20%
    MIN_PRICE_VALUE: Final[float] = 0.01
    MAX_PRICE_VALUE: Final[float] = 100_000.0
    
    # Volume validation
    MIN_VOLUME: Final[int] = 0
    MAX_VOLUME: Final[int] = 1_000_000_000
    
    # Temporal validation
    MAX_DATA_AGE_DAYS: Final[int] = 7
    MIN_BUSINESS_DAYS_THRESHOLD: Final[int] = 5

# Feature engineering constants
class FeatureConstants:
    """Constants for feature engineering."""
    
    # Default periods
    DEFAULT_MA_PERIODS: Final[List[int]] = [7, 30]
    DEFAULT_VOLATILITY_WINDOW: Final[int] = 20
    DEFAULT_RSI_PERIOD: Final[int] = 14
    DEFAULT_VOLUME_MA_PERIOD: Final[int] = 20
    
    # Volatility thresholds
    VOLATILITY_LOW_THRESHOLD: Final[float] = 0.02      # 2%
    VOLATILITY_MODERATE_THRESHOLD: Final[float] = 0.05  # 5%
    VOLATILITY_HIGH_THRESHOLD: Final[float] = 0.10     # 10%
    
    # Price momentum periods
    MOMENTUM_SHORT_PERIOD: Final[int] = 5
    MOMENTUM_LONG_PERIOD: Final[int] = 10

# Cleaning operation constants
class CleaningConstants:
    """Constants for data cleaning operations."""
    
    # Outlier detection
    IQR_DEFAULT_MULTIPLIER: Final[float] = 1.5
    ZSCORE_DEFAULT_THRESHOLD: Final[float] = 2.0
    
    # Missing value methods
    FORWARD_FILL: Final[str] = "forward_fill"
    BACKWARD_FILL: Final[str] = "backward_fill"
    INTERPOLATE: Final[str] = "interpolate"
    MEAN_FILL: Final[str] = "mean"
    
    # Outlier methods
    IQR_METHOD: Final[str] = "iqr"
    ZSCORE_METHOD: Final[str] = "zscore"
