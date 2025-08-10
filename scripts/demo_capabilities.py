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


def demo_stock_data(client: AlphaVantageClient) -> None:
    """Demonstrate stock data functionality."""
    print("=" * 60)
    print("STOCK DATA DEMONSTRATION")
    print("=" * 60)

    try:
        # Get Apple stock data
        print("Getting AAPL daily stock data...")
        stock_data = client.get_daily_data("AAPL")
        latest_date = stock_data.iloc[-1]["Date"].strftime("%Y-%m-%d")
        latest_close = stock_data.iloc[-1]["Close"]
        print(f"[SUCCESS] AAPL latest close ({latest_date}): ${latest_close:.2f}")
        print(f"   Data points: {len(stock_data)} days")

        # Get company overview
        print("\nGetting AAPL company overview...")
        overview = client.get_company_overview("AAPL")
        company_name = overview.get("Name", "N/A")
        market_cap = overview.get("MarketCapitalization", "N/A")
        print(f"[SUCCESS] Company: {company_name}")
        print(f"   Market Cap: ${market_cap}")

    except AlphaVantageAPIError as e:
        print(f"[ERROR] Stock data error: {e}")


def demo_forex_data(client: AlphaVantageClient) -> None:
    """Demonstrate forex data functionality."""
    print("\n" + "=" * 60)
    print("FOREX DATA DEMONSTRATION")
    print("=" * 60)

    try:
        # Get real-time exchange rate
        print("Getting USD/EUR exchange rate...")
        exchange_data = client.get_currency_exchange_rate("USD", "EUR")
        rate_info = exchange_data["Realtime Currency Exchange Rate"]
        exchange_rate = float(rate_info["5. Exchange Rate"])
        last_refreshed = rate_info["6. Last Refreshed"]
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
    print("\n" + "=" * 60)
    print("CRYPTOCURRENCY DATA DEMONSTRATION")
    print("=" * 60)

    try:
        # Get Bitcoin exchange rate
        print("Getting BTC/USD exchange rate...")
        btc_rate = client.get_currency_exchange_rate("BTC", "USD")
        rate_info = btc_rate["Realtime Currency Exchange Rate"]
        btc_price = float(rate_info["5. Exchange Rate"])
        last_refreshed = rate_info["6. Last Refreshed"]
        print(f"[SUCCESS] BTC/USD rate: ${btc_price:,.2f}")
        print(f"   Last updated: {last_refreshed}")

        # Get historical crypto data
        print("\nGetting BTC historical data...")
        crypto_history = client.get_digital_currency_daily("BTC", "USD")
        latest_date = crypto_history.iloc[-1]["Date"].strftime("%Y-%m-%d")
        latest_close = crypto_history.iloc[-1]["Close_USD"]
        latest_volume = crypto_history.iloc[-1]["Volume"]
        print(f"[SUCCESS] BTC latest close ({latest_date}): ${latest_close:,.2f}")
        print(f"   Volume: {latest_volume:,.2f} BTC")
        print(f"   Historical data points: {len(crypto_history)} days")

        # Try Ethereum as well
        print("\nGetting ETH/USD exchange rate...")
        eth_rate = client.get_currency_exchange_rate("ETH", "USD")
        eth_info = eth_rate["Realtime Currency Exchange Rate"]
        eth_price = float(eth_info["5. Exchange Rate"])
        print(f"[SUCCESS] ETH/USD rate: ${eth_price:,.2f}")

    except AlphaVantageAPIError as e:
        print(f"[ERROR] Crypto data error: {e}")


def demo_comprehensive_analysis(client: AlphaVantageClient) -> None:
    """Demonstrate comprehensive multi-asset analysis."""
    print("\n" + "=" * 60)
    print("COMPREHENSIVE MARKET ANALYSIS")
    print("=" * 60)

    try:
        print("Cross-asset comparison using single API...")

        # Get multiple exchange rates for comparison
        rates = {}
        symbols = [("USD", "EUR"), ("USD", "GBP"), ("USD", "JPY")]

        for from_curr, to_curr in symbols:
            try:
                data = client.get_currency_exchange_rate(from_curr, to_curr)
                rate = float(
                    data["Realtime Currency Exchange Rate"]["5. Exchange Rate"]
                )
                rates[f"{from_curr}/{to_curr}"] = rate
                print(f"[SUCCESS] {from_curr}/{to_curr}: {rate:.6f}")
            except AlphaVantageAPIError as e:
                print(f"[ERROR] {from_curr}/{to_curr}: {e}")

        # Show crypto vs fiat comparison
        try:
            btc_usd = client.get_currency_exchange_rate("BTC", "USD")
            btc_price = float(
                btc_usd["Realtime Currency Exchange Rate"]["5. Exchange Rate"]
            )

            if "USD/EUR" in rates:
                btc_eur_equivalent = btc_price * rates["USD/EUR"]
                print("\nCross-currency calculation:")
                print(f"   BTC: ${btc_price:,.2f} USD = €{btc_eur_equivalent:,.2f} EUR")

        except AlphaVantageAPIError as e:
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

    print("\n" + "=" * 60)
    print("DEMONSTRATION COMPLETE!")
    print("=" * 60)
    print("[SUCCESS] Stocks: Daily prices, company overviews")
    print("[SUCCESS] Forex: Real-time rates, historical data")
    print("[SUCCESS] Crypto: Real-time prices, historical data")
    print("[SUCCESS] Cross-asset: Multi-currency calculations")
    print("\nAll capabilities delivered through a single, unified API!")
    print("Ready for Issue #1 completion and future enhancements!")


if __name__ == "__main__":
    main()
