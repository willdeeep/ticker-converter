#!/usr/bin/env python3
"""Script to examine API data retrieval and storage functionality.

This script is designed to be conservative with API calls to stay within
Alpha Vantage's free tier limit of 25 requests per day.
"""

import os
import time
from datetime import datetime
from pathlib import Path

import pandas as pd

from ticker_converter.api_client import AlphaVantageClient, AlphaVantageAPIError
from ticker_converter.config import config
from ticker_converter.storage import StorageConfig, StorageFactory


def check_rate_limit_response(response_data):
    """Check if the API response indicates rate limiting.
   
    Args:
        response_data: Raw API response data
       
    Returns:
        tuple: (is_rate_limited, message)
    """
    if isinstance(response_data, dict):
        # Check for rate limit information message
        if "Information" in response_data:
            info_msg = response_data["Information"]
            if "rate limit" in info_msg.lower():
                return True, info_msg
       
        # Check for error messages
        if "Error Message" in response_data:
            return True, response_data["Error Message"]
           
        # Check for note about API calls
        if "Note" in response_data:
            note_msg = response_data["Note"]
            if "api call" in note_msg.lower() or "per minute" in note_msg.lower():
                return True, note_msg
   
    return False, None


def safe_api_call(func, *args, **kwargs):
    """Safely make an API call with rate limit detection.
   
    Args:
        func: API function to call
        *args: Function arguments
        **kwargs: Function keyword arguments
       
    Returns:
        tuple: (success, data_or_error_message)
    """
    try:
        result = func(*args, **kwargs)
        return True, result
    except AlphaVantageAPIError as e:
        error_msg = str(e)
        if "rate limit" in error_msg.lower() or "per day" in error_msg.lower():
            return False, f"Rate limit exceeded: {error_msg}"
        return False, f"API Error: {error_msg}"
    except Exception as e:
        return False, f"Unexpected error: {e}"


def examine_api_data():
    """Fetch and examine data from the Alpha Vantage API."""

    # Check if API key is available
    api_key = config.ALPHA_VANTAGE_API_KEY
    if not api_key or api_key == "your_api_key_here":
        print("❌ Alpha Vantage API key not found!")
        print("Please set the ALPHA_VANTAGE_API_KEY environment variable")
        print("Example: export ALPHA_VANTAGE_API_KEY='your_key_here'")
        return

    print("🔑 API Key found, initializing client...")
    client = AlphaVantageClient(api_key)
   
    # Keep track of API calls made
    api_calls_made = 0
    max_calls_per_run = 3  # Conservative limit to avoid hitting daily limit

    try:
        print(f"\n📈 Fetching AAPL daily stock data... (API call {api_calls_made + 1})")
        success, result = safe_api_call(client.get_daily_stock_data, "AAPL")
        api_calls_made += 1
       
        if not success:
            print(f"❌ Failed to fetch stock data: {result}")
            return
           
        stock_data = result

        print(f"✅ Retrieved {len(stock_data)} records")
        print(f"📅 Date range: {stock_data['Date'].min()} to {stock_data['Date'].max()}")
        print(f"📊 Columns: {list(stock_data.columns)}")
        print(f"💰 Latest close price: ${stock_data.iloc[-1]['Close']:.2f}")

        print("\n🔍 Data sample (last 5 rows):")
        print(stock_data.tail().to_string(index=False))

        print(f"\n📋 Data types:")
        for col, dtype in stock_data.dtypes.items():
            print(f"  {col}: {dtype}")

        print(f"\n📊 Data statistics:")
        numeric_cols = stock_data.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 0:
            print(stock_data[numeric_cols].describe())

        # Test storage functionality
        print(f"\n💾 Testing storage functionality...")

        # JSON Storage
        json_storage = StorageFactory.create_storage(
            "json",
            base_path="raw_data_output",
            include_metadata=True
        )
        json_metadata = json_storage.save(stock_data, "AAPL", "daily")
        print(f"✅ JSON saved: {json_metadata.file_path}")
        print(f"   Records: {json_metadata.record_count}")
        print(f"   File size: {Path(json_metadata.file_path).stat().st_size / 1024:.1f} KB")

        # Parquet Storage
        parquet_storage = StorageFactory.create_storage(
            "parquet",
            base_path="raw_data_output",
            include_metadata=True
        )
        parquet_metadata = parquet_storage.save(stock_data, "AAPL", "daily")
        print(f"✅ Parquet saved: {parquet_metadata.file_path}")
        print(f"   Records: {parquet_metadata.record_count}")
        print(f"   File size: {Path(parquet_metadata.file_path).stat().st_size / 1024:.1f} KB")

        # Test loading
        print(f"\n🔄 Testing data loading...")
        loaded_json = json_storage.load(json_metadata.file_path)
        loaded_parquet = parquet_storage.load(parquet_metadata.file_path)

        print(f"✅ JSON loaded: {len(loaded_json)} records")
        print(f"✅ Parquet loaded: {len(loaded_parquet)} records")

        # Compare data integrity
        print(f"\n🔍 Data integrity check:")
        print(f"   Original records: {len(stock_data)}")
        print(f"   JSON records: {len(loaded_json)}")
        print(f"   Parquet records: {len(loaded_parquet)}")
        print(f"   JSON columns match: {list(stock_data.columns) == list(loaded_json.columns)}")
        print(f"   Parquet columns match: {list(stock_data.columns) == list(loaded_parquet.columns)}")

        # Show file organization
        print(f"\n📁 File organization:")
        base_path = Path("raw_data_output")
        if base_path.exists():
            for file_path in base_path.rglob("*"):
                if file_path.is_file():
                    size_kb = file_path.stat().st_size / 1024
                    print(f"   {file_path.relative_to(base_path)} ({size_kb:.1f} KB)")
       
        print(f"\n📊 API Usage Summary:")
        print(f"   API calls made: {api_calls_made}")
        print(f"   Calls remaining (est.): {25 - api_calls_made} (daily limit: 25)")

    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"   Type: {type(e).__name__}")
        import traceback
        traceback.print_exc()


def examine_forex_data():
    """Fetch and examine forex data (if rate limits allow)."""

    api_key = config.ALPHA_VANTAGE_API_KEY
    if not api_key or api_key == "your_api_key_here":
        return

    client = AlphaVantageClient(api_key)

    print(f"\n💱 Fetching EUR/USD exchange rate... (additional API call)")
    success, result = safe_api_call(client.get_currency_exchange_rate, "EUR", "USD")
   
    if not success:
        print(f"❌ Forex rate error: {result}")
        return
       
    fx_rate = result
   
    # Check if response indicates rate limiting
    is_limited, msg = check_rate_limit_response(fx_rate)
    if is_limited:
        print(f"⚠️ Rate limit detected: {msg}")
        print("   Skipping additional forex API calls to preserve quota.")
        return
   
    print(f"✅ Current EUR/USD rate: {fx_rate.get('5. Exchange Rate', 'N/A')}")

    # Only fetch historical data if we haven't hit limits
    print(f"\n📈 Fetching EUR/USD daily forex data... (additional API call)")
    success, result = safe_api_call(client.get_forex_daily, "EUR", "USD")
   
    if not success:
        print(f"❌ Forex historical data error: {result}")
        return
       
    fx_data = result
    print(f"✅ Retrieved {len(fx_data)} forex records")
    print(f"📅 Date range: {fx_data['Date'].min()} to {fx_data['Date'].max()}")
    print(f"📊 Columns: {list(fx_data.columns)}")

    print(f"\n🔍 Forex data sample (last 3 rows):")
    print(fx_data.tail(3).to_string(index=False))


def examine_crypto_data():
    """Fetch and examine crypto data (if rate limits allow)."""

    api_key = config.ALPHA_VANTAGE_API_KEY
    if not api_key or api_key == "your_api_key_here":
        return

    client = AlphaVantageClient(api_key)

    print(f"\n₿ Fetching BTC/USD exchange rate... (additional API call)")
    success, result = safe_api_call(client.get_currency_exchange_rate, "BTC", "USD")
   
    if not success:
        print(f"❌ Crypto rate error: {result}")
        return
       
    btc_rate = result
   
    # Check if response indicates rate limiting
    is_limited, msg = check_rate_limit_response(btc_rate)
    if is_limited:
        print(f"⚠️ Rate limit detected: {msg}")
        print("   Skipping additional crypto API calls to preserve quota.")
        return
   
    print(f"✅ Current BTC/USD rate: ${float(btc_rate.get('5. Exchange Rate', 0)):,.2f}")

    # Only fetch historical data if we haven't hit limits
    print(f"\n📈 Fetching BTC/USD daily crypto data... (additional API call)")
    success, result = safe_api_call(client.get_digital_currency_daily, "BTC", "USD")
   
    if not success:
        print(f"❌ Crypto historical data error: {result}")
        return
       
    crypto_data = result
    print(f"✅ Retrieved {len(crypto_data)} crypto records")
    print(f"📅 Date range: {crypto_data['Date'].min()} to {crypto_data['Date'].max()}")
    print(f"📊 Columns: {list(crypto_data.columns)}")

    print(f"\n🔍 Crypto data sample (last 3 rows):")
    print(crypto_data.tail(3).to_string(index=False))


if __name__ == "__main__":
    print("🚀 Alpha Vantage Data Examination Tool")
    print("=" * 50)
    print("⚠️  Rate Limit Aware: Limited to 3 API calls to preserve daily quota")
    print("   (Alpha Vantage free tier: 25 requests/day)")
    print()

    # Check API key first
    if not config.ALPHA_VANTAGE_API_KEY or config.ALPHA_VANTAGE_API_KEY == "your_api_key_here":
        print("❌ No API key found!")
        print("To examine real data, set your Alpha Vantage API key:")
        print("export ALPHA_VANTAGE_API_KEY='your_key_here'")
        print("\nGet a free key at: https://www.alphavantage.co/support/#api-key")
        exit(1)

    # Main stock data examination (1 API call)
    examine_api_data()

    # Additional data types (only if user wants to use more API calls)
    print(f"\n" + "="*50)
    print("📊 Additional Data Types Available:")
    print("   - Forex data (EUR/USD rates + historical)")
    print("   - Crypto data (BTC/USD rates + historical)")
    print("   - These require additional API calls")
    print()
   
    user_choice = input("Fetch additional data? (y/N): ").lower().strip()
   
    if user_choice in ['y', 'yes']:
        print("\n🔄 Fetching additional data (will use more API quota)...")
        examine_forex_data()
        examine_crypto_data()
    else:
        print("\n⏭️  Skipping additional data to preserve API quota")

    print(f"\n✅ Data examination complete!")
    print(f"📁 Check the 'raw_data_output' directory for saved files")
    print(f"💡 Tip: Use saved data files to avoid repeated API calls")
