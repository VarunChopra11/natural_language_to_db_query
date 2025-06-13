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
        await create_tables()
    return _db_pool

async def create_tables():
    async with _db_pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS client_users (
                    id SERIAL PRIMARY KEY,
                    company_name VARCHAR(100) NOT NULL UNIQUE,
                    email VARCHAR(100) NOT NULL UNIQUE,
                    is_verified BOOLEAN NOT NULL DEFAULT FALSE,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMP
                )
            """)
            print(" 'client_users' table checked/created.")
            
            # Create api_keys table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS api_keys (
                    id SERIAL PRIMARY KEY,
                    api_key_id VARCHAR(100) NOT NULL UNIQUE,
                    client_id INTEGER NOT NULL REFERENCES client_users(id) ON DELETE CASCADE,
                    api_key_hash VARCHAR(100) NOT NULL UNIQUE,
                    is_active BOOLEAN NOT NULL DEFAULT TRUE,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMP,
                    last_used_at TIMESTAMP
                )
            """)
            print(" 'api_keys' table checked/created.")
            
            # Create indexes for api_keys table for better performance
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_api_keys_client_id ON api_keys(client_id);
            """)
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_api_keys_hash ON api_keys(api_key_hash);
            """)
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_api_keys_active ON api_keys(is_active);
            """)
            print(" API keys indexes checked/created.")
            
            # Create end_users table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS end_users (
                    id SERIAL PRIMARY KEY,
                    client_id INTEGER NOT NULL REFERENCES client_users(id),
                    wallet_address VARCHAR(100) NOT NULL UNIQUE,
                    email VARCHAR(100),
                    created_at TIMESTAMP NOT NULL DEFAULT NOW()
                )
            """)
            print(" 'end_users' table checked/created.")

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