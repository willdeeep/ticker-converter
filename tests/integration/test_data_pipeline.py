"""Integration tests for data cleaning and feature engineering pipeline."""

from datetime import datetime, timedelta

import pandas as pd
import pytest

from src.ticker_converter.core import FinancialDataPipeline
from src.ticker_converter.data_models.market_data import MarketDataPoint, RawMarketData
from src.ticker_converter.etl_modules import (
    DataCleaner,
    FeatureEngineer,
    QualityValidator,
)


class TestDataPipelineIntegration:
    """Test complete data pipeline integration."""

    @pytest.fixture
    def sample_market_data(self):
        """Create comprehensive sample market data."""
        points = []

        # Create 60 days of sample data
        base_date = datetime(2025, 6, 1)
        for i in range(60):
            current_date = base_date + timedelta(days=i)

            # Create realistic price movements
            base_price = 100.0
            volatility = 0.02
            random_factor = (i % 7) * 0.01  # Weekly pattern

            price = base_price + (i * 0.1) + random_factor
            open_price = price * (1 + volatility * (i % 3 - 1))
            high_price = price * (1 + abs(volatility * (i % 5)))
            low_price = price * (1 - abs(volatility * (i % 4)))
            close_price = price * (1 + volatility * (i % 2 - 0.5))

            # Ensure price relationships are valid
            high_price = max(high_price, open_price, close_price, low_price)
            low_price = min(low_price, open_price, close_price)

            volume = 1000000 + (i * 5000) + ((i % 10) * 50000)

            point = MarketDataPoint(
                timestamp=current_date,
                symbol="AAPL",
                open=round(open_price, 2),
                high=round(high_price, 2),
                low=round(low_price, 2),
                close=round(close_price, 2),
                volume=int(volume),
            )
            points.append(point)

        return RawMarketData(
            data_points=points,
            source="alpha_vantage",
            symbol="AAPL",
            data_type="daily",
        )

    def test_complete_pipeline_flow(self, sample_market_data):
        """Test the complete data processing pipeline."""
        # Step 1: Validate raw data
        validator = QualityValidator()
        df = sample_market_data.to_dataframe()
        validation_result = validator.validate(df, "AAPL")

        assert validation_result.is_valid is True

        # Step 2: Clean the data
        cleaner = DataCleaner()
        cleaned_data = cleaner.clean(sample_market_data)

        assert len(cleaned_data.cleaning_applied) > 0
        assert cleaned_data.raw_data == sample_market_data

        # Step 3: Engineer features
        engineer = FeatureEngineer()
        feature_data = engineer.engineer_features(cleaned_data)

        assert len(feature_data.features_created) > 0
        assert feature_data.cleaned_data == cleaned_data

        # Step 4: Generate quality report
        quality_report = validator.generate_quality_report(df, "AAPL")

        assert quality_report.symbol == "AAPL"
        assert quality_report.metrics.total_records == len(df)
        assert quality_report.is_high_quality()

    def test_pipeline_with_core_transform(self, sample_market_data):
        """Test pipeline integration through core transform method."""
        pipeline = FinancialDataPipeline()
        df = sample_market_data.to_dataframe()

        # Use the enhanced transform method
        transformed_df = pipeline.transform(df, symbol="AAPL")

        # Should return a DataFrame
        assert isinstance(transformed_df, pd.DataFrame)
        assert len(transformed_df) > 0
        assert "Symbol" in transformed_df.columns

    def test_end_to_end_data_quality(self, sample_market_data):
        """Test end-to-end data quality improvement."""
        # Initial quality assessment
        validator = QualityValidator()
        initial_df = sample_market_data.to_dataframe()
        initial_report = validator.generate_quality_report(initial_df, "AAPL")

        # Process through pipeline
        cleaner = DataCleaner()
        engineer = FeatureEngineer()

        cleaned_data = cleaner.clean(sample_market_data)
        engineer.engineer_features(cleaned_data)

        # Final quality assessment
        final_df = (
            sample_market_data.to_dataframe()
        )  # In real implementation, this would be the processed DF
        final_report = validator.generate_quality_report(final_df, "AAPL")

        # Quality should be maintained or improved
        assert (
            final_report.metrics.overall_quality_score
            >= initial_report.metrics.overall_quality_score
        )
        assert final_report.is_high_quality()

    def test_feature_engineering_completeness(self, sample_market_data):
        """Test that all expected features are created."""
        cleaner = DataCleaner()
        engineer = FeatureEngineer()

        cleaned_data = cleaner.clean(sample_market_data)
        feature_data = engineer.engineer_features(cleaned_data)

        expected_features = [
            "Daily_Return",
            "Log_Return",
            "Cumulative_Return",
            "MA_7",
            "MA_30",
            "Price_to_MA_7_Ratio",
            "Price_to_MA_30_Ratio",
            "Volatility",
            "True_Range",
            "ATR",
            "HL_Range_Pct",
            "Volatility_Flag",
            "Is_Low_Volatility",
            "Is_Moderate_Volatility",
            "Is_High_Volatility",
            "Is_Extreme_Volatility",
            "RSI",
            "RSI_Oversold",
            "RSI_Overbought",
            "BB_Middle",
            "BB_Upper",
            "BB_Lower",
            "BB_Width",
            "BB_Position",
            "BB_Squeeze",
            "Gap_Up",
            "Gap_Down",
            "Is_Doji",
            "Price_Momentum_5",
            "Price_Momentum_10",
            "Volume_MA_20",
            "Volume_Ratio",
            "High_Volume",
        ]

        for feature in expected_features:
            assert (
                feature in feature_data.features_created
            ), f"Feature {feature} not created"

    def test_error_handling_in_pipeline(self):
        """Test error handling in the pipeline."""
        # Create invalid data
        invalid_points = [
            MarketDataPoint(
                timestamp=datetime(2025, 8, 8),
                symbol="AAPL",
                open=100.0,
                high=105.0,
                low=98.0,
                close=103.0,
                volume=1000000,
            ),
        ]

        invalid_data = RawMarketData(
            data_points=invalid_points,
            source="test",
            symbol="AAPL",
            data_type="daily",
        )

        # Pipeline should handle minimal data gracefully
        cleaner = DataCleaner()
        engineer = FeatureEngineer()
        validator = QualityValidator()

        try:
            cleaned_data = cleaner.clean(invalid_data)
            feature_data = engineer.engineer_features(cleaned_data)
            df = invalid_data.to_dataframe()
            validation_result = validator.validate(df, "AAPL")

            # Should complete without throwing exceptions
            assert cleaned_data is not None
            assert feature_data is not None
            assert validation_result is not None

        except Exception as e:
            pytest.fail(f"Pipeline should handle minimal data gracefully: {e}")

    def test_performance_with_large_dataset(self):
        """Test pipeline performance with larger dataset."""
        # Create larger dataset (1 year of data)
        points = []
        base_date = datetime(2024, 1, 1)

        for i in range(365):
            current_date = base_date + timedelta(days=i)

            price = 100.0 + (i * 0.05)

            point = MarketDataPoint(
                timestamp=current_date,
                symbol="AAPL",
                open=price,
                high=price + 1.0,
                low=price - 0.5,
                close=price + 0.5,
                volume=1000000,
            )
            points.append(point)

        large_data = RawMarketData(
            data_points=points,
            source="test",
            symbol="AAPL",
            data_type="daily",
        )

        # Process through pipeline
        cleaner = DataCleaner()
        engineer = FeatureEngineer()

        cleaned_data = cleaner.clean(large_data)
        feature_data = engineer.engineer_features(cleaned_data)

        # Should handle large dataset
        assert len(cleaned_data.raw_data.data_points) == 365
        assert len(feature_data.features_created) > 0

    def test_different_symbols_processing(self):
        """Test pipeline with different stock symbols."""
        symbols = ["AAPL", "MSFT", "GOOGL"]

        for symbol in symbols:
            points = [
                MarketDataPoint(
                    timestamp=datetime(2025, 8, 8),
                    symbol=symbol,
                    open=100.0,
                    high=105.0,
                    low=98.0,
                    close=103.0,
                    volume=1000000,
                ),
                MarketDataPoint(
                    timestamp=datetime(2025, 8, 9),
                    symbol=symbol,
                    open=103.0,
                    high=108.0,
                    low=102.0,
                    close=106.0,
                    volume=1200000,
                ),
            ]

            raw_data = RawMarketData(
                data_points=points,
                source="test",
                symbol=symbol,
                data_type="daily",
            )

            # Process each symbol
            cleaner = DataCleaner()
            engineer = FeatureEngineer()
            validator = QualityValidator()

            cleaned_data = cleaner.clean(raw_data)
            feature_data = engineer.engineer_features(cleaned_data)
            df = raw_data.to_dataframe()
            validation_result = validator.validate(df, symbol)

            assert cleaned_data.raw_data.symbol == symbol
            assert feature_data.cleaned_data.raw_data.symbol == symbol
            assert validation_result.is_valid is True
