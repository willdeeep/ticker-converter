"""Tests for market data models validation."""

from datetime import datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError

from ticker_converter.data_models.market_data import MarketDataPoint


class TestMarketDataPointValidation:
    """Test MarketDataPoint validation logic."""

    def test_valid_market_data_point(self) -> None:
        """Test creating a valid market data point."""
        data = MarketDataPoint(
            symbol="AAPL",
            timestamp=datetime(2025, 1, 1),
            open=Decimal("150.0"),
            high=Decimal("155.0"),
            low=Decimal("149.0"),
            close=Decimal("154.0"),
            volume=1000000,
        )
        assert data.symbol == "AAPL"
        assert data.high == Decimal("155.0")

    def test_high_less_than_low_raises_error(self) -> None:
        """Test that high < low raises validation error."""
        with pytest.raises(
            ValidationError,
            match=r"High price \(149\.0\) cannot be less than low price \(150\.0\)",
        ):
            MarketDataPoint(
                symbol="AAPL",
                timestamp=datetime(2025, 1, 1),
                open=Decimal("150.0"),
                high=Decimal("149.0"),  # High less than low
                low=Decimal("150.0"),
                close=Decimal("149.5"),
                volume=1000000,
            )

    def test_close_outside_high_low_range_raises_error(self) -> None:
        """Test that close price outside high/low range raises error."""
        with pytest.raises(
            ValidationError,
            match=r"High price \(155\.0\) cannot be less than close price \(156\.0\)",
        ):
            MarketDataPoint(
                symbol="AAPL",
                timestamp=datetime(2025, 1, 1),
                open=Decimal("150.0"),
                high=Decimal("155.0"),
                low=Decimal("149.0"),
                close=Decimal("156.0"),  # Close above high
                volume=1000000,
            )

    def test_close_below_low_raises_error(self) -> None:
        """Test that close price below low raises error."""
        with pytest.raises(
            ValidationError,
            match=r"Low price \(149\.0\) cannot be greater than close price \(148\.0\)",
        ):
            MarketDataPoint(
                symbol="AAPL",
                timestamp=datetime(2025, 1, 1),
                open=Decimal("150.0"),
                high=Decimal("155.0"),
                low=Decimal("149.0"),
                close=Decimal("148.0"),  # Close below low
                volume=1000000,
            )

    def test_negative_volume_raises_error(self) -> None:
        """Test that negative volume raises validation error."""
        with pytest.raises(
            ValidationError, match="Input should be greater than or equal to 0"
        ):
            MarketDataPoint(
                symbol="AAPL",
                timestamp=datetime(2025, 1, 1),
                open=Decimal("150.0"),
                high=Decimal("155.0"),
                low=Decimal("149.0"),
                close=Decimal("154.0"),
                volume=-1000,  # Negative volume
            )
