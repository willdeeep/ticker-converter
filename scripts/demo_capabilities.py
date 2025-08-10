#!/usr/bin/env python3
"""Demonstration script showing the expanded Alpha Vantage client capabilities.

This script demonstrates:
1. Stock data (daily price history and company overview)
2. Forex data (currency exchange rates and historical data)
3. Cryptocurrency data (real-time rates and historical data)

All using the single Alpha Vantage API.
"""

from datetime import datetime

from ticker_converter.api_client import AlphaVantageAPIError, AlphaVantageClient
from ticker_converter.config import config
from ticker_converter.constants import AlphaVantageResponseKey, AlphaVantageValueKey

# Demo configuration constants
DEMO_SEPARATOR = "=" * 60
DEMO_SYMBOLS = {
    "stock": "AAPL",
    "crypto_symbols": ["BTC", "ETH"],
    "cross_analysis_pairs": [("USD", "EUR"), ("USD", "GBP"), ("USD", "JPY")],
}


def print_section_header(title: str) -> None:
    """Print a formatted section header."""
    print("\n" + DEMO_SEPARATOR)
    print(title)
    print(DEMO_SEPARATOR)


def safe_get_exchange_rate(
    client: AlphaVantageClient, from_curr: str, to_curr: str
) -> float | None:
    """Safely get exchange rate between two currencies.

    Args:
        client: Alpha Vantage API client
        from_curr: Source currency code
        to_curr: Target currency code

    Returns:
        Exchange rate as float, or None if error occurred
    """
    try:
        data = client.get_currency_exchange_rate(from_curr, to_curr)
        rate_info = data[AlphaVantageResponseKey.REALTIME_CURRENCY_EXCHANGE_RATE]
        return float(rate_info[AlphaVantageValueKey.EXCHANGE_RATE])
    except (AlphaVantageAPIError, KeyError, ValueError) as e:
        print(f"[ERROR] {from_curr}/{to_curr}: {e}")
        return None


def demo_stock_data(client: AlphaVantageClient) -> None:
    """Demonstrate stock data functionality."""
    print_section_header("STOCK DATA DEMONSTRATION")

    try:
        # Get Apple stock data
        symbol = DEMO_SYMBOLS["stock"]
        print(f"Getting {symbol} daily stock data...")
        stock_data = client.get_daily_data(symbol)
        latest_date = stock_data.iloc[-1]["Date"].strftime("%Y-%m-%d")
        latest_close = stock_data.iloc[-1]["Close"]
        print(f"[SUCCESS] {symbol} latest close ({latest_date}): ${latest_close:.2f}")
        print(f"   Data points: {len(stock_data)} days")

        # Get company overview
        print(f"\nGetting {symbol} company overview...")
        overview = client.get_company_overview(symbol)
        company_name = overview.get("Name", "N/A")
        market_cap = overview.get("MarketCapitalization", "N/A")
        print(f"[SUCCESS] Company: {company_name}")
        print(f"   Market Cap: ${market_cap}")

    except AlphaVantageAPIError as e:
        print(f"[ERROR] Stock data error: {e}")


def demo_forex_data(client: AlphaVantageClient) -> None:
    """Demonstrate forex data functionality."""
    print_section_header("FOREX DATA DEMONSTRATION")

    try:
        # Get real-time exchange rate
        print("Getting USD/EUR exchange rate...")
        exchange_data = client.get_currency_exchange_rate("USD", "EUR")
        rate_info = exchange_data[
            AlphaVantageResponseKey.REALTIME_CURRENCY_EXCHANGE_RATE
        ]
        exchange_rate = float(rate_info[AlphaVantageValueKey.EXCHANGE_RATE])
        last_refreshed = rate_info[AlphaVantageValueKey.LAST_REFRESHED]
        print(f"[SUCCESS] USD/EUR rate: {exchange_rate:.6f}")
        print(f"   Last updated: {last_refreshed}")

        # Get historical forex data
        print("\nGetting EUR/USD historical data...")
        forex_history = client.get_forex_daily("EUR", "USD")
        latest_date = forex_history.iloc[-1]["Date"].strftime("%Y-%m-%d")
        latest_close = forex_history.iloc[-1]["Close"]
        print(f"[SUCCESS] EUR/USD latest close ({latest_date}): {latest_close:.6f}")
        print(f"   Historical data points: {len(forex_history)} days")

    except AlphaVantageAPIError as e:
        print(f"[ERROR] Forex data error: {e}")


def demo_crypto_data(client: AlphaVantageClient) -> None:
    """Demonstrate cryptocurrency data functionality."""
    print_section_header("CRYPTOCURRENCY DATA DEMONSTRATION")

    try:
        # Get Bitcoin exchange rate
        crypto_symbols = DEMO_SYMBOLS["crypto_symbols"]

        for symbol in crypto_symbols:
            print(f"Getting {symbol}/USD exchange rate...")
            rate = safe_get_exchange_rate(client, symbol, "USD")
            if rate is not None:
                print(f"[SUCCESS] {symbol}/USD rate: ${rate:,.2f}")

        # Get historical crypto data for Bitcoin
        print("\nGetting BTC historical data...")
        crypto_history = client.get_digital_currency_daily("BTC", "USD")
        latest_date = crypto_history.iloc[-1]["Date"].strftime("%Y-%m-%d")

        # Handle different possible column names for close price
        close_columns = ["Close_USD", "Close", "4a. close (USD)"]
        latest_close = None
        for col in close_columns:
            if col in crypto_history.columns:
                latest_close = crypto_history.iloc[-1][col]
                break

        if latest_close is not None:
            print(f"[SUCCESS] BTC latest close ({latest_date}): ${latest_close:,.2f}")

        if "Volume" in crypto_history.columns:
            latest_volume = crypto_history.iloc[-1]["Volume"]
            print(f"   Volume: {latest_volume:,.2f} BTC")

        print(f"   Historical data points: {len(crypto_history)} days")

    except AlphaVantageAPIError as e:
        print(f"[ERROR] Crypto data error: {e}")


def demo_comprehensive_analysis(client: AlphaVantageClient) -> None:
    """Demonstrate comprehensive multi-asset analysis."""
    print_section_header("COMPREHENSIVE MARKET ANALYSIS")

    try:
        print("Cross-asset comparison using single API...")

        # Get multiple exchange rates for comparison
        rates = {}
        for from_curr, to_curr in DEMO_SYMBOLS["cross_analysis_pairs"]:
            rate = safe_get_exchange_rate(client, from_curr, to_curr)
            if rate is not None:
                rates[f"{from_curr}/{to_curr}"] = rate
                print(f"[SUCCESS] {from_curr}/{to_curr}: {rate:.6f}")

        # Show crypto vs fiat comparison
        try:
            btc_price = safe_get_exchange_rate(client, "BTC", "USD")
            if btc_price and "USD/EUR" in rates:
                btc_eur_equivalent = btc_price * rates["USD/EUR"]
                print("\nCross-currency calculation:")
                print(f"   BTC: ${btc_price:,.2f} USD = €{btc_eur_equivalent:,.2f} EUR")

        except (KeyError, TypeError) as e:
            print(f"[ERROR] Cross-currency calculation error: {e}")

    except AlphaVantageAPIError as e:
        print(f"[ERROR] Comprehensive analysis error: {e}")


def main() -> None:
    """Main demonstration function."""
    print("Alpha Vantage API Client - Comprehensive Demo")
    print(f"Running at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\nThis demo showcases the complete financial data capabilities")
    print("of the Alpha Vantage API - stocks, forex, and crypto in one place!")

    # Initialize client
    if not config.ALPHA_VANTAGE_API_KEY:
        print("\n[ERROR] ALPHA_VANTAGE_API_KEY not found in environment!")
        print("Please set your API key to run this demo:")
        print("export ALPHA_VANTAGE_API_KEY='your_key_here'")
        return

    client = AlphaVantageClient(config.ALPHA_VANTAGE_API_KEY)
    print("[SUCCESS] Alpha Vantage client initialized")

    # Run demonstrations
    demo_stock_data(client)
    demo_forex_data(client)
    demo_crypto_data(client)
    demo_comprehensive_analysis(client)

    print_section_header("DEMONSTRATION COMPLETE!")
    print("[SUCCESS] Stocks: Daily prices, company overviews")
    print("[SUCCESS] Forex: Real-time rates, historical data")
    print("[SUCCESS] Crypto: Real-time prices, historical data")
    print("[SUCCESS] Cross-asset: Multi-currency calculations")
    print("\nAll capabilities delivered through a single, unified API!")
    print("Ready for Issue #1 completion and future enhancements!")


if __name__ == "__main__":
    main()
