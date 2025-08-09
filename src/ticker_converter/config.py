"""Configuration management for the ticker converter."""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Application configuration from environment variables."""
    
    # API Keys
    ALPHA_VANTAGE_API_KEY: Optional[str] = os.getenv("ALPHA_VANTAGE_API_KEY")
    
    # API Configuration
    API_TIMEOUT: int = int(os.getenv("API_TIMEOUT", "30"))
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
    RATE_LIMIT_DELAY: float = float(os.getenv("RATE_LIMIT_DELAY", "1.0"))
    
    # API Base URLs
    ALPHA_VANTAGE_BASE_URL = "https://www.alphavantage.co/query"
    
    @classmethod
    def validate_api_keys(cls) -> dict[str, bool]:
        """Validate that required API keys are present.
        
        Returns:
            Dictionary with API key validation status.
        """
        return {
            "alpha_vantage": cls.ALPHA_VANTAGE_API_KEY is not None,
        }
    
    @classmethod
    def get_missing_keys(cls) -> list[str]:
        """Get list of missing API keys.
        
        Returns:
            List of missing API key names.
        """
        validation = cls.validate_api_keys()
        return [key for key, is_valid in validation.items() if not is_valid]


# Global config instance
config = Config()
