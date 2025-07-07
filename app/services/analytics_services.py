from app.db.db import get_connection
from fastapi import HTTPException
from datetime import datetime, timedelta

async def get_client_portfolio_summary(client_id: int):
    query = """
        SELECT 
            COALESCE(SUM(total_balance_usd), 0) AS total_balance_usd,
            COUNT(DISTINCT end_user_id) AS user_count
        FROM financial_portfolios
        WHERE client_id = $1
    """
    pool = await get_connection()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(query, client_id)
    return dict(row)

async def get_client_token_distribution(client_id: int):
    query = """
        SELECT 
            symbol,
            token_address,
            network,
            SUM(balance) AS total_balance,
            SUM(balance_usd) AS total_balance_usd,
            AVG(price) AS average_price
        FROM token_balances
        WHERE client_id = $1
        GROUP BY symbol, token_address, network
        ORDER BY total_balance_usd DESC
    """
    pool = await get_connection()
    async with pool.acquire() as conn:
        rows = await conn.fetch(query, client_id)
    return [dict(row) for row in rows]

async def get_client_app_summary(client_id: int):
    query = """
        SELECT 
            meta_type,
            SUM(position_count) AS total_position_count,
            SUM(balance_usd) AS total_balance_usd
        FROM app_balances
        WHERE client_id = $1
        GROUP BY meta_type
        ORDER BY total_balance_usd DESC
    """
    pool = await get_connection()
    async with pool.acquire() as conn:
        rows = await conn.fetch(query, client_id)
    return [dict(row) for row in rows]

async def get_client_nft_summary(client_id: int):
    query = """
        SELECT 
            collection_address,
            COUNT(*) AS nft_count,
            COALESCE(SUM(estimated_value), 0) AS total_estimated_value
        FROM nft_assets
        WHERE client_id = $1
        GROUP BY collection_address
        ORDER BY nft_count DESC
        LIMIT 20
    """
    pool = await get_connection()
    async with pool.acquire() as conn:
        rows = await conn.fetch(query, client_id)
    return [dict(row) for row in rows]

async def get_client_transaction_activity(client_id: int, range: str):
    range_map = {
        "7d": ("day", 7),
        "1m": ("day", 30),
        "1y": ("month", 12)
    }
    
    if range not in range_map:
        raise HTTPException(status_code=400, detail="Invalid range parameter")
    
    interval, num_units = range_map[range]
    end_date = datetime.utcnow()
    
    if interval == "day":
        start_date = end_date - timedelta(days=num_units)
        trunc = "day"
    else:  # month
        start_date = end_date - timedelta(days=30*num_units)
        trunc = "month"
    
    query = f"""
        SELECT 
            DATE_TRUNC('{trunc}', timestamp) AS period,
            COUNT(*) AS transaction_count,
            COUNT(DISTINCT end_user_id) AS active_users
        FROM transaction_history
        WHERE 
            client_id = $1
            AND timestamp >= $2
            AND timestamp <= $3
        GROUP BY period
        ORDER BY period
    """
    
    pool = await get_connection()
    async with pool.acquire() as conn:
        rows = await conn.fetch(query, client_id, start_date, end_date)
    
    return [
        {
            "period": row["period"],
            "transaction_count": row["transaction_count"],
            "active_users": row["active_users"]
        }
        for row in rows
    ]