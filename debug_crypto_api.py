#!/usr/bin/env python3
"""Debug script to examine raw crypto API response."""

import json
from ticker_converter.api_client import AlphaVantageClient
from ticker_converter.config import config


def debug_crypto_response():
    """Examine the raw API response for crypto data."""
   
    api_key = config.ALPHA_VANTAGE_API_KEY
    if not api_key:
        print("❌ No API key found!")
        return
   
    client = AlphaVantageClient(api_key)
   
    try:
        # Make raw request to see the actual response structure
        params = {
            "function": "DIGITAL_CURRENCY_DAILY",
            "symbol": "BTC",
            "market": "USD",
        }
       
        print("🔍 Making raw API request for BTC/USD...")
        raw_data = client._make_request(params)
       
        print("📋 Top-level keys in response:")
        for key in raw_data.keys():
            print(f"   - {key}")
       
        # Check if time series exists
        time_series_key = "Time Series (Digital Currency Daily)"
        if time_series_key in raw_data:
            time_series = raw_data[time_series_key]
            print(f"\n✅ Found time series with {len(time_series)} entries")
           
            # Get the first entry to examine the structure
            first_date = list(time_series.keys())[0]
            first_entry = time_series[first_date]
           
            print(f"\n🗓️ Sample entry for {first_date}:")
            for key, value in first_entry.items():
                print(f"   {key}: {value}")

        else:
            print(f"\n❌ No time series found. Available keys:")
            print(json.dumps(raw_data, indent=2))
           
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    debug_crypto_response()
