"""FastAPI main application with SQL-powered endpoints."""

from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Query

from .database import DatabaseConnection
from .dependencies import get_db, get_sql_query
from .models import CurrencyConversion, DailySummary, StockPerformance

app = FastAPI(
    title="NYSE Stock Analytics API",
    description="SQL-first API for Magnificent Seven stock analysis",
    version="1.0.0",
)


def _build_stock_performance(row: dict[str, Any]) -> StockPerformance:
    """Build StockPerformance model from database row.

    Args:
        row: Database row as dictionary

    Returns:
        StockPerformance model instance
    """
    return StockPerformance(
        symbol=row["symbol"],
        company_name=row["company_name"],
        price_usd=float(row["price_usd"]),
        price_gbp=float(row["price_gbp"]) if row["price_gbp"] else None,
        daily_return=float(row["daily_return"]) if row["daily_return"] else None,
        volume=int(row["volume"]),
        trade_date=row["trade_date"],
        performance_rank=(
            int(row["performance_rank"]) if row.get("performance_rank") else None
        ),
    )


def _build_currency_conversion(row: dict[str, Any]) -> CurrencyConversion:
    """Build CurrencyConversion model from database row.

    Args:
        row: Database row as dictionary

    Returns:
        CurrencyConversion model instance
    """
    return CurrencyConversion(
        symbol=row["symbol"],
        company_name=row["company_name"],
        price_usd=float(row["price_usd"]),
        usd_to_gbp_rate=float(row["usd_to_gbp_rate"]),
        price_gbp=float(row["price_gbp"]),
        rate_date=row["rate_date"],
    )


def _build_daily_summary(row: dict[str, Any]) -> DailySummary:
    """Build DailySummary model from database row.

    Args:
        row: Database row as dictionary

    Returns:
        DailySummary model instance
    """
    return DailySummary(
        summary_date=row["summary_date"],
        stocks_count=int(row["stocks_count"]),
        avg_closing_price_usd=float(row["avg_closing_price_usd"]),
        min_closing_price_usd=float(row["min_closing_price_usd"]),
        max_closing_price_usd=float(row["max_closing_price_usd"]),
        avg_daily_return_pct=(
            float(row["avg_daily_return_pct"]) if row["avg_daily_return_pct"] else None
        ),
        min_daily_return_pct=(
            float(row["min_daily_return_pct"]) if row["min_daily_return_pct"] else None
        ),
        max_daily_return_pct=(
            float(row["max_daily_return_pct"]) if row["max_daily_return_pct"] else None
        ),
        total_volume=int(row["total_volume"]),
        avg_volume=int(row["avg_volume"]),
        avg_closing_price_gbp=(
            float(row["avg_closing_price_gbp"])
            if row["avg_closing_price_gbp"]
            else None
        ),
        usd_to_gbp_rate=(
            float(row["usd_to_gbp_rate"]) if row["usd_to_gbp_rate"] else None
        ),
    )


async def _execute_query_with_error_handling(
    db: DatabaseConnection, query: str, params: list[Any]
) -> list[dict[str, Any]]:
    """Execute database query with consistent error handling.

    Args:
        db: Database connection
        query: SQL query string
        params: Query parameters

    Returns:
        Query results

    Raises:
        HTTPException: On database errors
    """
    try:
        return await db.execute_query(query, params)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}") from e


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "nyse-stock-api"}


@app.get("/top-performers")
async def get_top_performers(
    limit: int = Query(default=10, description="Number of top performers to return"),
    db: DatabaseConnection = Depends(get_db),
):
    """Get top performing stocks by daily return."""
    query = get_sql_query("top_performers.sql")
    rows = await _execute_query_with_error_handling(db, query, [limit])

    return [_build_stock_performance(row) for row in rows[:limit]]


@app.get("/price-ranges")
async def get_price_ranges(
    min_price: float = Query(description="Minimum price in USD"),
    max_price: float = Query(description="Maximum price in USD"),
    period_days: int = Query(default=30, description="Number of days to analyze"),
    db: DatabaseConnection = Depends(get_db),
):
    """Get stocks within specified price range."""
    if min_price > max_price:
        raise HTTPException(
            status_code=400, detail="min_price must be less than max_price"
        )

    query = get_sql_query("price_ranges.sql")
    rows = await _execute_query_with_error_handling(
        db, query, [min_price, max_price, period_days]
    )

    return [_build_stock_performance(row) for row in rows]


@app.get("/currency-conversion")
async def currency_conversion(
    symbol: str = Query(description="Stock symbol"),
    from_currency: str = Query(default="USD", description="Source currency code"),
    to_currency: str = Query(default="GBP", description="Target currency code"),
    db: DatabaseConnection = Depends(get_db),
):
    """Get USD to GBP price conversion for stocks."""
    query = get_sql_query("currency_conversion.sql")
    rows = await _execute_query_with_error_handling(
        db, query, [symbol, from_currency, to_currency]
    )

    return [_build_currency_conversion(row) for row in rows]


@app.get("/stock-summary/{symbol}")
async def get_stock_summary(
    symbol: str,
    days: int = Query(default=30, description="Number of days to summarize"),
    db: DatabaseConnection = Depends(get_db),
):
    """Get daily summary statistics for stocks."""
    query = get_sql_query("stock_summary.sql")
    rows = await _execute_query_with_error_handling(db, query, [symbol, days])

    return [_build_daily_summary(row) for row in rows[:days]]


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
