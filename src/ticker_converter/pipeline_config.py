"""Configuration classes for financial data pipeline."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class PeriodType(str, Enum):
    """Time period types for data fetching."""

    ONE_MONTH = "1mo"
    THREE_MONTHS = "3mo"
    ONE_YEAR = "1y"
    FIVE_YEARS = "5y"
    MAX = "max"


@dataclass
class PipelineConfig:
    """Configuration for financial data pipeline operations."""

    # API Configuration
    api_key: Optional[str] = None
    timeout: int = 30
    max_retries: int = 3
    rate_limit_delay: float = 1.0

    # Data Processing Configuration
    default_period: PeriodType = PeriodType.ONE_MONTH
    include_symbol_in_data: bool = True
    validate_data: bool = True

    # Error Handling Configuration
    suppress_api_errors: bool = False
    return_empty_on_error: bool = True
    log_errors: bool = True

    # Period to outputsize mapping
    compact_periods: list[str] = field(default_factory=lambda: ["1mo", "3mo"])

    def get_outputsize(self, period: str) -> str:
        """Get Alpha Vantage outputsize parameter for given period.

        Args:
            period: Time period string

        Returns:
            'compact' or 'full' depending on period
        """
        from .constants import OutputSize

        return OutputSize.COMPACT if period in self.compact_periods else OutputSize.FULL
