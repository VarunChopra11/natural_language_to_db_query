import asyncpg
from app.config import DATABASE_URL

_db_pool = None

async def init_db_pool():
    global _db_pool
    if _db_pool is None:
        print("Initializing database connection pool...")
        _db_pool = await asyncpg.create_pool(
            dsn=DATABASE_URL,
            min_size=1,
            max_size=10,
            timeout=60,
            max_inactive_connection_lifetime=300,
        )
    return _db_pool 

async def get_connection():
    global _db_pool
    if _db_pool is None:
        await init_db_pool()
    return _db_pool

async def close_db_pool():
    global _db_pool
    if _db_pool is not None:
        await _db_pool.close()
        _db_pool = None