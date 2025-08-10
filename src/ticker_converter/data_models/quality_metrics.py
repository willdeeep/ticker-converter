"""Data quality metrics and reporting models."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel
from pydantic import Field


class DataQualityMetrics(BaseModel):
    """Metrics for assessing data quality."""

    total_records: int = Field(..., ge=0, description="Total number of records")
    complete_records: int = Field(
        default=0, ge=0, description="Records with no missing values"
    )
    missing_value_count: int = Field(
        default=0, ge=0, description="Total missing values"
    )
    duplicate_count: int = Field(
        default=0, ge=0, description="Number of duplicate records"
    )
    outlier_count: int = Field(
        default=0, ge=0, description="Number of statistical outliers"
    )

    # Data type consistency
    type_consistency_score: float = Field(
        default=1.0, ge=0, le=1, description="Data type consistency (0-1)"
    )

    # Date/timestamp quality
    date_range_start: Optional[datetime] = Field(None, description="Earliest timestamp")
    date_range_end: Optional[datetime] = Field(None, description="Latest timestamp")
    date_gaps: int = Field(
        default=0, ge=0, description="Number of missing dates in sequence"
    )

    # Price data validation
    negative_prices: int = Field(
        default=0, ge=0, description="Number of negative price values"
    )
    zero_volume_days: int = Field(
        default=0, ge=0, description="Days with zero trading volume"
    )
    price_anomalies: int = Field(
        default=0, ge=0, description="Price values outside expected ranges"
    )

    # Calculated quality scores
    completeness_score: float = Field(
        default=0.0, ge=0, le=1, description="Data completeness (0-1)"
    )
    consistency_score: float = Field(
        default=0.0, ge=0, le=1, description="Data consistency (0-1)"
    )
    validity_score: float = Field(
        default=0.0, ge=0, le=1, description="Data validity (0-1)"
    )
    overall_quality_score: float = Field(
        default=0.0, ge=0, le=1, description="Overall quality score (0-1)"
    )

    def calculate_scores(self) -> None:
        """Calculate quality scores based on metrics."""
        if self.total_records == 0:
            self.completeness_score = 0.0
            self.consistency_score = 0.0
            self.validity_score = 0.0
            self.overall_quality_score = 0.0
            return

        # Completeness: ratio of complete records
        self.completeness_score = self.complete_records / self.total_records

        # Consistency: penalize duplicates and type inconsistencies
        consistency_penalty = (self.duplicate_count / self.total_records) * 0.5
        self.consistency_score = max(
            0.0, self.type_consistency_score - consistency_penalty
        )

        # Validity: penalize anomalies and invalid values
        invalid_count = self.negative_prices + self.price_anomalies
        validity_penalty = invalid_count / self.total_records
        self.validity_score = max(0.0, 1.0 - validity_penalty)

        # Overall score: weighted average
        self.overall_quality_score = (
            self.completeness_score * 0.4
            + self.consistency_score * 0.3
            + self.validity_score * 0.3
        )


class DataQualityReport(BaseModel):
    """Comprehensive data quality assessment report."""

    symbol: str = Field(..., description="Stock symbol analyzed")
    report_id: str = Field(..., description="Unique report identifier")
    generated_at: datetime = Field(default_factory=datetime.utcnow)

    # Quality metrics
    metrics: DataQualityMetrics = Field(..., description="Quality metrics")

    # Detailed findings
    issues_found: list[str] = Field(
        default_factory=list, description="List of data quality issues"
    )
    recommendations: list[str] = Field(
        default_factory=list, description="Improvement recommendations"
    )

    # Field-specific analysis
    field_completeness: dict[str, float] = Field(
        default_factory=dict, description="Completeness by field"
    )
    field_validity: dict[str, float] = Field(
        default_factory=dict, description="Validity by field"
    )

    # Statistical summaries
    price_statistics: dict[str, float] = Field(
        default_factory=dict, description="Price field statistics"
    )
    volume_statistics: dict[str, float] = Field(
        default_factory=dict, description="Volume statistics"
    )

    class Config:
        """Pydantic configuration."""

        json_encoders = {datetime: lambda v: v.isoformat()}

    def add_issue(self, issue: str) -> None:
        """Add a data quality issue."""
        self.issues_found.append(issue)

    def add_recommendation(self, recommendation: str) -> None:
        """Add an improvement recommendation."""
        self.recommendations.append(recommendation)

    def is_high_quality(self, threshold: float = 0.8) -> bool:
        """Check if data meets high quality threshold."""
        return self.metrics.overall_quality_score >= threshold

    def get_summary(self) -> dict[str, any]:
        """Get a summary of the quality report."""
        return {
            "symbol": self.symbol,
            "overall_score": self.metrics.overall_quality_score,
            "completeness": self.metrics.completeness_score,
            "consistency": self.metrics.consistency_score,
            "validity": self.metrics.validity_score,
            "total_records": self.metrics.total_records,
            "issues_count": len(self.issues_found),
            "high_quality": self.is_high_quality(),
        }
