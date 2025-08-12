"""FastAPI main application with SQL-powered endpoints for Magnificent Seven stocks."""

from typing import Any

from fastapi import Depends, FastAPI, HTTPException

from .database import DatabaseConnection
from .dependencies import get_db, get_sql_query
from .models import StockPerformanceDetails, TopPerformerStock

app = FastAPI(
    title="Magnificent Seven Stock Performance API",
    description="SQL-first API for Magnificent Seven stock analysis with USD/GBP currency conversion",
    version="1.0.0",
)

# Magnificent Seven company symbols
MAGNIFICENT_SEVEN = {"AAPL", "MSFT", "AMZN", "GOOGL", "META", "NVDA", "TSLA"}


def _build_top_performer_stock(row: dict[str, Any]) -> TopPerformerStock:
    """Build TopPerformerStock model from database row.

    Args:
        row: Database row as dictionary

    Returns:
        TopPerformerStock model instance
    """
    return TopPerformerStock(
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


def _build_stock_performance_details(row: dict[str, Any]) -> StockPerformanceDetails:
    """Build StockPerformanceDetails model from database row.

    Args:
        row: Database row as dictionary

    Returns:
        StockPerformanceDetails model instance
    """
    return StockPerformanceDetails(
        symbol=row["symbol"],
        company_name=row["company_name"],
        price_usd=float(row["price_usd"]),
        price_gbp=float(row["price_gbp"]) if row["price_gbp"] else None,
        daily_return=float(row["daily_return"]) if row["daily_return"] else None,
        volume=int(row["volume"]),
        trade_date=row["trade_date"],
        avg_price_30d_usd=(
            float(row["avg_price_30d_usd"]) if row.get("avg_price_30d_usd") else None
        ),
        avg_volume_30d=(
            int(row["avg_volume_30d"]) if row.get("avg_volume_30d") else None
        ),
        price_change_30d_pct=(
            float(row["price_change_30d_pct"])
            if row.get("price_change_30d_pct")
            else None
        ),
        volatility_30d=(
            float(row["volatility_30d"]) if row.get("volatility_30d") else None
        ),
        performance_rank=(
            int(row["performance_rank"]) if row.get("performance_rank") else None
        ),
    )


async def _execute_query_with_error_handling(
    db: DatabaseConnection, query: str, params: list[Any] | None = None
) -> list[dict[str, Any]]:
    """Execute database query with consistent error handling.

    Args:
        db: Database connection
        query: SQL query string
        params: Query parameters (optional)

    Returns:
        Query results

    Raises:
        HTTPException: On database errors
    """
    try:
        return await db.execute_query(query, params or [])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}") from e


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "service": "magnificent-seven-stock-api"}


@app.get("/api/stocks/top-performers", response_model=list[TopPerformerStock])
async def get_top_performers(
    db: DatabaseConnection = Depends(get_db),
) -> list[TopPerformerStock]:
    """Get top 3 performing Magnificent Seven stocks by daily return.

    Returns the top 3 performing stocks from the Magnificent Seven companies
    (Apple, Microsoft, Amazon, Google, Meta, Nvidia, Tesla) based on their
    latest daily return percentage.

    Args:
        db: Database connection dependency

    Returns:
        List of top 3 performing stocks with USD and GBP prices

    Raises:
        HTTPException: If database query fails or no data available
    """
    query = get_sql_query("magnificent_seven_top_performers.sql")
    rows = await _execute_query_with_error_handling(db, query)

    if not rows:
        raise HTTPException(
            status_code=404,
            detail="No performance data available for Magnificent Seven stocks",
        )

    return [_build_top_performer_stock(row) for row in rows]


@app.get(
    "/api/stocks/performance-details", response_model=list[StockPerformanceDetails]
)
async def get_performance_details(
    db: DatabaseConnection = Depends(get_db),
) -> list[StockPerformanceDetails]:
    """Get detailed performance metrics for all Magnificent Seven stocks.

    Returns comprehensive performance analytics including:
    - Current prices in USD and GBP
    - Daily returns and trading volume
    - 30-day averages and price changes
    - Volatility metrics
    - Performance rankings

    Args:
        db: Database connection dependency

    Returns:
        List of detailed performance metrics for all Magnificent Seven stocks

    Raises:
        HTTPException: If database query fails or no data available
    """
    query = get_sql_query("magnificent_seven_performance_details.sql")
    rows = await _execute_query_with_error_handling(db, query)

    if not rows:
        raise HTTPException(
            status_code=404,
            detail="No detailed performance data available for Magnificent Seven stocks",
        )

    return [_build_stock_performance_details(row) for row in rows]


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
