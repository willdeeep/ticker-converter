"""Tests for quality metrics models."""

from src.ticker_converter.data_models.quality_metrics import (
    DataQualityMetrics,
    DataQualityReport,
)


class TestDataQualityMetrics:
    """Test DataQualityMetrics model."""
    
    def test_basic_metrics(self):
        """Test creating basic quality metrics."""
        metrics = DataQualityMetrics(
            total_records=100,
            complete_records=95,
            missing_value_count=5,
            duplicate_count=2,
        )
        
        assert metrics.total_records == 100
        assert metrics.complete_records == 95
        assert metrics.missing_value_count == 5
        assert metrics.duplicate_count == 2
    
    def test_calculate_scores(self):
        """Test score calculations."""
        metrics = DataQualityMetrics(
            total_records=100,
            complete_records=90,
            missing_value_count=10,
            duplicate_count=5,
            negative_prices=2,
            price_anomalies=3,
            type_consistency_score=0.95,
        )
        
        metrics.calculate_scores()
        
        # Completeness: 90/100 = 0.9
        assert metrics.completeness_score == 0.9
        
        # Consistency: 0.95 - (5/100)*0.5 = 0.925 (with floating point tolerance)
        assert abs(metrics.consistency_score - 0.925) < 0.001
        
        # Validity: 1.0 - (5/100) = 0.95
        assert metrics.validity_score == 0.95
        
        # Overall: weighted average
        expected_overall = 0.9 * 0.4 + 0.925 * 0.3 + 0.95 * 0.3
        assert abs(metrics.overall_quality_score - expected_overall) < 0.001
    
    def test_empty_dataset_scores(self):
        """Test score calculation for empty dataset."""
        metrics = DataQualityMetrics(total_records=0)
        metrics.calculate_scores()
        
        assert metrics.completeness_score == 0.0
        assert metrics.consistency_score == 0.0
        assert metrics.validity_score == 0.0
        assert metrics.overall_quality_score == 0.0


class TestDataQualityReport:
    """Test DataQualityReport model."""
    
    def test_basic_report(self):
        """Test creating a basic quality report."""
        metrics = DataQualityMetrics(
            total_records=100,
            complete_records=95,
            overall_quality_score=0.85,
        )
        
        report = DataQualityReport(
            symbol="AAPL",
            report_id="AAPL_20250808_120000",
            metrics=metrics,
        )
        
        assert report.symbol == "AAPL"
        assert report.report_id == "AAPL_20250808_120000"
        assert report.metrics.total_records == 100
    
    def test_add_issue_and_recommendation(self):
        """Test adding issues and recommendations."""
        metrics = DataQualityMetrics(total_records=100, complete_records=95)
        report = DataQualityReport(
            symbol="AAPL",
            report_id="test",
            metrics=metrics,
        )
        
        report.add_issue("Missing data detected")
        report.add_recommendation("Fill missing values")
        
        assert "Missing data detected" in report.issues_found
        assert "Fill missing values" in report.recommendations
    
    def test_is_high_quality(self):
        """Test quality threshold checking."""
        # High quality metrics
        high_quality_metrics = DataQualityMetrics(
            total_records=100,
            complete_records=95,
            overall_quality_score=0.9,
        )
        
        report = DataQualityReport(
            symbol="AAPL",
            report_id="test",
            metrics=high_quality_metrics,
        )
        
        assert report.is_high_quality() is True
        assert report.is_high_quality(threshold=0.95) is False
        
        # Low quality metrics
        low_quality_metrics = DataQualityMetrics(
            total_records=100,
            complete_records=50,
            overall_quality_score=0.6,
        )
        
        report.metrics = low_quality_metrics
        assert report.is_high_quality() is False
    
    def test_get_summary(self):
        """Test report summary generation."""
        metrics = DataQualityMetrics(
            total_records=100,
            complete_records=95,
            completeness_score=0.95,
            consistency_score=0.90,
            validity_score=0.85,
            overall_quality_score=0.90,
        )
        
        report = DataQualityReport(
            symbol="AAPL",
            report_id="test",
            metrics=metrics,
        )
        
        report.add_issue("Test issue")
        
        summary = report.get_summary()
        
        assert summary["symbol"] == "AAPL"
        assert summary["overall_score"] == 0.90
        assert summary["completeness"] == 0.95
        assert summary["consistency"] == 0.90
        assert summary["validity"] == 0.85
        assert summary["total_records"] == 100
        assert summary["issues_count"] == 1
        assert summary["high_quality"] is True
