"""FastAPI main application with SQL-powered endpoints."""

from fastapi import FastAPI, Depends, HTTPException, Query
from typing import List, Optional
import asyncpg
from .database import get_database_connection
from .models import (
    StockPerformance,
    StockSummary,
    CurrencyConversion,
    DailySummary
)
from .dependencies import get_sql_query

app = FastAPI(
    title="NYSE Stock Analytics API",
    description="SQL-first API for Magnificent Seven stock analysis",
    version="1.0.0"
)

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "nyse-stock-api"}

@app.get("/api/top-performers", response_model=List[StockPerformance])
async def get_top_performers(
    limit: int = Query(5, ge=1, le=10),
    db: asyncpg.Connection = Depends(get_database_connection)
):
    """Get top performing stocks by daily return."""
    try:
        query = get_sql_query("top_performers.sql")
        rows = await db.fetch(query)
        
        return [
            StockPerformance(
                symbol=row["symbol"],
                company_name=row["company_name"],
                price_usd=float(row["price_usd"]),
                price_gbp=float(row["price_gbp"]) if row["price_gbp"] else None,
                daily_return=float(row["daily_return"]) if row["daily_return"] else None,
                volume=int(row["volume"]),
                trade_date=row["trade_date"],
                performance_rank=int(row["performance_rank"])
            )
            for row in rows[:limit]
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/api/stocks/price-range", response_model=List[StockPerformance])
async def get_stocks_by_price_range(
    min_price: float = Query(..., ge=0),
    max_price: float = Query(..., ge=0),
    db: asyncpg.Connection = Depends(get_database_connection)
):
    """Get stocks within specified price range."""
    if min_price > max_price:
        raise HTTPException(status_code=400, detail="min_price must be less than max_price")
    
    try:
        query = get_sql_query("price_ranges.sql")
        rows = await db.fetch(query, min_price, max_price)
        
        return [
            StockPerformance(
                symbol=row["symbol"],
                company_name=row["company_name"],
                price_usd=float(row["price_usd"]),
                price_gbp=float(row["price_gbp"]) if row["price_gbp"] else None,
                daily_return=float(row["daily_return"]) if row["daily_return"] else None,
                volume=int(row["volume"]),
                trade_date=row["trade_date"]
            )
            for row in rows
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/api/currency/convert", response_model=List[CurrencyConversion])
async def get_currency_conversion(
    symbol: Optional[str] = Query(None),
    db: asyncpg.Connection = Depends(get_database_connection)
):
    """Get USD to GBP price conversion for stocks."""
    try:
        query = get_sql_query("currency_conversion.sql")
        rows = await db.fetch(query, symbol)
        
        return [
            CurrencyConversion(
                symbol=row["symbol"],
                company_name=row["company_name"],
                price_usd=float(row["price_usd"]),
                usd_to_gbp_rate=float(row["usd_to_gbp_rate"]),
                price_gbp=float(row["price_gbp"]),
                rate_date=row["rate_date"]
            )
            for row in rows
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/api/summary", response_model=List[DailySummary])
async def get_daily_summary(
    days: int = Query(7, ge=1, le=30),
    db: asyncpg.Connection = Depends(get_database_connection)
):
    """Get daily summary statistics for stocks."""
    try:
        query = get_sql_query("stock_summary.sql")
        rows = await db.fetch(query)
        
        return [
            DailySummary(
                summary_date=row["summary_date"],
                stocks_count=int(row["stocks_count"]),
                avg_closing_price_usd=float(row["avg_closing_price_usd"]),
                min_closing_price_usd=float(row["min_closing_price_usd"]),
                max_closing_price_usd=float(row["max_closing_price_usd"]),
                avg_daily_return_pct=float(row["avg_daily_return_pct"]) if row["avg_daily_return_pct"] else None,
                min_daily_return_pct=float(row["min_daily_return_pct"]) if row["min_daily_return_pct"] else None,
                max_daily_return_pct=float(row["max_daily_return_pct"]) if row["max_daily_return_pct"] else None,
                total_volume=int(row["total_volume"]),
                avg_volume=int(row["avg_volume"]),
                avg_closing_price_gbp=float(row["avg_closing_price_gbp"]) if row["avg_closing_price_gbp"] else None,
                usd_to_gbp_rate=float(row["usd_to_gbp_rate"]) if row["usd_to_gbp_rate"] else None
            )
            for row in rows[:days]
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
