"""Unit tests for core pipeline functionality."""

import pytest
import pandas as pd
from unittest.mock import Mock, patch

from src.ticker_converter.core import FinancialDataPipeline
from src.ticker_converter.api_client import AlphaVantageAPIError


class TestFinancialDataPipeline:
    """Test financial data pipeline."""
    
    def test_pipeline_initialization_with_api_key(self):
        """Test pipeline initializes correctly with API key."""
        with patch('src.ticker_converter.core.AlphaVantageClient') as mock_client:
            pipeline = FinancialDataPipeline("test_key")
            
            assert pipeline.api_key == "test_key"
            mock_client.assert_called_once_with("test_key")
    
    def test_pipeline_initialization_without_api_key(self, mock_config):
        """Test pipeline initializes with config API key."""
        mock_config.ALPHA_VANTAGE_API_KEY = "config_key"
        
        with patch('src.ticker_converter.core.AlphaVantageClient') as mock_client:
            pipeline = FinancialDataPipeline()
            
            assert pipeline.api_key is None
            mock_client.assert_called_once_with(None)
    
    def test_fetch_stock_data_compact_period(self, financial_pipeline, sample_dataframe):
        """Test fetching stock data with compact period."""
        with patch.object(financial_pipeline.alpha_vantage, 'get_daily_stock_data', 
                         return_value=sample_dataframe) as mock_get:
            result = financial_pipeline.fetch_stock_data("AAPL", "1mo")
        
        mock_get.assert_called_once_with("AAPL", "compact")
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
    
    def test_fetch_stock_data_full_period(self, financial_pipeline, sample_dataframe):
        """Test fetching stock data with full period."""
        with patch.object(financial_pipeline.alpha_vantage, 'get_daily_stock_data', 
                         return_value=sample_dataframe) as mock_get:
            result = financial_pipeline.fetch_stock_data("AAPL", "1y")
        
        mock_get.assert_called_once_with("AAPL", "full")
        assert isinstance(result, pd.DataFrame)
    
    def test_fetch_stock_data_api_error_handling(self, financial_pipeline, capsys):
        """Test error handling in fetch_stock_data."""
        with patch.object(financial_pipeline.alpha_vantage, 'get_daily_stock_data', 
                         side_effect=AlphaVantageAPIError("API Error")):
            result = financial_pipeline.fetch_stock_data("INVALID")
        
        # Should return empty DataFrame on error
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0
        
        # Check error message was printed
        captured = capsys.readouterr()
        assert "Error fetching data for INVALID: API Error" in captured.out
    
    def test_fetch_intraday_data_success(self, financial_pipeline, sample_dataframe):
        """Test successful intraday data fetching."""
        intraday_df = sample_dataframe.copy()
        intraday_df['DateTime'] = intraday_df['Date']
        intraday_df = intraday_df.drop('Date', axis=1)
        
        with patch.object(financial_pipeline.alpha_vantage, 'get_intraday_stock_data', 
                         return_value=intraday_df) as mock_get:
            result = financial_pipeline.fetch_intraday_data("AAPL", "5min")
        
        mock_get.assert_called_once_with("AAPL", "5min")
        assert isinstance(result, pd.DataFrame)
        assert 'DateTime' in result.columns
    
    def test_fetch_intraday_data_api_error_handling(self, financial_pipeline, capsys):
        """Test error handling in fetch_intraday_data."""
        with patch.object(financial_pipeline.alpha_vantage, 'get_intraday_stock_data', 
                         side_effect=AlphaVantageAPIError("API Error")):
            result = financial_pipeline.fetch_intraday_data("INVALID")
        
        # Should return empty DataFrame on error
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0
        
        # Check error message was printed
        captured = capsys.readouterr()
        assert "Error fetching intraday data for INVALID: API Error" in captured.out
    
    def test_get_company_info_success(self, financial_pipeline, sample_company_overview):
        """Test successful company info retrieval."""
        with patch.object(financial_pipeline.alpha_vantage, 'get_company_overview', 
                         return_value=sample_company_overview) as mock_get:
            result = financial_pipeline.get_company_info("AAPL")
        
        mock_get.assert_called_once_with("AAPL")
        assert result == sample_company_overview
        assert result['Name'] == 'Apple Inc'
    
    def test_get_company_info_api_error_handling(self, financial_pipeline, capsys):
        """Test error handling in get_company_info."""
        with patch.object(financial_pipeline.alpha_vantage, 'get_company_overview', 
                         side_effect=AlphaVantageAPIError("API Error")):
            result = financial_pipeline.get_company_info("INVALID")
        
        # Should return empty dict on error
        assert result == {}
        
        # Check error message was printed
        captured = capsys.readouterr()
        assert "Error fetching company info for INVALID: API Error" in captured.out
    
    def test_transform_placeholder(self, financial_pipeline, sample_dataframe):
        """Test transform method (currently a placeholder)."""
        result = financial_pipeline.transform(sample_dataframe)
        
        # Currently just returns the input data
        pd.testing.assert_frame_equal(result, sample_dataframe)
    
    def test_period_mapping(self, financial_pipeline, sample_dataframe):
        """Test that periods are correctly mapped to outputsize."""
        with patch.object(financial_pipeline.alpha_vantage, 'get_daily_stock_data', 
                         return_value=sample_dataframe) as mock_get:
            
            # Test compact periods
            for period in ["1mo", "3mo"]:
                financial_pipeline.fetch_stock_data("AAPL", period)
                mock_get.assert_called_with("AAPL", "compact")
                mock_get.reset_mock()
            
            # Test full periods
            for period in ["1y", "max", "5y"]:
                financial_pipeline.fetch_stock_data("AAPL", period)
                mock_get.assert_called_with("AAPL", "full")
                mock_get.reset_mock()
