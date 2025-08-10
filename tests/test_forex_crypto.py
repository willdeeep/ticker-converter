"""Tests for forex and cryptocurrency functionality."""

import pandas as pd
import pytest
import responses

from ticker_converter.api_client import AlphaVantageAPIError, AlphaVantageClient


@responses.activate
def test_get_currency_exchange_rate_success():
    """Test successful currency exchange rate retrieval."""
    mock_response = {
        "Realtime Currency Exchange Rate": {
            "1. From_Currency Code": "USD",
            "2. From_Currency Name": "United States Dollar",
            "3. To_Currency Code": "EUR",
            "4. To_Currency Name": "Euro",
            "5. Exchange Rate": "0.85123400",
            "6. Last Refreshed": "2023-12-01 10:00:00",
            "7. Time Zone": "UTC",
            "8. Bid Price": "0.85120000",
            "9. Ask Price": "0.85126800",
        }
    }

    responses.add(
        responses.GET,
        "https://www.alphavantage.co/query",
        json=mock_response,
        status=200,
    )

    client = AlphaVantageClient("test_key")
    result = client.get_currency_exchange_rate("USD", "EUR")

    assert result == mock_response
    assert len(responses.calls) == 1

    # Check request parameters
    request = responses.calls[0].request
    assert "function=CURRENCY_EXCHANGE_RATE" in request.url
    assert "from_currency=USD" in request.url
    assert "to_currency=EUR" in request.url


@responses.activate
def test_get_currency_exchange_rate_crypto():
    """Test currency exchange rate for cryptocurrency."""
    mock_response = {
        "Realtime Currency Exchange Rate": {
            "1. From_Currency Code": "BTC",
            "2. From_Currency Name": "Bitcoin",
            "3. To_Currency Code": "USD",
            "4. To_Currency Name": "United States Dollar",
            "5. Exchange Rate": "42345.67890000",
            "6. Last Refreshed": "2023-12-01 10:00:00",
            "7. Time Zone": "UTC",
            "8. Bid Price": "42340.00000000",
            "9. Ask Price": "42350.00000000",
        }
    }

    responses.add(
        responses.GET,
        "https://www.alphavantage.co/query",
        json=mock_response,
        status=200,
    )

    client = AlphaVantageClient("test_key")
    result = client.get_currency_exchange_rate("BTC", "USD")

    assert result == mock_response


@responses.activate
def test_get_forex_daily_success():
    """Test successful forex daily data retrieval."""
    mock_response = {
        "Meta Data": {
            "1. Information": "Forex Daily Prices (open, high, low, close)",
            "2. From Symbol": "EUR",
            "3. To Symbol": "USD",
            "4. Output Size": "Compact",
            "5. Last Refreshed": "2023-12-01 21:00:00",
            "6. Time Zone": "UTC",
        },
        "Time Series FX (Daily)": {
            "2023-12-01": {
                "1. open": "1.0850",
                "2. high": "1.0890",
                "3. low": "1.0840",
                "4. close": "1.0875",
            },
            "2023-11-30": {
                "1. open": "1.0820",
                "2. high": "1.0860",
                "3. low": "1.0810",
                "4. close": "1.0850",
            },
        },
    }

    responses.add(
        responses.GET,
        "https://www.alphavantage.co/query",
        json=mock_response,
        status=200,
    )

    client = AlphaVantageClient("test_key")
    result = client.get_forex_daily("EUR", "USD")

    assert isinstance(result, pd.DataFrame)
    assert len(result) == 2
    assert list(result.columns) == [
        "Date",
        "Open",
        "High",
        "Low",
        "Close",
        "From_Symbol",
        "To_Symbol",
    ]

    # Check data ordering (should be chronological)
    assert result.iloc[0]["Date"] == pd.to_datetime("2023-11-30")
    assert result.iloc[1]["Date"] == pd.to_datetime("2023-12-01")

    # Check specific values
    assert result.iloc[1]["Open"] == 1.0850
    assert result.iloc[1]["High"] == 1.0890
    assert result.iloc[1]["Low"] == 1.0840
    assert result.iloc[1]["Close"] == 1.0875
    assert result.iloc[1]["From_Symbol"] == "EUR"
    assert result.iloc[1]["To_Symbol"] == "USD"


@responses.activate
def test_get_forex_daily_full_output():
    """Test forex daily data with full output size."""
    mock_response = {
        "Meta Data": {
            "1. Information": "Forex Daily Prices (open, high, low, close)",
            "2. From Symbol": "GBP",
            "3. To Symbol": "JPY",
            "4. Output Size": "Full",
            "5. Last Refreshed": "2023-12-01 21:00:00",
            "6. Time Zone": "UTC",
        },
        "Time Series FX (Daily)": {
            "2023-12-01": {
                "1. open": "181.50",
                "2. high": "182.00",
                "3. low": "181.00",
                "4. close": "181.75",
            }
        },
    }

    responses.add(
        responses.GET,
        "https://www.alphavantage.co/query",
        json=mock_response,
        status=200,
    )

    client = AlphaVantageClient("test_key")
    result = client.get_forex_daily("GBP", "JPY", outputsize="full")

    assert isinstance(result, pd.DataFrame)
    assert len(result) == 1

    # Check request parameters
    request = responses.calls[0].request
    assert "outputsize=full" in request.url


@responses.activate
def test_get_forex_daily_invalid_response():
    """Test forex daily data with invalid response format."""
    mock_response = {
        "Error Message": "Invalid API call. Please retry or visit the documentation."
    }

    responses.add(
        responses.GET,
        "https://www.alphavantage.co/query",
        json=mock_response,
        status=200,
    )

    client = AlphaVantageClient("test_key")

    with pytest.raises(AlphaVantageAPIError, match="API Error: Invalid API call"):
        client.get_forex_daily("INVALID", "USD")


@responses.activate
def test_get_digital_currency_daily_success():
    """Test successful digital currency daily data retrieval."""
    mock_response = {
        "Meta Data": {
            "1. Information": "Digital Currency Daily Prices",
            "2. Digital Currency Code": "BTC",
            "3. Digital Currency Name": "Bitcoin",
            "4. Market Code": "USD",
            "5. Market Name": "United States Dollar",
            "6. Last Refreshed": "2023-12-01 00:00:00",
            "7. Time Zone": "UTC",
        },
        "Time Series (Digital Currency Daily)": {
            "2023-12-01": {
                "1a. open (USD)": "42000.00000000",
                "1b. open (USD)": "42000.00000000",
                "2a. high (USD)": "42500.00000000",
                "2b. high (USD)": "42500.00000000",
                "3a. low (USD)": "41800.00000000",
                "3b. low (USD)": "41800.00000000",
                "4a. close (USD)": "42300.00000000",
                "4b. close (USD)": "42300.00000000",
                "5. volume": "12345.67890000",
                "6. market cap (USD)": "827000000000.00000000",
            },
            "2023-11-30": {
                "1a. open (USD)": "41500.00000000",
                "1b. open (USD)": "41500.00000000",
                "2a. high (USD)": "42100.00000000",
                "2b. high (USD)": "42100.00000000",
                "3a. low (USD)": "41400.00000000",
                "3b. low (USD)": "41400.00000000",
                "4a. close (USD)": "42000.00000000",
                "4b. close (USD)": "42000.00000000",
                "5. volume": "15678.90123000",
                "6. market cap (USD)": "821000000000.00000000",
            },
        },
    }

    responses.add(
        responses.GET,
        "https://www.alphavantage.co/query",
        json=mock_response,
        status=200,
    )

    client = AlphaVantageClient("test_key")
    result = client.get_digital_currency_daily("BTC", "USD")

    assert isinstance(result, pd.DataFrame)
    assert len(result) == 2
    assert list(result.columns) == [
        "Date",
        "Open_Market",
        "High_Market",
        "Low_Market",
        "Close_Market",
        "Open_USD",
        "High_USD",
        "Low_USD",
        "Close_USD",
        "Volume",
        "Market_Cap_USD",
        "Symbol",
        "Market",
    ]

    # Check data ordering (should be chronological)
    assert result.iloc[0]["Date"] == pd.to_datetime("2023-11-30")
    assert result.iloc[1]["Date"] == pd.to_datetime("2023-12-01")

    # Check specific values for latest date
    latest = result.iloc[1]
    assert latest["Open_Market"] == 42000.0
    assert latest["High_Market"] == 42500.0
    assert latest["Low_Market"] == 41800.0
    assert latest["Close_Market"] == 42300.0
    assert latest["Open_USD"] == 42000.0
    assert latest["High_USD"] == 42500.0
    assert latest["Low_USD"] == 41800.0
    assert latest["Close_USD"] == 42300.0
    assert latest["Volume"] == 12345.67890000
    assert latest["Market_Cap_USD"] == 827000000000.0
    assert latest["Symbol"] == "BTC"
    assert latest["Market"] == "USD"


@responses.activate
def test_get_digital_currency_daily_eur_market():
    """Test digital currency daily data with EUR market."""
    mock_response = {
        "Meta Data": {
            "1. Information": "Digital Currency Daily Prices",
            "2. Digital Currency Code": "ETH",
            "3. Digital Currency Name": "Ethereum",
            "4. Market Code": "EUR",
            "5. Market Name": "Euro",
            "6. Last Refreshed": "2023-12-01 00:00:00",
            "7. Time Zone": "UTC",
        },
        "Time Series (Digital Currency Daily)": {
            "2023-12-01": {
                "1a. open (EUR)": "1900.00000000",
                "1b. open (USD)": "2090.00000000",
                "2a. high (EUR)": "1950.00000000",
                "2b. high (USD)": "2145.00000000",
                "3a. low (EUR)": "1880.00000000",
                "3b. low (USD)": "2068.00000000",
                "4a. close (EUR)": "1925.00000000",
                "4b. close (USD)": "2117.50000000",
                "5. volume": "45678.90123000",
                "6. market cap (USD)": "254000000000.00000000",
            }
        },
    }

    responses.add(
        responses.GET,
        "https://www.alphavantage.co/query",
        json=mock_response,
        status=200,
    )

    client = AlphaVantageClient("test_key")
    result = client.get_digital_currency_daily("ETH", "EUR")

    assert isinstance(result, pd.DataFrame)
    assert len(result) == 1

    # Check EUR market values
    row = result.iloc[0]
    assert row["Open_Market"] == 1900.0
    assert row["High_Market"] == 1950.0
    assert row["Low_Market"] == 1880.0
    assert row["Close_Market"] == 1925.0
    assert row["Symbol"] == "ETH"
    assert row["Market"] == "EUR"

    # USD values should still be available
    assert row["Open_USD"] == 2090.0
    assert row["High_USD"] == 2145.0
    assert row["Low_USD"] == 2068.0
    assert row["Close_USD"] == 2117.5


@responses.activate
def test_get_digital_currency_daily_invalid_response():
    """Test digital currency daily data with invalid response format."""
    mock_response = {
        "Note": "Thank you for using Alpha Vantage! Our standard API call frequency is 5 calls per minute."
    }

    responses.add(
        responses.GET,
        "https://www.alphavantage.co/query",
        json=mock_response,
        status=200,
    )

    client = AlphaVantageClient("test_key")

    with pytest.raises(AlphaVantageAPIError, match="Rate limit exceeded"):
        client.get_digital_currency_daily("INVALID", "USD")


@responses.activate
def test_forex_and_crypto_integration():
    """Test that forex and crypto methods work well together."""
    # Test currency exchange rate first
    exchange_response = {
        "Realtime Currency Exchange Rate": {
            "1. From_Currency Code": "USD",
            "2. From_Currency Name": "United States Dollar",
            "3. To_Currency Code": "EUR",
            "4. To_Currency Name": "Euro",
            "5. Exchange Rate": "0.85000000",
            "6. Last Refreshed": "2023-12-01 10:00:00",
            "7. Time Zone": "UTC",
            "8. Bid Price": "0.84995000",
            "9. Ask Price": "0.85005000",
        }
    }

    responses.add(
        responses.GET,
        "https://www.alphavantage.co/query",
        json=exchange_response,
        status=200,
    )

    client = AlphaVantageClient("test_key")

    # Get exchange rate
    exchange_data = client.get_currency_exchange_rate("USD", "EUR")
    exchange_rate = float(
        exchange_data["Realtime Currency Exchange Rate"]["5. Exchange Rate"]
    )

    assert exchange_rate == 0.85
    assert len(responses.calls) == 1
