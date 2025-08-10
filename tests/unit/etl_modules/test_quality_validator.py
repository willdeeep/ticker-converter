"""Tests for quality validation module."""

from datetime import datetime, timedelta

import pandas as pd
import pytest

from src.ticker_converter.etl_modules.quality_validator import (
    QualityValidator,
    ValidationConfig,
)


class TestQualityValidator:
    """Test QualityValidator functionality."""

    @pytest.fixture
    def good_data(self):
        """Create sample good quality data."""
        dates = pd.date_range(start="2025-08-01", end="2025-08-10", freq="D")
        data = []

        for i, date in enumerate(dates):
            data.append({
                "Date": date,
                "Symbol": "AAPL",
                "Open": 100.0 + i,
                "High": 105.0 + i,
                "Low": 98.0 + i,
                "Close": 103.0 + i,
                "Volume": 1000000 + i * 10000,
            })

        df = pd.DataFrame(data)
        df.set_index("Date", inplace=True)
        return df

    @pytest.fixture
    def bad_data(self):
        """Create sample poor quality data."""
        dates = pd.date_range(start="2025-08-01", end="2025-08-05", freq="D")
        data = []

        for i, date in enumerate(dates):
            data.append({
                "Date": date,
                "Symbol": "AAPL",
                "Open": 100.0 + i if i != 2 else None,  # Missing value
                "High": 95.0 + i if i != 1 else 105.0 + i,  # High < Low for i=1
                "Low": 98.0 + i,
                "Close": 90.0 if i == 3 else 103.0 + i,  # Negative price change
                "Volume": -1000 if i == 4 else 1000000 + i * 10000,  # Negative volume
            })

        df = pd.DataFrame(data)
        df.set_index("Date", inplace=True)
        return df

    def test_validate_good_data(self, good_data):
        """Test validation of good quality data."""
        validator = QualityValidator()
        result = validator.validate(good_data, "AAPL")

        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_validate_bad_data(self, bad_data):
        """Test validation of poor quality data."""
        validator = QualityValidator()
        result = validator.validate(bad_data, "AAPL")

        assert result.is_valid is False
        assert len(result.errors) > 0

    def test_completeness_check(self, bad_data):
        """Test completeness validation."""
        config = ValidationConfig(
            check_completeness=True,
            min_completeness_score=0.95
        )
        validator = QualityValidator(config)
        result = validator.validate(bad_data, "AAPL")

        # Should have warnings about missing values
        assert len(result.warnings) > 0 or len(result.errors) > 0

    def test_consistency_check(self, bad_data):
        """Test consistency validation."""
        config = ValidationConfig(check_consistency=True)
        validator = QualityValidator(config)
        result = validator.validate(bad_data, "AAPL")

        # Should detect price relationship errors
        assert result.is_valid is False
        assert any("High < Low" in error for error in result.errors)

    def test_validity_check(self, bad_data):
        """Test validity validation."""
        config = ValidationConfig(
            check_validity=True,
            min_price_value=0.01,
            max_daily_price_change=0.20
        )
        validator = QualityValidator(config)
        result = validator.validate(bad_data, "AAPL")

        # Should detect negative volume
        assert result.is_valid is False
        assert any("negative volume" in error.lower() for error in result.errors)

    def test_timeliness_check(self, good_data):
        """Test timeliness validation."""
        # Create old data to test timeliness
        old_dates = pd.date_range(start="2024-01-01", end="2024-01-10", freq="D")
        old_data = []

        for i, date in enumerate(old_dates):
            old_data.append({
                "Date": date,
                "Symbol": "AAPL",
                "Open": 100.0 + i,
                "High": 105.0 + i,
                "Low": 98.0 + i,
                "Close": 103.0 + i,
                "Volume": 1000000 + i * 10000,
            })

        old_df = pd.DataFrame(old_data)
        old_df.set_index("Date", inplace=True)

        config = ValidationConfig(
            check_timeliness=True,
            max_data_age_days=30  # Data from 2024 should be too old
        )
        validator = QualityValidator(config)
        result = validator.validate(old_df, "AAPL")

        # Should warn about data age
        assert len(result.warnings) > 0

    def test_generate_quality_report(self, good_data):
        """Test quality report generation."""
        validator = QualityValidator()
        report = validator.generate_quality_report(good_data, "AAPL")

        assert report.symbol == "AAPL"
        assert report.metrics.total_records == len(good_data)
        assert report.metrics.overall_quality_score > 0
        assert len(report.field_completeness) > 0
        assert len(report.field_validity) > 0

    def test_quality_metrics_calculation(self, good_data, bad_data):
        """Test quality metrics calculation."""
        validator = QualityValidator()

        # Good data should have high scores
        good_report = validator.generate_quality_report(good_data, "AAPL")
        assert good_report.metrics.overall_quality_score > 0.8
        assert good_report.is_high_quality()

        # Bad data should have lower scores
        bad_report = validator.generate_quality_report(bad_data, "AAPL")
        assert bad_report.metrics.overall_quality_score < good_report.metrics.overall_quality_score

    def test_field_completeness_analysis(self, bad_data):
        """Test field-level completeness analysis."""
        validator = QualityValidator()
        report = validator.generate_quality_report(bad_data, "AAPL")

        # Open column has missing values
        assert report.field_completeness["Open"] < 1.0
        # Other columns should be complete
        assert report.field_completeness["Close"] == 1.0

    def test_statistical_analysis(self, good_data):
        """Test statistical properties analysis."""
        validator = QualityValidator()
        report = validator.generate_quality_report(good_data, "AAPL")

        assert len(report.price_statistics) > 0
        assert len(report.volume_statistics) > 0
        assert "Open_mean" in report.price_statistics
        assert "mean" in report.volume_statistics

    def test_recommendations_generation(self, bad_data):
        """Test recommendation generation."""
        validator = QualityValidator()
        report = validator.generate_quality_report(bad_data, "AAPL")

        # Should generate recommendations for poor quality data
        assert len(report.recommendations) > 0

        # Check for specific recommendations
        recommendations_text = " ".join(report.recommendations).lower()
        assert "missing" in recommendations_text or "clean" in recommendations_text

    def test_empty_dataframe(self):
        """Test validation of empty DataFrame."""
        empty_df = pd.DataFrame()
        validator = QualityValidator()
        result = validator.validate(empty_df, "AAPL")

        assert result.is_valid is False
        assert "empty" in result.errors[0].lower()

    def test_disabled_checks(self, bad_data):
        """Test with validation checks disabled."""
        config = ValidationConfig(
            check_completeness=False,
            check_consistency=False,
            check_validity=False,
            check_timeliness=False,
        )
        validator = QualityValidator(config)
        result = validator.validate(bad_data, "AAPL")

        # Should pass since no checks are performed
        assert result.is_valid is True
        assert len(result.errors) == 0


class TestValidationConfig:
    """Test ValidationConfig model."""

    def test_default_config(self):
        """Test default configuration values."""
        config = ValidationConfig()

        assert config.check_completeness is True
        assert config.check_consistency is True
        assert config.check_validity is True
        assert config.check_timeliness is True
        assert config.min_completeness_score == 0.95
        assert config.min_consistency_score == 0.90
        assert config.min_validity_score == 0.95
        assert config.max_daily_price_change == 0.20
        assert config.min_price_value == 0.01
        assert config.max_price_value == 100000.0

    def test_custom_config(self):
        """Test custom configuration."""
        config = ValidationConfig(
            check_completeness=False,
            min_completeness_score=0.90,
            max_daily_price_change=0.15,
            max_data_age_days=30,
        )

        assert config.check_completeness is False
        assert config.min_completeness_score == 0.90
        assert config.max_daily_price_change == 0.15
        assert config.max_data_age_days == 30
