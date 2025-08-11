# Data Cleaning and Feature Engineering Pipeline

This document describes the data cleaning and feature engineering pipeline implemented for the Financial Market Data Analytics Pipeline.

## Overview

The pipeline consists of three main components:

1. **DataCleaner**: Cleans and validates raw market data
2. **FeatureEngineer**: Creates engineered features for analysis
3. **QualityValidator**: Validates data quality and generates reports

## Architecture

```
Raw Market Data → Data Cleaning → Feature Engineering → Quality Validation
                     ↓               ↓                    ↓
                 CleanedData    FeatureEngineeredData  QualityReport
```

## Data Models

### MarketDataPoint
Represents a single market data observation with validation:
- `timestamp`: Date and time of the observation
- `symbol`: Stock ticker symbol
- `open`, `high`, `low`, `close`: OHLC prices (validated for relationships)
- `volume`: Trading volume (non-negative)

### RawMarketData
Collection of market data points with metadata:
- `data_points`: List of MarketDataPoint objects
- `source`: Data source (e.g., "alpha_vantage")
- `symbol`: Primary symbol for the dataset
- `data_type`: Type of data (e.g., "daily", "intraday")

### CleanedMarketData
Result of data cleaning operations:
- `raw_data`: Original raw data
- `cleaning_applied`: List of cleaning operations performed
- `outliers_removed`: Count of outliers removed
- `missing_values_filled`: Count of missing values filled

### FeatureEngineeredData
Result of feature engineering:
- `cleaned_data`: Source cleaned data
- `features_created`: List of engineered features
- `ma_periods`: Moving average periods used
- Volatility thresholds configuration

## Data Cleaning Operations

### 1. Type Consistency
- Ensures numeric columns are proper numeric types
- Converts Volume to integer
- Standardizes Symbol as string

### 2. Duplicate Removal
- Removes duplicate records based on date and symbol
- Keeps the first occurrence of duplicates

### 3. Price Relationship Validation
- Removes rows where High < Low
- Removes rows where Close is outside High/Low range
- Removes rows with non-positive prices

### 4. Missing Value Handling
Methods available:
- `forward_fill`: Forward fill missing values
- `backward_fill`: Backward fill missing values
- `interpolate`: Linear interpolation
- `mean`: Fill with column mean

### 5. Outlier Detection and Removal
Methods available:
- `iqr`: Interquartile Range method
- `zscore`: Z-score method

Configuration parameters:
- `outlier_threshold`: Multiplier for outlier detection (default: 1.5 for IQR)

## Feature Engineering

### Price-Based Features

#### Returns
- `Daily_Return`: Daily percentage return
- `Log_Return`: Logarithmic return
- `Cumulative_Return`: Cumulative return from start

#### Moving Averages
- `MA_N`: N-period moving average (configurable periods)
- `Price_to_MA_N_Ratio`: Current price to moving average ratio

#### Price Patterns
- `Gap_Up`: Boolean flag for gap up patterns
- `Gap_Down`: Boolean flag for gap down patterns
- `Is_Doji`: Boolean flag for doji candlestick patterns
- `Price_Momentum_N`: N-period price momentum

### Volatility Features

#### Basic Volatility
- `Volatility`: Rolling standard deviation of returns
- `True_Range`: True Range calculation
- `ATR`: Average True Range
- `HL_Range_Pct`: High-Low range as percentage of close

#### Volatility Classification
- `Volatility_Flag`: Categorical volatility classification
- `Is_Low_Volatility`: Boolean flag for low volatility
- `Is_Moderate_Volatility`: Boolean flag for moderate volatility
- `Is_High_Volatility`: Boolean flag for high volatility
- `Is_Extreme_Volatility`: Boolean flag for extreme volatility

Thresholds (configurable):
- Low: < 2%
- Moderate: 2-5%
- High: 5-10%
- Extreme: > 10%

### Technical Indicators

#### RSI (Relative Strength Index)
- `RSI`: RSI value (0-100)
- `RSI_Oversold`: Boolean flag for RSI < 30
- `RSI_Overbought`: Boolean flag for RSI > 70

#### Bollinger Bands
- `BB_Middle`: Middle band (SMA)
- `BB_Upper`: Upper band
- `BB_Lower`: Lower band
- `BB_Width`: Band width
- `BB_Position`: Position within bands (0-1)
- `BB_Squeeze`: Boolean flag for band squeeze

### Volume Features
- `Volume_MA_20`: 20-period volume moving average
- `Volume_Ratio`: Current volume to average ratio
- `High_Volume`: Boolean flag for high volume days

## Quality Validation

### Validation Checks

#### Completeness
- Measures percentage of non-null values
- Configurable threshold (default: 95%)

#### Consistency
- Validates price relationships
- Checks for duplicate records
- Ensures consistent symbols

#### Validity
- Validates price ranges
- Checks for negative values
- Detects extreme price movements

#### Timeliness
- Checks data freshness
- Identifies date gaps in time series

### Quality Metrics

#### Scores (0-1 scale)
- `completeness_score`: Data completeness ratio
- `consistency_score`: Data consistency measure
- `validity_score`: Data validity measure
- `overall_quality_score`: Weighted average of all scores

#### Detailed Metrics
- `total_records`: Total number of records
- `complete_records`: Records with no missing values
- `missing_value_count`: Total missing values
- `duplicate_count`: Number of duplicates
- `outlier_count`: Number of outliers
- `negative_prices`: Count of negative price values
- `price_anomalies`: Count of price anomalies

## Configuration

### CleaningConfig
```python
CleaningConfig(
    remove_duplicates=True,
    fill_missing_values=True,
    missing_value_method="forward_fill",
    remove_outliers=True,
    outlier_method="iqr",
    outlier_threshold=1.5,
    validate_price_relationships=True,
    ensure_consistent_types=True,
    sort_by_date=True
)
```

### FeatureConfig
```python
FeatureConfig(
    moving_averages=[7, 30],
    calculate_returns=True,
    calculate_volatility=True,
    volatility_window=20,
    volatility_threshold_low=0.02,
    volatility_threshold_moderate=0.05,
    volatility_threshold_high=0.10,
    calculate_rsi=True,
    rsi_period=14,
    calculate_bollinger_bands=True,
    bollinger_period=20,
    bollinger_std=2.0
)
```

### ValidationConfig
```python
ValidationConfig(
    check_completeness=True,
    check_consistency=True,
    check_validity=True,
    check_timeliness=True,
    min_completeness_score=0.95,
    min_consistency_score=0.90,
    min_validity_score=0.95,
    max_daily_price_change=0.20,
    min_price_value=0.01,
    max_price_value=100000.0,
    max_data_age_days=7
)
```

## Usage Examples

### Basic Pipeline Usage
```python
from src.ticker_converter.etl_modules import DataCleaner, FeatureEngineer, QualityValidator
from src.ticker_converter.data_models.market_data import RawMarketData

# Initialize components
cleaner = DataCleaner()
engineer = FeatureEngineer()
validator = QualityValidator()

# Process data
cleaned_data = cleaner.clean(raw_market_data)
feature_data = engineer.engineer_features(cleaned_data)

# Validate quality
df = raw_market_data.to_dataframe()
validation_result = validator.validate(df, "AAPL")
quality_report = validator.generate_quality_report(df, "AAPL")
```

### Custom Configuration
```python
from src.ticker_converter.etl_modules.data_cleaner import CleaningConfig
from src.ticker_converter.etl_modules.feature_engineer import FeatureConfig

# Custom cleaning configuration
cleaning_config = CleaningConfig(
    outlier_method="zscore",
    outlier_threshold=2.0,
    missing_value_method="interpolate"
)

# Custom feature configuration
feature_config = FeatureConfig(
    moving_averages=[5, 10, 20, 50],
    volatility_threshold_low=0.01,
    rsi_period=21
)

cleaner = DataCleaner(cleaning_config)
engineer = FeatureEngineer(feature_config)
```

### Integration with Core Pipeline
```python
from src.ticker_converter.core import FinancialDataPipeline

pipeline = FinancialDataPipeline()
df = pipeline.fetch_stock_data("AAPL", "1mo")

# Enhanced transform with cleaning and feature engineering
transformed_df = pipeline.transform(df, symbol="AAPL")
```

## Error Handling and Logging

The pipeline includes comprehensive error handling and logging:

- **Validation Errors**: Captured in ValidationResult objects
- **Processing Warnings**: Logged but don't stop processing
- **Exception Handling**: Graceful degradation with informative error messages
- **Progress Logging**: Detailed logging of operations performed

## Performance Considerations

- **Idempotent Operations**: All transformations are designed to be idempotent
- **Memory Efficient**: Uses pandas operations optimized for performance
- **Configurable Processing**: Can disable expensive operations if not needed
- **Batch Processing**: Designed to handle large datasets efficiently

## Testing

Comprehensive test suite includes:

- **Unit Tests**: Individual component testing
- **Integration Tests**: End-to-end pipeline testing
- **Performance Tests**: Large dataset handling
- **Error Handling Tests**: Edge case validation

Test coverage includes:
- Data model validation
- Cleaning operations
- Feature engineering algorithms
- Quality validation logic
- Configuration management
- Error scenarios
