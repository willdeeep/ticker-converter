"""Configuration constants and enums for demo script."""

from dataclasses import dataclass, field
from enum import Enum


class DemoSymbols(Enum):
    """Demo stock symbols."""

    APPLE = "AAPL"
    MICROSOFT = "MSFT"
    TESLA = "TSLA"


class CryptoSymbols(Enum):
    """Cryptocurrency symbols."""

    BITCOIN = "BTC"
    ETHEREUM = "ETH"
    CARDANO = "ADA"


@dataclass(frozen=True)
class DemoConfig:
    """Configuration for demo script."""

    # Display constants
    SEPARATOR: str = "=" * 60
    SECTION_WIDTH: int = 60

    # Demo symbols
    STOCK_SYMBOL: str = DemoSymbols.APPLE.value
    CRYPTO_SYMBOLS: list[str] = field(
        default_factory=lambda: [
            CryptoSymbols.BITCOIN.value,
            CryptoSymbols.ETHEREUM.value,
        ]
    )

    # Currency pairs for cross-analysis
    CURRENCY_PAIRS: list[tuple[str, str]] = field(
        default_factory=lambda: [
            ("USD", "EUR"),
            ("USD", "GBP"),
            ("USD", "JPY"),
        ]
    )

    # API response column mappings
    CLOSE_COLUMNS: list[str] = field(
        default_factory=lambda: ["Close_USD", "Close", "4a. close (USD)"]
    )

    # Formatting
    PRICE_PRECISION: int = 2
    RATE_PRECISION: int = 6


# Singleton instance
DEMO_CONFIG = DemoConfig()
