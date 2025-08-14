"""Unit tests for NYSE data fetcher."""

from unittest.mock import Mock, patch, MagicMock
import pandas as pd
import pytest
from datetime import date

from src.ticker_converter.data_ingestion.nyse_fetcher import NYSEDataFetcher
from src.ticker_converter.api_clients.exceptions import AlphaVantageAPIError
from src.ticker_converter.api_clients.constants import OutputSize


class TestNYSEDataFetcher:
    """Test suite for NYSEDataFetcher."""

    def test_initialization_default(self):
        """Test fetcher initialization with default settings."""
        fetcher = NYSEDataFetcher()
        
        assert fetcher.api_client is not None
        assert fetcher.magnificent_seven_symbols == [
            "AAPL", "MSFT", "AMZN", "GOOGL", "META", "NVDA", "TSLA"
        ]

    @patch('src.ticker_converter.data_ingestion.nyse_fetcher.AlphaVantageClient')
    def test_initialization_with_custom_client(self, mock_client_class):
        """Test fetcher initialization with custom API client."""
        mock_client = Mock()
        fetcher = NYSEDataFetcher(api_client=mock_client)
        
        assert fetcher.api_client is mock_client
        # Should not create new client when one is provided
        mock_client_class.assert_not_called()

    @patch.object(NYSEDataFetcher, '_fetch_symbol_data')
    def test_fetch_daily_data_success(self, mock_fetch_symbol):
        """Test successful daily data fetching for all symbols."""
        # Setup mock data for each symbol
        mock_data = pd.DataFrame({
            'open': [220.0, 218.0],
            'high': [225.0, 223.0],
            'low': [219.0, 217.0],
            'close': [224.5, 221.5],
            'volume': [1000000, 900000]
        }, index=pd.date_range('2025-08-13', periods=2))
        
        mock_fetch_symbol.return_value = mock_data
        
        fetcher = NYSEDataFetcher()
        result = fetcher.fetch_daily_data()
        
        # Should be called once for each magnificent seven symbol
        assert mock_fetch_symbol.call_count == 7
        
        # Check that result is a dictionary with symbol data
        assert isinstance(result, dict)
        assert len(result) == 7
        
        for symbol in fetcher.magnificent_seven_symbols:
            assert symbol in result
            assert isinstance(result[symbol], dict)

    @patch.object(NYSEDataFetcher, '_fetch_symbol_data')
    def test_fetch_daily_data_with_api_error(self, mock_fetch_symbol):
        """Test daily data fetching with API errors for some symbols."""
        # Setup mock to raise error for one symbol and succeed for others
        def side_effect(symbol, *args, **kwargs):
            if symbol == "AAPL":
                raise AlphaVantageAPIError("API Error for AAPL")
            return pd.DataFrame({
                'open': [220.0],
                'high': [225.0],
                'low': [219.0],
                'close': [224.5],
                'volume': [1000000]
            }, index=pd.date_range('2025-08-14', periods=1))
        
        mock_fetch_symbol.side_effect = side_effect
        
        fetcher = NYSEDataFetcher()
        result = fetcher.fetch_daily_data()
        
        # Should still return data for successful symbols
        assert isinstance(result, dict)
        assert len(result) == 6  # 7 symbols - 1 failed
        assert "AAPL" not in result
        assert "MSFT" in result

    @patch('src.ticker_converter.data_ingestion.nyse_fetcher.AlphaVantageClient')
    def test_fetch_symbol_data_success(self, mock_client_class):
        """Test successful symbol data fetching."""
        # Setup mock client
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # Setup mock DataFrame response
        mock_df = pd.DataFrame({
            'open': [220.0, 218.0],
            'high': [225.0, 223.0],
            'low': [219.0, 217.0],
            'close': [224.5, 221.5],
            'volume': [1000000, 900000]
        }, index=pd.date_range('2025-08-13', periods=2))
        
        mock_client.get_daily_stock_data.return_value = mock_df
        
        fetcher = NYSEDataFetcher()
        result = fetcher._fetch_symbol_data("AAPL", OutputSize.COMPACT)
        
        # Verify API client was called correctly
        mock_client.get_daily_stock_data.assert_called_once_with("AAPL", OutputSize.COMPACT)
        
        # Verify result
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        assert list(result.columns) == ['open', 'high', 'low', 'close', 'volume']

    @patch('src.ticker_converter.data_ingestion.nyse_fetcher.AlphaVantageClient')
    def test_fetch_symbol_data_api_error(self, mock_client_class):
        """Test symbol data fetching with API error."""
        # Setup mock client to raise error
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.get_daily_stock_data.side_effect = AlphaVantageAPIError("API Error")
        
        fetcher = NYSEDataFetcher()
        
        with pytest.raises(AlphaVantageAPIError):
            fetcher._fetch_symbol_data("AAPL", OutputSize.COMPACT)

    @patch('src.ticker_converter.data_ingestion.nyse_fetcher.AlphaVantageClient')
    def test_fetch_symbol_data_empty_response(self, mock_client_class):
        """Test symbol data fetching with empty response."""
        # Setup mock client to return empty DataFrame
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.get_daily_stock_data.return_value = pd.DataFrame()
        
        fetcher = NYSEDataFetcher()
        result = fetcher._fetch_symbol_data("AAPL", OutputSize.COMPACT)
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0

    def test_fetch_single_symbol_success(self):
        """Test fetching data for a single symbol."""
        with patch.object(NYSEDataFetcher, '_fetch_symbol_data') as mock_fetch:
            mock_data = pd.DataFrame({
                'open': [220.0],
                'high': [225.0],
                'low': [219.0],
                'close': [224.5],
                'volume': [1000000]
            }, index=pd.date_range('2025-08-14', periods=1))
            
            mock_fetch.return_value = mock_data
            
            fetcher = NYSEDataFetcher()
            result = fetcher.fetch_single_symbol("AAPL")
            
            mock_fetch.assert_called_once_with("AAPL", OutputSize.COMPACT)
            assert isinstance(result, pd.DataFrame)
            assert len(result) == 1

    def test_fetch_single_symbol_with_custom_output_size(self):
        """Test fetching single symbol with custom output size."""
        with patch.object(NYSEDataFetcher, '_fetch_symbol_data') as mock_fetch:
            mock_data = pd.DataFrame({
                'open': [220.0],
                'high': [225.0],
                'low': [219.0],
                'close': [224.5],
                'volume': [1000000]
            })
            
            mock_fetch.return_value = mock_data
            
            fetcher = NYSEDataFetcher()
            result = fetcher.fetch_single_symbol("AAPL", OutputSize.FULL)
            
            mock_fetch.assert_called_once_with("AAPL", OutputSize.FULL)

    def test_fetch_single_symbol_invalid_symbol(self):
        """Test fetching single symbol with invalid symbol."""
        fetcher = NYSEDataFetcher()
        
        with pytest.raises(ValueError, match="Symbol cannot be empty"):
            fetcher.fetch_single_symbol("")
        
        with pytest.raises(ValueError, match="Symbol cannot be empty"):
            fetcher.fetch_single_symbol(None)

    def test_get_supported_symbols(self):
        """Test getting list of supported symbols."""
        fetcher = NYSEDataFetcher()
        symbols = fetcher.get_supported_symbols()
        
        assert isinstance(symbols, list)
        assert len(symbols) == 7
        assert "AAPL" in symbols
        assert "MSFT" in symbols
        assert "GOOGL" in symbols

    def test_is_symbol_supported(self):
        """Test checking if a symbol is supported."""
        fetcher = NYSEDataFetcher()
        
        # Test supported symbols
        assert fetcher.is_symbol_supported("AAPL") is True
        assert fetcher.is_symbol_supported("MSFT") is True
        assert fetcher.is_symbol_supported("GOOGL") is True
        
        # Test unsupported symbols
        assert fetcher.is_symbol_supported("INVALID") is False
        assert fetcher.is_symbol_supported("XYZ") is False

    def test_is_symbol_supported_case_insensitive(self):
        """Test that symbol support check is case insensitive."""
        fetcher = NYSEDataFetcher()
        
        assert fetcher.is_symbol_supported("aapl") is True
        assert fetcher.is_symbol_supported("AAPL") is True
        assert fetcher.is_symbol_supported("Aapl") is True

    @patch.object(NYSEDataFetcher, '_fetch_symbol_data')
    def test_fetch_custom_symbols(self, mock_fetch_symbol):
        """Test fetching data for custom list of symbols."""
        # Setup mock data
        mock_data = pd.DataFrame({
            'open': [220.0],
            'high': [225.0],
            'low': [219.0],
            'close': [224.5],
            'volume': [1000000]
        }, index=pd.date_range('2025-08-14', periods=1))
        
        mock_fetch_symbol.return_value = mock_data
        
        fetcher = NYSEDataFetcher()
        custom_symbols = ["AAPL", "MSFT", "CUSTOM"]
        result = fetcher.fetch_custom_symbols(custom_symbols)
        
        # Should be called once for each custom symbol
        assert mock_fetch_symbol.call_count == 3
        
        # Check result structure
        assert isinstance(result, dict)
        assert len(result) == 3
        for symbol in custom_symbols:
            assert symbol in result

    def test_fetch_custom_symbols_empty_list(self):
        """Test fetching custom symbols with empty list."""
        fetcher = NYSEDataFetcher()
        result = fetcher.fetch_custom_symbols([])
        
        assert isinstance(result, dict)
        assert len(result) == 0

    def test_fetch_custom_symbols_with_duplicates(self):
        """Test fetching custom symbols with duplicate symbols."""
        with patch.object(NYSEDataFetcher, '_fetch_symbol_data') as mock_fetch:
            mock_data = pd.DataFrame({
                'open': [220.0],
                'high': [225.0],
                'low': [219.0],
                'close': [224.5],
                'volume': [1000000]
            })
            
            mock_fetch.return_value = mock_data
            
            fetcher = NYSEDataFetcher()
            symbols_with_duplicates = ["AAPL", "MSFT", "AAPL"]
            result = fetcher.fetch_custom_symbols(symbols_with_duplicates)
            
            # Should only fetch each unique symbol once
            assert mock_fetch.call_count == 2
            assert len(result) == 2
            assert "AAPL" in result
            assert "MSFT" in result

    def test_str_representation(self):
        """Test string representation of fetcher."""
        fetcher = NYSEDataFetcher()
        str_repr = str(fetcher)
        
        assert "NYSEDataFetcher" in str_repr
        assert "magnificent_seven" in str_repr.lower()

    def test_repr_representation(self):
        """Test repr representation of fetcher."""
        fetcher = NYSEDataFetcher()
        repr_str = repr(fetcher)
        
        assert "NYSEDataFetcher" in repr_str
