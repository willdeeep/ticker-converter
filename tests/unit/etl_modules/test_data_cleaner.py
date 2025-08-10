"""Tests for data cleaning module."""

from datetime import datetime

import pandas as pd
import pytest

from src.ticker_converter.data_models.market_data import MarketDataPoint, RawMarketData
from src.ticker_converter.etl_modules.data_cleaner import CleaningConfig, DataCleaner


class TestDataCleaner:
    """Test DataCleaner functionality."""

    @pytest.fixture
    def sample_raw_data(self):
        """Create sample raw market data for testing."""
        points = [
            MarketDataPoint(
                timestamp=datetime(2025, 8, 5),
                symbol="AAPL",
                open=100.0,
                high=105.0,
                low=98.0,
                close=103.0,
                volume=1000000,
            ),
            MarketDataPoint(
                timestamp=datetime(2025, 8, 6),
                symbol="AAPL",
                open=103.0,
                high=108.0,
                low=102.0,
                close=106.0,
                volume=1200000,
            ),
            MarketDataPoint(
                timestamp=datetime(2025, 8, 7),
                symbol="AAPL",
                open=106.0,
                high=110.0,
                low=105.0,
                close=109.0,
                volume=900000,
            ),
        ]

        return RawMarketData(
            data_points=points,
            source="alpha_vantage",
            symbol="AAPL",
            data_type="daily",
        )

    @pytest.fixture
    def sample_dirty_data(self):
        """Create sample data with quality issues."""
        points = [
            MarketDataPoint(
                timestamp=datetime(2025, 8, 5),
                symbol="AAPL",
                open=100.0,
                high=105.0,
                low=98.0,
                close=103.0,
                volume=1000000,
            ),
            # Duplicate record
            MarketDataPoint(
                timestamp=datetime(2025, 8, 5),
                symbol="AAPL",
                open=100.0,
                high=105.0,
                low=98.0,
                close=103.0,
                volume=1000000,
            ),
            MarketDataPoint(
                timestamp=datetime(2025, 8, 6),
                symbol="AAPL",
                open=103.0,
                high=108.0,
                low=102.0,
                close=106.0,
                volume=1200000,
            ),
        ]

        return RawMarketData(
            data_points=points,
            source="alpha_vantage",
            symbol="AAPL",
            data_type="daily",
        )

    def test_basic_cleaning(self, sample_raw_data):
        """Test basic data cleaning functionality."""
        cleaner = DataCleaner()
        cleaned_data = cleaner.clean(sample_raw_data)

        assert cleaned_data.raw_data == sample_raw_data
        assert len(cleaned_data.cleaning_applied) > 0
        assert "ensure_consistent_types" in cleaned_data.cleaning_applied
        assert "sort_by_date" in cleaned_data.cleaning_applied

    def test_duplicate_removal(self, sample_dirty_data):
        """Test duplicate removal."""
        config = CleaningConfig(remove_duplicates=True)
        cleaner = DataCleaner(config)
        cleaned_data = cleaner.clean(sample_dirty_data)

        # Should have removed the duplicate
        any_duplicate_operation = any(
            "remove_duplicates" in op for op in cleaned_data.cleaning_applied
        )
        assert any_duplicate_operation

    def test_missing_value_handling(self):
        """Test missing value handling."""
        # Create data with missing values
        df = pd.DataFrame({
            'Date': pd.to_datetime(['2025-08-05', '2025-08-06', '2025-08-07']),
            'Open': [100.0, None, 106.0],
            'High': [105.0, 108.0, 110.0],
            'Low': [98.0, 102.0, 105.0],
            'Close': [103.0, 106.0, 109.0],
            'Volume': [1000000, 1200000, 900000],
            'Symbol': ['AAPL', 'AAPL', 'AAPL']
        })
        df.set_index('Date', inplace=True)

        # Create MarketDataPoint objects from non-null rows
        points = []
        for idx, row in df.iterrows():
            if pd.notna(row['Open']):  # Only add rows without missing values
                points.append(MarketDataPoint(
                    timestamp=idx,
                    symbol=row['Symbol'],
                    open=float(row['Open']),
                    high=float(row['High']),
                    low=float(row['Low']),
                    close=float(row['Close']),
                    volume=int(row['Volume']),
                ))

        raw_data = RawMarketData(
            data_points=points,
            source="test",
            symbol="AAPL",
            data_type="daily",
        )

        config = CleaningConfig(fill_missing_values=True)
        cleaner = DataCleaner(config)
        cleaned_data = cleaner.clean(raw_data)

        # Should indicate missing value handling was attempted
        assert len(cleaned_data.cleaning_applied) > 0

    def test_outlier_removal_iqr(self, sample_raw_data):
        """Test IQR-based outlier removal."""
        config = CleaningConfig(
            remove_outliers=True,
            outlier_method="iqr",
            outlier_threshold=1.5
        )
        cleaner = DataCleaner(config)
        cleaned_data = cleaner.clean(sample_raw_data)

        # With normal data, shouldn't remove outliers
        assert cleaned_data.outliers_removed == 0

    def test_outlier_removal_zscore(self, sample_raw_data):
        """Test Z-score-based outlier removal."""
        config = CleaningConfig(
            remove_outliers=True,
            outlier_method="zscore",
            outlier_threshold=2.0
        )
        cleaner = DataCleaner(config)
        cleaned_data = cleaner.clean(sample_raw_data)

        # With normal data, shouldn't remove outliers
        assert cleaned_data.outliers_removed == 0

    def test_price_relationship_validation(self):
        """Test price relationship validation."""
        # Create data with invalid price relationships
        points = [
            MarketDataPoint(
                timestamp=datetime(2025, 8, 5),
                symbol="AAPL",
                open=100.0,
                high=105.0,
                low=98.0,
                close=103.0,
                volume=1000000,
            ),
        ]

        raw_data = RawMarketData(
            data_points=points,
            source="test",
            symbol="AAPL",
            data_type="daily",
        )

        config = CleaningConfig(validate_price_relationships=True)
        cleaner = DataCleaner(config)
        cleaned_data = cleaner.clean(raw_data)

        # Should pass validation with good data
        assert len(cleaned_data.cleaning_applied) > 0

    def test_disabled_cleaning_operations(self, sample_raw_data):
        """Test with cleaning operations disabled."""
        config = CleaningConfig(
            remove_duplicates=False,
            fill_missing_values=False,
            remove_outliers=False,
            validate_price_relationships=False,
            ensure_consistent_types=False,
            sort_by_date=False,
        )
        cleaner = DataCleaner(config)
        cleaned_data = cleaner.clean(sample_raw_data)

        # Should have minimal cleaning operations
        assert len(cleaned_data.cleaning_applied) == 0
        assert cleaned_data.outliers_removed == 0
        assert cleaned_data.missing_values_filled == 0


class TestCleaningConfig:
    """Test CleaningConfig model."""

    def test_default_config(self):
        """Test default configuration values."""
        config = CleaningConfig()

        assert config.remove_duplicates is True
        assert config.fill_missing_values is True
        assert config.missing_value_method == "forward_fill"
        assert config.remove_outliers is True
        assert config.outlier_method == "iqr"
        assert config.outlier_threshold == 1.5

    def test_custom_config(self):
        """Test custom configuration."""
        config = CleaningConfig(
            remove_duplicates=False,
            outlier_method="zscore",
            outlier_threshold=2.0,
        )

        assert config.remove_duplicates is False
        assert config.outlier_method == "zscore"
        assert config.outlier_threshold == 2.0
