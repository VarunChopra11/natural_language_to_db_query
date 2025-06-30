from app.db.db import get_connection
from fastapi import HTTPException

async def get_transactions_per_hour(range: str):
    interval_map = {
        "7d": "7 DAY",
        "1m": "1 MONTH",
        "1y": "1 YEAR"
    }
    if range not in interval_map:
        raise HTTPException(status_code=400, detail="Invalid range parameter. Use '7d', '1m', or '1y'")

    query = f"""
        SELECT 
            DATE_TRUNC('hour', blocks.timestamp) AS hour,
            COUNT(transactions.hash) AS transaction_count
        FROM blocks
        JOIN transactions ON blocks.number = transactions.block_number
        WHERE blocks.timestamp >= NOW() - INTERVAL '{interval_map[range]}'
        GROUP BY hour
        ORDER BY hour;
    """
    pool = await get_connection()
    async with pool.acquire() as conn:
        result = await conn.fetch(query)
    return [{"hour": r["hour"], "transaction_count": r["transaction_count"]} for r in result]

async def get_top_miners():
    query = """
        SELECT 
            miner AS miner_address,
            COUNT(*) AS block_count
        FROM blocks
        GROUP BY miner
        ORDER BY block_count DESC
        LIMIT 10;
    """
    
    pool = await get_connection()
    async with pool.acquire() as conn:
        result = await conn.fetch(query)
    return [{"miner_address": r["miner_address"], "block_count": r["block_count"]} for r in result]

async def get_average_gas_used(days: int = 7):
    query = f"""
        SELECT 
            DATE_TRUNC('hour', timestamp) AS hour,
            AVG(gas_used) AS average_gas_used
        FROM blocks
        WHERE timestamp >= NOW() - INTERVAL '{days} DAYS'
        GROUP BY hour
        ORDER BY hour;
    """
    
    pool = await get_connection()
    async with pool.acquire() as conn:
        result = await conn.fetch(query)
    return [{"hour": r["hour"], "average_gas_used": float(r["average_gas_used"])} for r in result]

async def get_top_withdrawal_addresses():
    query = """
        SELECT 
            address,
            SUM(amount) AS total_amount
        FROM withdrawals
        GROUP BY address
        ORDER BY total_amount DESC
        LIMIT 10;
    """
    
    pool = await get_connection()
    async with pool.acquire() as conn:
        result = await conn.fetch(query)
    return [{"address": r["address"], "total_amount": float(r["total_amount"])} for r in result]