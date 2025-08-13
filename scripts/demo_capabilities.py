#!/usr/bin/env python3
"""Demonstration script showing the expanded Alpha Vantage client capabilities.

This script demonstrates:
1. Stock data (daily price history and company overview)
2. Forex data (currency exchange rates and historical data)
3. Cryptocurrency data (real-time rates and historical data)

All using the single Alpha Vantage API.
"""

from datetime import datetime

from ticker_converter.api_clients.api_client import (
    AlphaVantageAPIError,
    AlphaVantageClient,
)
from ticker_converter.api_clients.constants import (
    AlphaVantageResponseKey,
    AlphaVantageValueKey,
    config,
)

try:
    from demo_config import DEMO_CONFIG
except ImportError:
    # Fallback for when running as script
    import sys
    from pathlib import Path

    sys.path.append(str(Path(__file__).parent))
    from demo_config import DEMO_CONFIG


class DemoRunner:
    """Encapsulates demo functionality with error handling."""

    def __init__(self, client: AlphaVantageClient):
        """Initialize demo runner with API client."""
        self.client = client

    def print_section_header(self, title: str) -> None:
        """Print a formatted section header."""
        print(f"\n{DEMO_CONFIG.SEPARATOR}")
        print(title)
        print(DEMO_CONFIG.SEPARATOR)

    def safe_get_exchange_rate(self, from_curr: str, to_curr: str) -> float | None:
        """Safely get exchange rate between two currencies.

        Args:
            from_curr: Source currency code
            to_curr: Target currency code

        Returns:
            Exchange rate as float, or None if error occurred
        """
        try:
            data = self.client.get_currency_exchange_rate(from_curr, to_curr)
            rate_info = data[AlphaVantageResponseKey.REALTIME_CURRENCY_EXCHANGE_RATE]
            return float(rate_info[AlphaVantageValueKey.EXCHANGE_RATE])
        except (AlphaVantageAPIError, KeyError, ValueError) as e:
            print(f"[ERROR] {from_curr}/{to_curr}: {e}")
            return None

    def demo_stock_data(self) -> None:
        """Demonstrate stock data functionality."""
        self.print_section_header("STOCK DATA DEMONSTRATION")

        try:
            symbol = DEMO_CONFIG.STOCK_SYMBOL
            print(f"Getting {symbol} daily stock data...")

            stock_data = self.client.get_daily_stock_data(symbol)
            latest_date = stock_data.iloc[-1]["Date"].strftime("%Y-%m-%d")
            latest_close = stock_data.iloc[-1]["Close"]

            print(
                f"[SUCCESS] {symbol} latest close ({latest_date}): "
                f"${latest_close:.{DEMO_CONFIG.PRICE_PRECISION}f}"
            )
            print(f"   Data points: {len(stock_data)} days")

            # Get company overview
            print(f"\nGetting {symbol} company overview...")
            overview = self.client.get_company_overview(symbol)
            company_name = overview.get("Name", "N/A")
            market_cap = overview.get("MarketCapitalization", "N/A")

            print(f"[SUCCESS] Company: {company_name}")
            print(f"   Market Cap: ${market_cap}")

        except AlphaVantageAPIError as e:
            print(f"[ERROR] Stock data error: {e}")

    def demo_forex_data(self) -> None:
        """Demonstrate forex data functionality."""
        self.print_section_header("FOREX DATA DEMONSTRATION")

        try:
            # Get real-time exchange rate
            print("Getting USD/EUR exchange rate...")
            exchange_data = self.client.get_currency_exchange_rate("USD", "EUR")
            rate_info = exchange_data[
                AlphaVantageResponseKey.REALTIME_CURRENCY_EXCHANGE_RATE
            ]
            exchange_rate = float(rate_info[AlphaVantageValueKey.EXCHANGE_RATE])
            last_refreshed = rate_info[AlphaVantageValueKey.LAST_REFRESHED]

            print(
                f"[SUCCESS] USD/EUR rate: "
                f"{exchange_rate:.{DEMO_CONFIG.RATE_PRECISION}f}"
            )
            print(f"   Last updated: {last_refreshed}")

            # Get historical forex data
            print("\nGetting EUR/USD historical data...")
            forex_history = self.client.get_forex_daily("EUR", "USD")
            latest_date = forex_history.iloc[-1]["Date"].strftime("%Y-%m-%d")
            latest_close = forex_history.iloc[-1]["Close"]

            print(
                f"[SUCCESS] EUR/USD latest close ({latest_date}): "
                f"{latest_close:.{DEMO_CONFIG.RATE_PRECISION}f}"
            )
            print(f"   Historical data points: {len(forex_history)} days")

        except AlphaVantageAPIError as e:
            print(f"[ERROR] Forex data error: {e}")

    def demo_crypto_data(self) -> None:
        """Demonstrate cryptocurrency data functionality."""
        self.print_section_header("CRYPTOCURRENCY DATA DEMONSTRATION")

        try:
            # Get exchange rates for multiple cryptocurrencies
            for symbol in DEMO_CONFIG.CRYPTO_SYMBOLS:
                print(f"Getting {symbol}/USD exchange rate...")
                rate = self.safe_get_exchange_rate(symbol, "USD")
                if rate is not None:
                    print(
                        f"[SUCCESS] {symbol}/USD rate: "
                        f"${rate:,.{DEMO_CONFIG.PRICE_PRECISION}f}"
                    )

            # Get historical crypto data for Bitcoin
            print("\nGetting BTC historical data...")
            crypto_history = self.client.get_digital_currency_daily("BTC", "USD")
            latest_date = crypto_history.iloc[-1]["Date"].strftime("%Y-%m-%d")

            # Handle different possible column names for close price
            latest_close = self._get_close_price(crypto_history)

            if latest_close is not None:
                print(
                    f"[SUCCESS] BTC latest close ({latest_date}): "
                    f"${latest_close:,.{DEMO_CONFIG.PRICE_PRECISION}f}"
                )

            if "Volume" in crypto_history.columns:
                latest_volume = crypto_history.iloc[-1]["Volume"]
                print(
                    f"   Volume: {latest_volume:,.{DEMO_CONFIG.PRICE_PRECISION}f} BTC"
                )

            print(f"   Historical data points: {len(crypto_history)} days")

        except AlphaVantageAPIError as e:
            print(f"[ERROR] Crypto data error: {e}")

    def _get_close_price(self, crypto_history) -> float | None:
        """Extract close price from crypto data with multiple column formats."""
        for col in DEMO_CONFIG.CLOSE_COLUMNS:
            if col in crypto_history.columns:
                return crypto_history.iloc[-1][col]
        return None

    def demo_comprehensive_analysis(self) -> None:
        """Demonstrate comprehensive multi-asset analysis."""
        self.print_section_header("COMPREHENSIVE MARKET ANALYSIS")

        try:
            print("Cross-asset comparison using single API...")

            # Get multiple exchange rates for comparison
            rates = {}
            for from_curr, to_curr in DEMO_CONFIG.CURRENCY_PAIRS:
                rate = self.safe_get_exchange_rate(from_curr, to_curr)
                if rate is not None:
                    pair_key = f"{from_curr}/{to_curr}"
                    rates[pair_key] = rate
                    print(
                        f"[SUCCESS] {pair_key}: "
                        f"{rate:.{DEMO_CONFIG.RATE_PRECISION}f}"
                    )

            # Show crypto vs fiat comparison
            self._show_cross_currency_calculation(rates)

        except AlphaVantageAPIError as e:
            print(f"[ERROR] Comprehensive analysis error: {e}")

    def _show_cross_currency_calculation(self, rates: dict) -> None:
        """Demonstrate cross-currency calculations."""
        try:
            btc_price = self.safe_get_exchange_rate("BTC", "USD")
            if btc_price and "USD/EUR" in rates:
                btc_eur_equivalent = btc_price * rates["USD/EUR"]
                print("\nCross-currency calculation:")
                print(
                    f"   BTC: ${btc_price:,.{DEMO_CONFIG.PRICE_PRECISION}f} USD = "
                    f"€{btc_eur_equivalent:,.{DEMO_CONFIG.PRICE_PRECISION}f} EUR"
                )

        except (KeyError, TypeError) as e:
            print(f"[ERROR] Cross-currency calculation error: {e}")


def print_demo_intro() -> None:
    """Print introduction message."""
    print("Alpha Vantage API Client - Comprehensive Demo")
    print(f"Running at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\nThis demo showcases the complete financial data capabilities")
    print("of the Alpha Vantage API - stocks, forex, and crypto in one place!")


def print_demo_summary() -> None:
    """Print demo completion summary."""
    print(f"\n{DEMO_CONFIG.SEPARATOR}")
    print("DEMONSTRATION COMPLETE!")
    print(f"{DEMO_CONFIG.SEPARATOR}")
    print("[SUCCESS] Stocks: Daily prices, company overviews")
    print("[SUCCESS] Forex: Real-time rates, historical data")
    print("[SUCCESS] Crypto: Real-time prices, historical data")
    print("[SUCCESS] Cross-asset: Multi-currency calculations")
    print("\nAll capabilities delivered through a single, unified API!")
    print("Ready for Issue #1 completion and future enhancements!")


def main() -> None:
    """Main demonstration function."""
    print_demo_intro()

    # Initialize client
    if not config.api_key or config.api_key == "demo":
        print("\n[ERROR] Valid API key not found in environment!")
        print("Please set your API key to run this demo:")
        print("export ALPHA_VANTAGE_API_KEY='your_key_here'")
        return

    client = AlphaVantageClient(config.api_key)
    print("[SUCCESS] Alpha Vantage client initialized")

    # Run demonstrations
    demo = DemoRunner(client)
    demo.demo_stock_data()
    demo.demo_forex_data()
    demo.demo_crypto_data()
    demo.demo_comprehensive_analysis()

    print_demo_summary()


if __name__ == "__main__":
    main()
