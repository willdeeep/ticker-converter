"""Unit tests for configuration module."""

import os
from unittest.mock import patch

from src.ticker_converter.config import Config


class TestConfig:
    """Test configuration management."""
    
    def test_config_loads_environment_variables(self):
        """Test that config loads environment variables correctly."""
        with patch.dict(os.environ, {
            'ALPHA_VANTAGE_API_KEY': 'test_key_123',
            'API_TIMEOUT': '45',
            'MAX_RETRIES': '5',
            'RATE_LIMIT_DELAY': '2.0'
        }):
            # Create new config instance to reload env vars
            test_config = Config()
            
            assert test_config.ALPHA_VANTAGE_API_KEY == 'test_key_123'
            assert test_config.API_TIMEOUT == 45
            assert test_config.MAX_RETRIES == 5
            assert test_config.RATE_LIMIT_DELAY == 2.0
    
    def test_config_default_values(self):
        """Test that config uses default values when env vars not set."""
        with patch.dict(os.environ, {'ALPHA_VANTAGE_API_KEY': ''}, clear=True):
            with patch('os.getenv') as mock_getenv:
                mock_getenv.side_effect = lambda key, default=None: {
                    'ALPHA_VANTAGE_API_KEY': None,
                    'API_TIMEOUT': default,
                    'MAX_RETRIES': default,
                    'RATE_LIMIT_DELAY': default
                }.get(key, default)
                
                test_config = Config()
                
                assert test_config.ALPHA_VANTAGE_API_KEY is None
                assert test_config.API_TIMEOUT == 30
                assert test_config.MAX_RETRIES == 3
                assert test_config.RATE_LIMIT_DELAY == 1.0
    
    def test_base_urls_are_correct(self):
        """Test that API base URLs are set correctly."""
        test_config = Config()
        
        assert test_config.ALPHA_VANTAGE_BASE_URL == "https://www.alphavantage.co/query"
    
    def test_validate_api_keys_with_key(self):
        """Test API key validation when key is present."""
        with patch.dict(os.environ, {'ALPHA_VANTAGE_API_KEY': 'test_key'}):
            test_config = Config()
            validation = test_config.validate_api_keys()
            
            assert validation['alpha_vantage'] is True
    
    def test_validate_api_keys_without_key(self):
        """Test API key validation when key is missing."""
        with patch('os.getenv') as mock_getenv:
            mock_getenv.return_value = None
            test_config = Config()
            validation = test_config.validate_api_keys()
            
            assert validation['alpha_vantage'] is False
    
    def test_get_missing_keys_with_key(self):
        """Test getting missing keys when key is present."""
        with patch.dict(os.environ, {'ALPHA_VANTAGE_API_KEY': 'test_key'}):
            test_config = Config()
            missing = test_config.get_missing_keys()
            
            assert missing == []
    
    def test_get_missing_keys_without_key(self):
        """Test getting missing keys when key is absent."""
        with patch('os.getenv') as mock_getenv:
            mock_getenv.return_value = None
            test_config = Config()
            missing = test_config.get_missing_keys()
            
            assert 'alpha_vantage' in missing
