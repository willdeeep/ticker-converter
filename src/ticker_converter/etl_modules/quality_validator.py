"""Data quality validation module for market data."""

import logging
from datetime import datetime
from typing import Optional

import pandas as pd
from pydantic import BaseModel, Field

from ..data_models.market_data import ValidationResult
from ..data_models.quality_metrics import DataQualityMetrics, DataQualityReport

logger = logging.getLogger(__name__)


class ValidationConfig(BaseModel):
    """Configuration for data quality validation."""

    check_completeness: bool = Field(
        default=True, description="Check data completeness"
    )
    check_consistency: bool = Field(default=True, description="Check data consistency")
    check_validity: bool = Field(default=True, description="Check data validity")
    check_timeliness: bool = Field(default=True, description="Check data timeliness")

    # Thresholds
    min_completeness_score: float = Field(
        default=0.95, description="Minimum completeness score"
    )
    min_consistency_score: float = Field(
        default=0.90, description="Minimum consistency score"
    )
    min_validity_score: float = Field(
        default=0.95, description="Minimum validity score"
    )

    # Price validation
    max_daily_price_change: float = Field(
        default=0.20, description="Maximum daily price change (20%)"
    )
    min_price_value: float = Field(default=0.01, description="Minimum valid price")
    max_price_value: float = Field(default=100000.0, description="Maximum valid price")

    # Volume validation
    min_volume: int = Field(default=0, description="Minimum trading volume")
    max_volume: int = Field(default=1_000_000_000, description="Maximum trading volume")

    # Temporal validation
    max_data_age_days: int = Field(default=7, description="Maximum age of data in days")


class QualityValidator:
    """Validates data quality for market data."""

    def __init__(self, config: Optional[ValidationConfig] = None):
        """Initialize the quality validator.

        Args:
            config: Validation configuration
        """
        self.config = config or ValidationConfig()

    def validate(self, df: pd.DataFrame, symbol: str) -> ValidationResult:
        """Validate a DataFrame for data quality issues.

        Args:
            df: DataFrame to validate
            symbol: Stock symbol being validated

        Returns:
            ValidationResult with validation outcome
        """
        logger.info("Starting data quality validation for %s", symbol)

        result = ValidationResult(is_valid=True)

        try:
            # Run validation checks
            if self.config.check_completeness:
                self._check_completeness(df, result)

            if self.config.check_consistency:
                self._check_consistency(df, result)

            if self.config.check_validity:
                self._check_validity(df, result)

            if self.config.check_timeliness:
                self._check_timeliness(df, result)

            logger.info(
                "Validation completed for %s. Valid: %s", symbol, result.is_valid
            )
            if result.errors:
                logger.warning("Validation errors: %s", result.errors)
            if result.warnings:
                logger.info("Validation warnings: %s", result.warnings)

        except Exception as e:
            result.add_error(f"Validation failed with exception: {str(e)}")
            logger.error("Validation failed for %s: %s", symbol, e)

        return result

    def generate_quality_report(
        self, df: pd.DataFrame, symbol: str
    ) -> DataQualityReport:
        """Generate a comprehensive data quality report.

        Args:
            df: DataFrame to analyze
            symbol: Stock symbol being analyzed

        Returns:
            DataQualityReport with detailed quality assessment
        """
        logger.info("Generating quality report for %s", symbol)

        # Calculate metrics
        metrics = self._calculate_quality_metrics(df)

        # Generate report ID
        report_id = f"{symbol}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

        # Create report
        report = DataQualityReport(
            symbol=symbol,
            report_id=report_id,
            metrics=metrics,
        )

        # Add detailed analysis
        self._analyze_field_quality(df, report)
        self._analyze_statistical_properties(df, report)
        self._generate_recommendations(metrics, report)

        logger.info(
            "Quality report generated for %s. Overall score: %.3f",
            symbol,
            metrics.overall_quality_score,
        )

        return report

    def _check_completeness(self, df: pd.DataFrame, result: ValidationResult) -> None:
        """Check data completeness."""
        try:
            total_values = df.size
            missing_values = df.isnull().sum().sum()

            if total_values == 0:
                result.add_error("DataFrame is empty")
                return

            completeness_ratio = (total_values - missing_values) / total_values

            if completeness_ratio < self.config.min_completeness_score:
                result.add_error(
                    f"Data completeness {completeness_ratio:.3f} below threshold "
                    f"{self.config.min_completeness_score}"
                )

            if missing_values > 0:
                result.add_warning(f"Found {missing_values} missing values")

        except Exception as e:
            result.add_error(f"Completeness check failed: {str(e)}")

    def _check_consistency(self, df: pd.DataFrame, result: ValidationResult) -> None:
        """Check data consistency."""
        try:
            # Check for duplicates
            duplicates = df.duplicated().sum()
            if duplicates > 0:
                result.add_warning(f"Found {duplicates} duplicate records")

            # Check price relationships
            if all(col in df.columns for col in ["High", "Low", "Close", "Open"]):
                # High should be >= Low
                invalid_high_low = (df["High"] < df["Low"]).sum()
                if invalid_high_low > 0:
                    result.add_error(
                        f"Found {invalid_high_low} records where High < Low"
                    )

                # Close should be between High and Low
                invalid_close = (
                    (df["Close"] > df["High"]) | (df["Close"] < df["Low"])
                ).sum()
                if invalid_close > 0:
                    result.add_error(
                        f"Found {invalid_close} records where Close is outside High/Low range"
                    )

            # Check for consistent symbol
            if "Symbol" in df.columns:
                unique_symbols = df["Symbol"].nunique()
                if unique_symbols > 1:
                    result.add_warning(
                        f"Found {unique_symbols} different symbols in dataset"
                    )

        except Exception as e:
            result.add_error(f"Consistency check failed: {str(e)}")

    def _check_validity(self, df: pd.DataFrame, result: ValidationResult) -> None:
        """Check data validity."""
        try:
            price_columns = ["Open", "High", "Low", "Close"]

            for col in price_columns:
                if col not in df.columns:
                    continue

                # Check for negative prices
                negative_prices = (df[col] <= 0).sum()
                if negative_prices > 0:
                    result.add_error(
                        f"Found {negative_prices} non-positive values in {col}"
                    )

                # Check for extreme prices
                min_val = df[col].min()
                max_val = df[col].max()

                if min_val < self.config.min_price_value:
                    result.add_warning(
                        f"{col} minimum value {min_val} below threshold {self.config.min_price_value}"
                    )

                if max_val > self.config.max_price_value:
                    result.add_warning(
                        f"{col} maximum value {max_val} above threshold {self.config.max_price_value}"
                    )

                # Check for extreme daily changes
                if len(df) > 1:
                    daily_changes = df[col].pct_change(fill_method=None).abs()
                    extreme_changes = (
                        daily_changes > self.config.max_daily_price_change
                    ).sum()
                    if extreme_changes > 0:
                        result.add_warning(
                            f"Found {extreme_changes} extreme daily changes (>{self.config.max_daily_price_change:.1%}) in {col}"
                        )

            # Check volume
            if "Volume" in df.columns:
                negative_volume = (df["Volume"] < 0).sum()
                if negative_volume > 0:
                    result.add_error(f"Found {negative_volume} negative volume values")

                extreme_volume = (df["Volume"] > self.config.max_volume).sum()
                if extreme_volume > 0:
                    result.add_warning(
                        f"Found {extreme_volume} extremely high volume values"
                    )

        except Exception as e:
            result.add_error(f"Validity check failed: {str(e)}")

    def _check_timeliness(self, df: pd.DataFrame, result: ValidationResult) -> None:
        """Check data timeliness."""
        try:
            if not isinstance(df.index, pd.DatetimeIndex):
                result.add_warning("DataFrame index is not a DatetimeIndex")
                return

            # Check data freshness
            latest_date = df.index.max()
            age_days = (datetime.now() - latest_date.to_pydatetime()).days

            if age_days > self.config.max_data_age_days:
                result.add_warning(
                    f"Data is {age_days} days old, exceeds threshold of {self.config.max_data_age_days} days"
                )

            # Check for data gaps
            if len(df) > 1:
                expected_business_days = pd.bdate_range(
                    start=df.index.min(), end=df.index.max()
                )
                missing_days = len(expected_business_days) - len(df)

                if missing_days > 0:
                    result.add_warning(
                        f"Found {missing_days} missing business days in date range"
                    )

        except Exception as e:
            result.add_error(f"Timeliness check failed: {str(e)}")

    def _calculate_quality_metrics(self, df: pd.DataFrame) -> DataQualityMetrics:
        """Calculate comprehensive quality metrics."""
        total_records = len(df)

        if total_records == 0:
            return DataQualityMetrics(
                total_records=0, date_range_start=None, date_range_end=None
            )

        # Basic counts
        missing_values = df.isnull().sum().sum()
        complete_records = len(df.dropna())
        duplicates = df.duplicated().sum()

        # Date range
        date_range_start = None
        date_range_end = None
        date_gaps = 0

        if isinstance(df.index, pd.DatetimeIndex):
            date_range_start = df.index.min().to_pydatetime()
            date_range_end = df.index.max().to_pydatetime()

            if len(df) > 1:
                expected_business_days = pd.bdate_range(
                    start=df.index.min(), end=df.index.max()
                )
                date_gaps = max(
                    0, len(expected_business_days) - len(df)
                )  # Ensure non-negative

        # Price validation
        negative_prices = 0
        price_anomalies = 0
        price_columns = ["Open", "High", "Low", "Close"]

        for col in price_columns:
            if col in df.columns:
                negative_prices += (df[col] <= 0).sum()
                # Count extreme price changes as anomalies
                if len(df) > 1:
                    extreme_changes = (
                        df[col].pct_change(fill_method=None).abs()
                        > self.config.max_daily_price_change
                    ).sum()
                    price_anomalies += extreme_changes

        # Volume validation
        zero_volume_days = 0
        if "Volume" in df.columns:
            zero_volume_days = (df["Volume"] == 0).sum()

        # Type consistency (simplified)
        type_consistency_score = 1.0  # Assume consistent if we got this far

        # Create metrics
        metrics = DataQualityMetrics(
            total_records=total_records,
            complete_records=complete_records,
            missing_value_count=missing_values,
            duplicate_count=duplicates,
            date_range_start=date_range_start,
            date_range_end=date_range_end,
            date_gaps=date_gaps,
            negative_prices=negative_prices,
            zero_volume_days=zero_volume_days,
            price_anomalies=price_anomalies,
            type_consistency_score=type_consistency_score,
        )

        # Calculate quality scores
        metrics.calculate_scores()

        return metrics

    def _analyze_field_quality(
        self, df: pd.DataFrame, report: DataQualityReport
    ) -> None:
        """Analyze quality by field."""
        for column in df.columns:
            # Completeness by field
            non_null_count = df[column].count()
            completeness = non_null_count / len(df) if len(df) > 0 else 0
            report.field_completeness[column] = completeness

            # Validity by field (simplified)
            validity = 1.0
            if column in ["Open", "High", "Low", "Close"]:
                negative_count = (df[column] <= 0).sum()
                validity = 1.0 - (negative_count / len(df)) if len(df) > 0 else 0
            elif column == "Volume":
                negative_count = (df[column] < 0).sum()
                validity = 1.0 - (negative_count / len(df)) if len(df) > 0 else 0

            report.field_validity[column] = validity

    def _analyze_statistical_properties(
        self, df: pd.DataFrame, report: DataQualityReport
    ) -> None:
        """Analyze statistical properties."""
        price_columns = ["Open", "High", "Low", "Close"]

        for col in price_columns:
            if col in df.columns:
                stats = df[col].describe()
                report.price_statistics[f"{col}_mean"] = stats["mean"]
                report.price_statistics[f"{col}_std"] = stats["std"]
                report.price_statistics[f"{col}_min"] = stats["min"]
                report.price_statistics[f"{col}_max"] = stats["max"]

        if "Volume" in df.columns:
            vol_stats = df["Volume"].describe()
            report.volume_statistics["mean"] = vol_stats["mean"]
            report.volume_statistics["std"] = vol_stats["std"]
            report.volume_statistics["min"] = vol_stats["min"]
            report.volume_statistics["max"] = vol_stats["max"]

    def _generate_recommendations(
        self, metrics: DataQualityMetrics, report: DataQualityReport
    ) -> None:
        """Generate improvement recommendations."""
        if metrics.completeness_score < 0.95:
            report.add_recommendation("Investigate and address missing data points")

        if metrics.duplicate_count > 0:
            report.add_recommendation("Remove duplicate records before analysis")

        if metrics.negative_prices > 0:
            report.add_recommendation("Clean or remove records with invalid price data")

        if metrics.date_gaps > 5:
            report.add_recommendation(
                "Consider filling gaps in date sequence for time series analysis"
            )

        if metrics.price_anomalies > metrics.total_records * 0.05:
            report.add_recommendation(
                "Review and potentially filter extreme price movements"
            )

        if metrics.overall_quality_score < 0.8:
            report.add_recommendation(
                "Data quality is below acceptable threshold - comprehensive cleaning required"
            )
