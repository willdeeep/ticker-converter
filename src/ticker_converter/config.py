"""Configuration management for the ticker converter."""

import os
from typing import Optional

from dotenv import load_dotenv


class Config:
    """Application configuration from environment variables."""

    def __init__(self) -> None:
        """Initialize configuration by loading environment variables."""
        # Load environment variables from .env file
        load_dotenv()

        # API Keys
        self.ALPHA_VANTAGE_API_KEY: Optional[str] = os.getenv("ALPHA_VANTAGE_API_KEY")

        # API Configuration
        self.API_TIMEOUT: int = int(os.getenv("API_TIMEOUT") or "30")
        self.MAX_RETRIES: int = int(os.getenv("MAX_RETRIES") or "3")
        self.RATE_LIMIT_DELAY: float = float(os.getenv("RATE_LIMIT_DELAY") or "1.0")

        # API Base URLs
        self.ALPHA_VANTAGE_BASE_URL = "https://www.alphavantage.co/query"

    def validate_api_keys(self) -> dict[str, bool]:
        """Validate that required API keys are present.

        Returns:
            Dictionary with API key validation status.
        """
        return {
            "alpha_vantage": self.ALPHA_VANTAGE_API_KEY is not None,
        }

    def get_missing_keys(self) -> list[str]:
        """Get list of missing API keys.

        Returns:
            List of missing API key names.
        """
        validation = self.validate_api_keys()
        return [key for key, is_valid in validation.items() if not is_valid]


# Global config instance
config = Config()


# Global config instance
config = Config()
