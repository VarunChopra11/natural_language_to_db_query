-- Blocks table
CREATE TABLE IF NOT EXISTS blocks (
    number BIGINT PRIMARY KEY,
    hash VARCHAR(66) UNIQUE NOT NULL,
    parent_hash VARCHAR(66) NOT NULL,
    base_fee_per_gas NUMERIC,
    blob_gas_used NUMERIC,
    difficulty NUMERIC,
    excess_blob_gas NUMERIC,
    extra_data TEXT,
    gas_limit NUMERIC,
    gas_used NUMERIC,
    logs_bloom TEXT,
    miner VARCHAR(42),
    mix_hash VARCHAR(66),
    nonce VARCHAR(18),
    parent_beacon_block_root VARCHAR(66),
    receipts_root VARCHAR(66),
    sha3_uncles VARCHAR(66),
    size NUMERIC,
    state_root VARCHAR(66),
    timestamp TIMESTAMP WITH TIME ZONE,
    transactions_root VARCHAR(66),
    withdrawals_root VARCHAR(66)
);

-- Indexes for blocks
CREATE INDEX ON blocks (timestamp);
CREATE INDEX ON blocks (miner);
CREATE INDEX ON blocks (parent_hash);

-- Transactions table
CREATE TABLE IF NOT EXISTS transactions (
    hash VARCHAR(66) PRIMARY KEY,
    block_number BIGINT REFERENCES blocks(number),
    chain_id INTEGER,
    from_address VARCHAR(42),
    to_address VARCHAR(42),
    gas NUMERIC,
    gas_price NUMERIC,
    input TEXT,
    max_fee_per_gas NUMERIC,
    max_priority_fee_per_gas NUMERIC,
    nonce NUMERIC,
    r VARCHAR(66),
    s VARCHAR(66),
    transaction_index INTEGER,
    type INTEGER,
    v INTEGER,
    value NUMERIC
);

-- Indexes for transactions
CREATE INDEX ON transactions (block_number);
CREATE INDEX ON transactions (from_address);
CREATE INDEX ON transactions (to_address);
CREATE INDEX ON transactions (gas_price);
CREATE INDEX ON transactions (type);

-- Access List table
CREATE TABLE IF NOT EXISTS access_list (
    transaction_hash VARCHAR(66) REFERENCES transactions(hash),
    address VARCHAR(42),
    storage_keys JSONB,
    PRIMARY KEY (transaction_hash, address)
);

-- Index for access_list
CREATE INDEX ON access_list (address);

-- Withdrawals table
CREATE TABLE IF NOT EXISTS withdrawals (
    block_number BIGINT REFERENCES blocks(number),
    index BIGINT,
    validator_index INTEGER,
    address VARCHAR(42),
    amount NUMERIC,
    PRIMARY KEY (block_number, index)
);

-- Indexes for withdrawals
CREATE INDEX ON withdrawals (validator_index);
CREATE INDEX ON withdrawals (address);