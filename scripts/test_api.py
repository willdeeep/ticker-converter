#!/usr/bin/env python3
"""Test script for the Magnificent Seven Stock Performance API endpoints."""

import asyncio
import os
import sys

import httpx

# Add the project root to the path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)


async def test_health_endpoint(client: httpx.AsyncClient) -> bool:
    """Test the health check endpoint."""
    try:
        response = await client.get("/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check passed: {data}")
            return True

        print(f"❌ Health check failed: {response.status_code}")
        return False
    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"❌ Health check error: {e}")
        return False


async def test_top_performers_endpoint(client: httpx.AsyncClient) -> bool:
    """Test the top performers endpoint."""
    try:
        response = await client.get("/api/stocks/top-performers")
        if response.status_code == 200:
            data = response.json()
            print("✅ Top performers endpoint works")
            print(f"   Returned {len(data)} stocks")
            if data:
                print(f"   Top performer: {data[0]['symbol']} - {data[0]['company_name']}")
                print(f"   Daily return: {data[0]['daily_return']}%")
            return True
        if response.status_code == 404:
            print("⚠️  Top performers endpoint: No data available (404)")
            return True  # This is acceptable if no data exists yet

        print(f"❌ Top performers endpoint failed: {response.status_code}")
        print(f"   Response: {response.text}")
        return False
    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"❌ Top performers endpoint error: {e}")
        return False


async def test_performance_details_endpoint(client: httpx.AsyncClient) -> bool:
    """Test the performance details endpoint."""
    try:
        response = await client.get("/api/stocks/performance-details")
        if response.status_code == 200:
            data = response.json()
            print("✅ Performance details endpoint works")
            print(f"   Returned {len(data)} stocks with detailed metrics")
            if data:
                stock = data[0]
                print(f"   Sample: {stock['symbol']} - {stock['company_name']}")
                print(f"   Price USD: ${stock['price_usd']}")
                if stock.get('price_gbp'):
                    print(f"   Price GBP: £{stock['price_gbp']}")
            return True
        if response.status_code == 404:
            print("⚠️  Performance details endpoint: No data available (404)")
            return True  # This is acceptable if no data exists yet

        print(f"❌ Performance details endpoint failed: {response.status_code}")
        print(f"   Response: {response.text}")
        return False
    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"❌ Performance details endpoint error: {e}")
        return False


async def main():
    """Run all API tests."""
    base_url = os.getenv("API_BASE_URL", "http://localhost:8000")

    print(f"Testing Magnificent Seven Stock Performance API at {base_url}")
    print("=" * 60)

    async with httpx.AsyncClient(base_url=base_url, timeout=30.0) as client:
        # Test health endpoint
        health_ok = await test_health_endpoint(client)

        if not health_ok:
            print("\n❌ Health check failed. Ensure the API server is running.")
            print("   Start the server with: python run_api.py")
            return

        print()

        # Test main endpoints
        top_performers_ok = await test_top_performers_endpoint(client)
        print()

        performance_details_ok = await test_performance_details_endpoint(client)
        print()

        # Summary
        print("=" * 60)
        if health_ok and top_performers_ok and performance_details_ok:
            print("🎉 All API tests passed!")
            print("\nEndpoints available:")
            print(f"   - Health: {base_url}/health")
            print(f"   - Top Performers: {base_url}/api/stocks/top-performers")
            print(f"   - Performance Details: {base_url}/api/stocks/performance-details")
            print(f"   - API Docs: {base_url}/docs")
        else:
            print("❌ Some tests failed. Check the output above.")


if __name__ == "__main__":
    asyncio.run(main())
