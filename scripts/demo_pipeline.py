#!/usr/bin/env python3
"""Demonstration script for the data cleaning and feature engineering pipeline."""

import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import logging
from datetime import datetime, timedelta

from ticker_converter.data_models.market_data import MarketDataPoint, RawMarketData
from ticker_converter.etl_modules import DataCleaner, FeatureEngineer, QualityValidator
from ticker_converter.etl_modules.data_cleaner import CleaningConfig
from ticker_converter.etl_modules.feature_engineer import FeatureConfig

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def create_sample_data(symbol: str = "AAPL", days: int = 30) -> RawMarketData:
    """Create sample market data for demonstration."""
    logger.info(f"Creating {days} days of sample data for {symbol}")

    points = []
    base_date = datetime(2025, 7, 1)
    base_price = 150.0

    for i in range(days):
        current_date = base_date + timedelta(days=i)

        # Simulate price movements with some volatility
        price_change = (i % 7 - 3) * 0.02  # Weekly pattern
        daily_volatility = 0.015 * ((i % 5) + 1)  # Variable volatility

        open_price = base_price + (i * 0.1) + price_change
        high_price = open_price + daily_volatility * open_price
        low_price = open_price - daily_volatility * open_price
        close_price = open_price + (price_change * 0.5)

        # Ensure price relationships are valid
        high_price = max(high_price, open_price, close_price)
        low_price = min(low_price, open_price, close_price)

        volume = int(1000000 + (i * 5000) + ((i % 10) * 50000))

        point = MarketDataPoint(
            timestamp=current_date,
            symbol=symbol,
            open=round(open_price, 2),
            high=round(high_price, 2),
            low=round(low_price, 2),
            close=round(close_price, 2),
            volume=volume,
        )
        points.append(point)

    return RawMarketData(
        data_points=points,
        source="demo",
        symbol=symbol,
        data_type="daily",
    )


def demonstrate_pipeline():
    """Demonstrate the complete data cleaning and feature engineering pipeline."""
    print("=" * 80)
    print("Financial Market Data Analytics Pipeline - Demo")
    print("Data Cleaning and Feature Engineering")
    print("=" * 80)

    # Step 1: Create sample data
    print("\n1. Creating Sample Market Data")
    print("-" * 40)

    raw_data = create_sample_data("AAPL", 60)
    df = raw_data.to_dataframe()

    print(f"Created data for {raw_data.symbol}")
    print(f"Data points: {len(raw_data.data_points)}")
    print(f"Date range: {df.index.min()} to {df.index.max()}")
    print(f"Price range: ${df['Close'].min():.2f} - ${df['Close'].max():.2f}")
    print(f"Average volume: {df['Volume'].mean():,.0f}")

    # Step 2: Quality validation (initial)
    print("\n2. Initial Data Quality Assessment")
    print("-" * 40)

    validator = QualityValidator()
    initial_validation = validator.validate(df, "AAPL")

    print(f"Data is valid: {initial_validation.is_valid}")
    if initial_validation.errors:
        print(f"Errors: {len(initial_validation.errors)}")
    if initial_validation.warnings:
        print(f"Warnings: {len(initial_validation.warnings)}")

    # Generate quality report
    quality_report = validator.generate_quality_report(df, "AAPL")
    print(f"Overall quality score: {quality_report.metrics.overall_quality_score:.3f}")

    # Step 3: Data cleaning
    print("\n3. Data Cleaning")
    print("-" * 40)

    cleaning_config = CleaningConfig(
        remove_duplicates=True,
        fill_missing_values=True,
        missing_value_method="forward_fill",
        remove_outliers=True,
        outlier_method="iqr",
        outlier_threshold=1.5,
    )

    cleaner = DataCleaner(cleaning_config)
    cleaned_data = cleaner.clean(raw_data)

    print(f"Cleaning operations applied: {len(cleaned_data.cleaning_applied)}")
    for operation in cleaned_data.cleaning_applied:
        print(f"  - {operation}")
    print(f"Outliers removed: {cleaned_data.outliers_removed}")
    print(f"Missing values filled: {cleaned_data.missing_values_filled}")

    # Step 4: Feature engineering
    print("\n4. Feature Engineering")
    print("-" * 40)

    feature_config = FeatureConfig(
        moving_averages=[7, 20, 50],
        calculate_returns=True,
        calculate_volatility=True,
        volatility_window=20,
        calculate_rsi=True,
        rsi_period=14,
        calculate_bollinger_bands=True,
    )

    engineer = FeatureEngineer(feature_config)
    feature_data = engineer.engineer_features(cleaned_data)

    print(f"Features created: {len(feature_data.features_created)}")
    print("Feature categories:")

    # Categorize features
    return_features = [f for f in feature_data.features_created if "Return" in f]
    ma_features = [f for f in feature_data.features_created if "MA_" in f]
    volatility_features = [
        f for f in feature_data.features_created if "Volatility" in f or "ATR" in f
    ]
    technical_features = [
        f for f in feature_data.features_created if "RSI" in f or "BB_" in f
    ]

    print(f"  - Returns: {len(return_features)} features")
    print(f"  - Moving Averages: {len(ma_features)} features")
    print(f"  - Volatility: {len(volatility_features)} features")
    print(f"  - Technical Indicators: {len(technical_features)} features")

    # Step 5: Final quality assessment
    print("\n5. Final Quality Assessment")
    print("-" * 40)

    validator.validate(df, "AAPL")
    final_quality_report = validator.generate_quality_report(df, "AAPL")

    print(
        f"Final quality score: {final_quality_report.metrics.overall_quality_score:.3f}"
    )
    print(f"Completeness: {final_quality_report.metrics.completeness_score:.3f}")
    print(f"Consistency: {final_quality_report.metrics.consistency_score:.3f}")
    print(f"Validity: {final_quality_report.metrics.validity_score:.3f}")

    if final_quality_report.is_high_quality():
        print("Data meets high quality standards!")
    else:
        print("⚠️  Data quality could be improved")

    # Step 6: Sample feature values
    print("\n6. Sample Feature Values (Latest Data Point)")
    print("-" * 40)

    # Since we can't directly access the processed DataFrame in this demo,
    # let's show some calculated values
    latest_data = raw_data.data_points[-1]
    print(f"Date: {latest_data.timestamp}")
    print(f"Close Price: ${latest_data.close:.2f}")
    print(f"Volume: {latest_data.volume:,}")

    # Calculate some simple features for demo
    recent_closes = [p.close for p in raw_data.data_points[-20:]]
    ma_20 = sum(recent_closes) / len(recent_closes)
    print(f"20-day MA: ${ma_20:.2f}")

    if len(raw_data.data_points) >= 2:
        prev_close = raw_data.data_points[-2].close
        daily_return = (latest_data.close - prev_close) / prev_close
        print(f"Daily Return: {daily_return:.3%}")

    # Volatility threshold classification
    for threshold_name, threshold_val in [
        ("Low", feature_data.volatility_threshold_low),
        ("Moderate", feature_data.volatility_threshold_moderate),
        ("High", feature_data.volatility_threshold_high),
    ]:
        print(f"Volatility Threshold ({threshold_name}): {threshold_val:.1%}")

    print("\n" + "=" * 80)
    print("Pipeline demonstration completed successfully!")
    print("Data has been cleaned, features engineered, and quality validated.")
    print("=" * 80)


if __name__ == "__main__":
    demonstrate_pipeline()
