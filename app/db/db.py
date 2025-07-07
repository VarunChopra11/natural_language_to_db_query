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
            # Existing tables
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
            print("'client_users' table checked/created.")
            
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
            print("'api_keys' table checked/created.")
            
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS end_users (
                    id SERIAL PRIMARY KEY,
                    client_id INTEGER NOT NULL REFERENCES client_users(id),
                    wallet_address VARCHAR(100) NOT NULL UNIQUE,
                    email VARCHAR(100),
                    created_at TIMESTAMP NOT NULL DEFAULT NOW()
                )
            """)
            print("'end_users' table checked/created.")
            
            # New financial tables
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS financial_portfolios (
                    id SERIAL PRIMARY KEY,
                    wallet_address TEXT NOT NULL UNIQUE,
                    total_balance_usd NUMERIC NOT NULL,
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
            """)
            print("'financial_portfolios' table checked/created.")
            
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS token_balances (
                    id SERIAL PRIMARY KEY,
                    wallet_address TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    token_address TEXT NOT NULL,
                    balance NUMERIC NOT NULL,
                    balance_usd NUMERIC NOT NULL,
                    price NUMERIC NOT NULL,
                    network TEXT NOT NULL,
                    img_url TEXT,
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    UNIQUE (wallet_address, token_address)
                )
            """)
            print("'token_balances' table checked/created.")
            
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS app_balances (
                    id SERIAL PRIMARY KEY,
                    wallet_address TEXT NOT NULL,
                    meta_type TEXT NOT NULL,
                    position_count INTEGER NOT NULL,
                    balance_usd NUMERIC NOT NULL,
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    UNIQUE (wallet_address, meta_type)
                )
            """)
            print("'app_balances' table checked/created.")
            
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS nft_assets (
                    id SERIAL PRIMARY KEY,
                    wallet_address TEXT NOT NULL,
                    token_id TEXT NOT NULL,
                    collection_address TEXT NOT NULL,
                    name TEXT,
                    estimated_value NUMERIC,
                    img_url TEXT,
                    network TEXT NOT NULL,
                    last_updated TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    UNIQUE (wallet_address, token_id, collection_address)
                )
            """)
            print("'nft_assets' table checked/created.")
            
            # Transaction history table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS transaction_history (
                    id SERIAL PRIMARY KEY,
                    wallet_address TEXT NOT NULL,
                    tx_hash TEXT NOT NULL UNIQUE,
                    block_number INTEGER NOT NULL,
                    timestamp TIMESTAMPTZ NOT NULL,
                    from_address TEXT NOT NULL,
                    to_address TEXT,
                    network TEXT NOT NULL,
                    method_signature TEXT,
                    method_sighash TEXT,
                    processed_description TEXT,
                    description TEXT,
                    value_usd NUMERIC,
                    value_eth NUMERIC,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
            """)
            print("'transaction_history' table checked/created.")
            
            # Create indexes for performance
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_end_users_wallet ON end_users(wallet_address);
            """)
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_token_balances_wallet ON token_balances(wallet_address);
            """)
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_app_balances_wallet ON app_balances(wallet_address);
            """)
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_nft_assets_wallet ON nft_assets(wallet_address);
            """)
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_tx_history_wallet ON transaction_history(wallet_address);
            """)
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_tx_history_timestamp ON transaction_history(timestamp DESC);
            """)
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_tx_history_hash ON transaction_history(tx_hash);
            """)
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_token_balances_network ON token_balances(network);
            """)
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_nft_assets_collection ON nft_assets(collection_address);
            """)
            print("All indexes created.")

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