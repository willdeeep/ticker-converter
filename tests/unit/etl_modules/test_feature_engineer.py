"""Tests for feature engineering module."""

from datetime import datetime

import pandas as pd
import pytest

from src.ticker_converter.data_models.market_data import (
    CleanedMarketData,
    MarketDataPoint,
    RawMarketData,
    VolatilityFlag,
)
from src.ticker_converter.etl_modules.feature_engineer import FeatureConfig, FeatureEngineer


class TestFeatureEngineer:
    """Test FeatureEngineer functionality."""

    @pytest.fixture
    def sample_cleaned_data(self):
        """Create sample cleaned market data for testing."""
        points = []

        # Create 30 days of sample data for testing moving averages
        base_date = datetime(2025, 7, 1)
        for i in range(30):
            current_date = datetime(base_date.year, base_date.month, base_date.day + i)
            price = 100.0 + i * 0.5  # Gradual price increase

            point = MarketDataPoint(
                timestamp=current_date,
                symbol="AAPL",
                open=price,
                high=price + 2.0,
                low=price - 1.0,
                close=price + 1.0,
                volume=1000000 + i * 10000,
            )
            points.append(point)

        raw_data = RawMarketData(
            data_points=points,
            source="alpha_vantage",
            symbol="AAPL",
            data_type="daily",
        )

        return CleanedMarketData(
            raw_data=raw_data,
            cleaning_applied=["test_cleaning"],
            outliers_removed=0,
            missing_values_filled=0,
        )

    def test_basic_feature_engineering(self, sample_cleaned_data):
        """Test basic feature engineering functionality."""
        engineer = FeatureEngineer()
        feature_data = engineer.engineer_features(sample_cleaned_data)

        assert feature_data.cleaned_data == sample_cleaned_data
        assert len(feature_data.features_created) > 0
        assert feature_data.ma_periods == [7, 30]  # Default periods

    def test_moving_averages(self, sample_cleaned_data):
        """Test moving average calculations."""
        config = FeatureConfig(moving_averages=[5, 10])
        engineer = FeatureEngineer(config)
        feature_data = engineer.engineer_features(sample_cleaned_data)

        # Check that MA features were created
        ma_features = [f for f in feature_data.features_created if "MA_" in f]
        assert "MA_5" in feature_data.features_created
        assert "MA_10" in feature_data.features_created
        assert "Price_to_MA_5_Ratio" in feature_data.features_created
        assert "Price_to_MA_10_Ratio" in feature_data.features_created

    def test_return_calculations(self, sample_cleaned_data):
        """Test return calculations."""
        config = FeatureConfig(calculate_returns=True)
        engineer = FeatureEngineer(config)
        feature_data = engineer.engineer_features(sample_cleaned_data)

        # Check that return features were created
        assert "Daily_Return" in feature_data.features_created
        assert "Log_Return" in feature_data.features_created
        assert "Cumulative_Return" in feature_data.features_created

    def test_volatility_metrics(self, sample_cleaned_data):
        """Test volatility metric calculations."""
        config = FeatureConfig(
            calculate_volatility=True,
            volatility_window=10
        )
        engineer = FeatureEngineer(config)
        feature_data = engineer.engineer_features(sample_cleaned_data)

        # Check that volatility features were created
        assert "Volatility" in feature_data.features_created
        assert "True_Range" in feature_data.features_created
        assert "ATR" in feature_data.features_created
        assert "HL_Range_Pct" in feature_data.features_created

    def test_volatility_flags(self, sample_cleaned_data):
        """Test volatility flag calculations."""
        config = FeatureConfig(
            calculate_volatility=True,
            volatility_threshold_low=0.01,
            volatility_threshold_moderate=0.03,
            volatility_threshold_high=0.05,
        )
        engineer = FeatureEngineer(config)
        feature_data = engineer.engineer_features(sample_cleaned_data)

        # Check that volatility flag features were created
        assert "Volatility_Flag" in feature_data.features_created
        assert "Is_Low_Volatility" in feature_data.features_created
        assert "Is_Moderate_Volatility" in feature_data.features_created
        assert "Is_High_Volatility" in feature_data.features_created
        assert "Is_Extreme_Volatility" in feature_data.features_created

    def test_rsi_calculation(self, sample_cleaned_data):
        """Test RSI indicator calculation."""
        config = FeatureConfig(
            calculate_rsi=True,
            rsi_period=14
        )
        engineer = FeatureEngineer(config)
        feature_data = engineer.engineer_features(sample_cleaned_data)

        # Check that RSI features were created
        assert "RSI" in feature_data.features_created
        assert "RSI_Oversold" in feature_data.features_created
        assert "RSI_Overbought" in feature_data.features_created

    def test_bollinger_bands(self, sample_cleaned_data):
        """Test Bollinger Bands calculation."""
        config = FeatureConfig(
            calculate_bollinger_bands=True,
            bollinger_period=20,
            bollinger_std=2.0
        )
        engineer = FeatureEngineer(config)
        feature_data = engineer.engineer_features(sample_cleaned_data)

        # Check that Bollinger Band features were created
        assert "BB_Middle" in feature_data.features_created
        assert "BB_Upper" in feature_data.features_created
        assert "BB_Lower" in feature_data.features_created
        assert "BB_Width" in feature_data.features_created
        assert "BB_Position" in feature_data.features_created
        assert "BB_Squeeze" in feature_data.features_created

    def test_price_features(self, sample_cleaned_data):
        """Test price-based feature calculations."""
        engineer = FeatureEngineer()
        feature_data = engineer.engineer_features(sample_cleaned_data)

        # Check that price features were created
        assert "Gap_Up" in feature_data.features_created
        assert "Gap_Down" in feature_data.features_created
        assert "Is_Doji" in feature_data.features_created
        assert "Price_Momentum_5" in feature_data.features_created
        assert "Price_Momentum_10" in feature_data.features_created

    def test_volume_features(self, sample_cleaned_data):
        """Test volume-based feature calculations."""
        engineer = FeatureEngineer()
        feature_data = engineer.engineer_features(sample_cleaned_data)

        # Check that volume features were created
        assert "Volume_MA_20" in feature_data.features_created
        assert "Volume_Ratio" in feature_data.features_created
        assert "High_Volume" in feature_data.features_created

    def test_disabled_features(self, sample_cleaned_data):
        """Test with features disabled."""
        config = FeatureConfig(
            calculate_returns=False,
            calculate_volatility=False,
            calculate_rsi=False,
            calculate_bollinger_bands=False,
        )
        engineer = FeatureEngineer(config)
        feature_data = engineer.engineer_features(sample_cleaned_data)

        # Should still have moving averages and price features
        assert len(feature_data.features_created) > 0
        # But not return features
        assert "Daily_Return" not in feature_data.features_created
        assert "Volatility" not in feature_data.features_created
        assert "RSI" not in feature_data.features_created
        assert "BB_Middle" not in feature_data.features_created

    def test_custom_thresholds(self, sample_cleaned_data):
        """Test custom volatility thresholds."""
        config = FeatureConfig(
            volatility_threshold_low=0.005,
            volatility_threshold_moderate=0.015,
            volatility_threshold_high=0.025,
        )
        engineer = FeatureEngineer(config)
        feature_data = engineer.engineer_features(sample_cleaned_data)

        assert feature_data.volatility_threshold_low == 0.005
        assert feature_data.volatility_threshold_moderate == 0.015
        assert feature_data.volatility_threshold_high == 0.025


class TestFeatureConfig:
    """Test FeatureConfig model."""

    def test_default_config(self):
        """Test default configuration values."""
        config = FeatureConfig()

        assert config.moving_averages == [7, 30]
        assert config.calculate_returns is True
        assert config.calculate_volatility is True
        assert config.volatility_window == 20
        assert config.volatility_threshold_low == 0.02
        assert config.volatility_threshold_moderate == 0.05
        assert config.volatility_threshold_high == 0.10
        assert config.calculate_rsi is True
        assert config.rsi_period == 14
        assert config.calculate_bollinger_bands is True
        assert config.bollinger_period == 20
        assert config.bollinger_std == 2.0

    def test_custom_config(self):
        """Test custom configuration."""
        config = FeatureConfig(
            moving_averages=[5, 15, 30],
            calculate_returns=False,
            volatility_window=10,
            rsi_period=21,
        )

        assert config.moving_averages == [5, 15, 30]
        assert config.calculate_returns is False
        assert config.volatility_window == 10
        assert config.rsi_period == 21
