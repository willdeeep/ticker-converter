# API Endpoints Documentation

## Overview

The ticker-converter FastAPI application provides REST endpoints for NYSE stock market data analysis with direct SQL query execution. All endpoints return JSON responses and focus on core analytical requirements.

## Base Configuration

**Base URL**: `http://localhost:8000`  
**API Version**: v1  
**Response Format**: JSON  
**Database**: Direct SQL query execution (PostgreSQL)

## Authentication

Currently implements basic API key authentication via header:
```
X-API-Key: your-api-key-here
```

## Core Endpoints

### GET /api/stocks/top-performers

Returns the top 5 performing stocks by daily return percentage.

**Query Execution**:
```sql
SELECT symbol, daily_return_pct, close_usd, date 
FROM v_top_performers 
WHERE daily_return_pct IS NOT NULL 
ORDER BY daily_return_pct DESC 
LIMIT 5;
```

**Response Model**:
```json
{
  "stocks": [
    {
      "symbol": "AAPL",
      "daily_return_pct": 3.45,
      "close_usd": 150.25,
      "date": "2025-08-11"
    }
  ],
  "count": 5,
  "generated_at": "2025-08-11T10:30:00Z"
}
```

**HTTP Status Codes**:
- `200`: Success
- `404`: No data found
- `500`: Database error

### GET /api/stocks/price-range

Returns stocks within specified USD price range.

**Parameters**:
- `min_price` (float, required): Minimum closing price in USD
- `max_price` (float, required): Maximum closing price in USD
- `date` (string, optional): Specific date (YYYY-MM-DD format)

**Example Request**:
```
GET /api/stocks/price-range?min_price=100.00&max_price=200.00&date=2025-08-11
```

**Query Execution**:
```sql
SELECT s.symbol, p.close_usd, d.date
FROM fact_stock_prices p
JOIN dim_stocks s ON p.stock_id = s.stock_id
JOIN dim_dates d ON p.date_id = d.date_id
WHERE p.close_usd BETWEEN ? AND ?
  AND (? IS NULL OR d.date = ?)
ORDER BY p.close_usd DESC;
```

**Response Model**:
```json
{
  "stocks": [
    {
      "symbol": "AAPL",
      "close_usd": 150.25,
      "date": "2025-08-11"
    }
  ],
  "filter": {
    "min_price": 100.00,
    "max_price": 200.00,
    "date": "2025-08-11"
  },
  "count": 3
}
```

### GET /api/stocks/gbp-prices

Returns stock prices converted to GBP using daily exchange rates.

**Parameters**:
- `symbols` (string, optional): Comma-separated stock symbols
- `date` (string, optional): Specific date (YYYY-MM-DD format)

**Example Request**:
```
GET /api/stocks/gbp-prices?symbols=AAPL,MSFT&date=2025-08-11
```

**Query Execution**:
```sql
SELECT symbol, close_usd, close_gbp, exchange_rate, date
FROM v_stocks_gbp
WHERE (? IS NULL OR symbol IN (?))
  AND (? IS NULL OR date = ?)
ORDER BY symbol, date DESC;
```

**Response Model**:
```json
{
  "stocks": [
    {
      "symbol": "AAPL",
      "close_usd": 150.25,
      "close_gbp": 118.45,
      "exchange_rate": 0.7883,
      "date": "2025-08-11"
    }
  ],
  "exchange_rate_date": "2025-08-11",
  "count": 2
}
```

### GET /api/stocks/summary

Returns daily summary statistics for all tracked stocks.

**Parameters**:
- `date` (string, optional): Specific date (YYYY-MM-DD format, defaults to latest)

**Query Execution**:
```sql
SELECT 
    COUNT(*) as total_stocks,
    AVG(close_usd) as avg_price_usd,
    MAX(close_usd) as max_price_usd,
    MIN(close_usd) as min_price_usd,
    SUM(volume) as total_volume,
    date
FROM fact_stock_prices p
JOIN dim_dates d ON p.date_id = d.date_id
WHERE (? IS NULL OR d.date = ?)
GROUP BY d.date
ORDER BY d.date DESC
LIMIT 1;
```

**Response Model**:
```json
{
  "summary": {
    "total_stocks": 5,
    "avg_price_usd": 145.67,
    "max_price_usd": 250.30,
    "min_price_usd": 95.45,
    "total_volume": 125000000,
    "date": "2025-08-11"
  }
}
```

## Error Handling

### Standard Error Response
```json
{
  "error": "Error description",
  "detail": "Detailed error message",
  "timestamp": "2025-08-11T10:30:00Z"
}
```

### Common Error Codes
- `400`: Bad Request (invalid parameters)
- `401`: Unauthorized (missing/invalid API key)
- `404`: Not Found (no data for specified criteria)
- `422`: Unprocessable Entity (validation error)
- `500`: Internal Server Error (database/system error)

## Rate Limiting

- **Limit**: 100 requests per minute per API key
- **Headers**: `X-RateLimit-Remaining`, `X-RateLimit-Reset`
- **Exceeded Response**: HTTP 429 with retry information

## Data Freshness

- **Stock Prices**: Updated daily after market close
- **Currency Rates**: Updated daily at 00:00 UTC
- **Cache Duration**: Responses cached for 5 minutes
- **Last Updated**: Available in response metadata

## OpenAPI Documentation

Interactive API documentation available at:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI JSON**: `http://localhost:8000/openapi.json`

## Usage Examples

### Python Client Example
```python
import requests

# Top performers
response = requests.get(
    "http://localhost:8000/api/stocks/top-performers",
    headers={"X-API-Key": "your-api-key"}
)
top_stocks = response.json()

# Price range filtering
response = requests.get(
    "http://localhost:8000/api/stocks/price-range",
    params={"min_price": 100, "max_price": 200},
    headers={"X-API-Key": "your-api-key"}
)
filtered_stocks = response.json()
```

### cURL Examples
```bash
# Top performers
curl -H "X-API-Key: your-api-key" \
     http://localhost:8000/api/stocks/top-performers

# Price range with date filter
curl -H "X-API-Key: your-api-key" \
     "http://localhost:8000/api/stocks/price-range?min_price=100&max_price=200&date=2025-08-11"

# GBP converted prices
curl -H "X-API-Key: your-api-key" \
     "http://localhost:8000/api/stocks/gbp-prices?symbols=AAPL,MSFT"
```

## Performance Considerations

- All endpoints execute optimized SQL queries with appropriate indexes
- Response caching implemented for frequently accessed data
- Database connection pooling for concurrent request handling
- Query execution time typically under 50ms for standard requests

This API design prioritizes simplicity and direct SQL execution while providing the essential analytical capabilities required for NYSE stock market data analysis.
