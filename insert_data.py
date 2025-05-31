import os
import ijson
import psycopg2
from psycopg2.extras import execute_batch, Json, execute_values
from datetime import datetime
from tqdm import tqdm
from dotenv import load_dotenv
import multiprocessing
from concurrent.futures import ProcessPoolExecutor, as_completed


load_dotenv()

START_FROM = 1
BATCH_SIZE = 1000  # Number of blocks to process before committing
WORKERS = multiprocessing.cpu_count()  # Use all available cores

def convert_hex_to_numeric(value):
    """Convert hexadecimal string to numeric. If not hex, convert directly."""
    if isinstance(value, str) and value.startswith('0x'):
        return int(value, 16)
    return int(value) if value else 0

def count_blocks(filename):
    """Count total blocks in JSON file"""
    with open(filename, 'r') as f:
        return sum(1 for _ in ijson.items(f, 'item'))

def create_tables(cur):
    """Create database tables if they don't exist"""
    # Create blocks table
    cur.execute("""
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
        )
    """)
    
    # Create transactions table
    cur.execute("""
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
        )
    """)
    
    # Create access_list table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS access_list (
            transaction_hash VARCHAR(66) REFERENCES transactions(hash),
            address VARCHAR(42),
            storage_keys JSONB,
            PRIMARY KEY (transaction_hash, address)
        )
    """)
    
    # Create withdrawals table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS withdrawals (
            block_number BIGINT REFERENCES blocks(number),
            index BIGINT,
            validator_index INTEGER,
            address VARCHAR(42),
            amount NUMERIC,
            PRIMARY KEY (block_number, index)
        )
    """)

def create_indexes(cur):
    """Create necessary indexes after data insertion"""
    # Indexes for blocks table
    cur.execute("CREATE INDEX IF NOT EXISTS blocks_timestamp_idx ON blocks (timestamp)")
    cur.execute("CREATE INDEX IF NOT EXISTS blocks_miner_idx ON blocks (miner)")
    cur.execute("CREATE INDEX IF NOT EXISTS blocks_parent_hash_idx ON blocks (parent_hash)")
    
    # Indexes for transactions table
    cur.execute("CREATE INDEX IF NOT EXISTS transactions_block_number_idx ON transactions (block_number)")
    cur.execute("CREATE INDEX IF NOT EXISTS transactions_from_address_idx ON transactions (from_address)")
    cur.execute("CREATE INDEX IF NOT EXISTS transactions_to_address_idx ON transactions (to_address)")
    cur.execute("CREATE INDEX IF NOT EXISTS transactions_gas_price_idx ON transactions (gas_price)")
    cur.execute("CREATE INDEX IF NOT EXISTS transactions_type_idx ON transactions (type)")
    
    # Index for access_list table
    cur.execute("CREATE INDEX IF NOT EXISTS access_list_address_idx ON access_list (address)")
    
    # Indexes for withdrawals table
    cur.execute("CREATE INDEX IF NOT EXISTS withdrawals_validator_index_idx ON withdrawals (validator_index)")
    cur.execute("CREATE INDEX IF NOT EXISTS withdrawals_address_idx ON withdrawals (address)")

# SQL templates for batch inserts
BLOCK_INSERT = """
    INSERT INTO blocks (
        number, hash, parent_hash, base_fee_per_gas, blob_gas_used, difficulty,
        excess_blob_gas, extra_data, gas_limit, gas_used, logs_bloom, miner,
        mix_hash, nonce, parent_beacon_block_root, receipts_root, sha3_uncles,
        size, state_root, timestamp, transactions_root, withdrawals_root
    ) VALUES %s
    ON CONFLICT (number) DO NOTHING
"""

TRANSACTION_INSERT = """
    INSERT INTO transactions (
        hash, block_number, chain_id, from_address, to_address, gas, gas_price,
        input, max_fee_per_gas, max_priority_fee_per_gas, nonce, r, s,
        transaction_index, type, v, value
    ) VALUES %s
    ON CONFLICT (hash) DO NOTHING
"""

ACCESS_LIST_INSERT = """
    INSERT INTO access_list (transaction_hash, address, storage_keys)
    VALUES (%s, %s, %s)
    ON CONFLICT (transaction_hash, address) DO NOTHING
"""

WITHDRAWAL_INSERT = """
    INSERT INTO withdrawals (block_number, index, validator_index, address, amount)
    VALUES (%s, %s, %s, %s, %s)
    ON CONFLICT (block_number, index) DO NOTHING
"""

def process_block(block):
    """Process a single block and return its data components"""
    block_data = (
        int(block['number']),
        block['hash'],
        block['parentHash'],
        convert_hex_to_numeric(block.get('baseFeePerGas', '0')),
        convert_hex_to_numeric(block.get('blobGasUsed', '0')),
        convert_hex_to_numeric(block.get('difficulty', '0')),
        convert_hex_to_numeric(block.get('excessBlobGas', '0')),
        block.get('extraData', ''),
        convert_hex_to_numeric(block.get('gasLimit', '0')),
        convert_hex_to_numeric(block.get('gasUsed', '0')),
        block.get('logsBloom', ''),
        block.get('miner', ''),
        block.get('mixHash', ''),
        block.get('nonce', '0x0'),
        block.get('parentBeaconBlockRoot', None),
        block.get('receiptsRoot', ''),
        block.get('sha3Uncles', ''),
        convert_hex_to_numeric(block.get('size', '0')),
        block.get('stateRoot', ''),
        datetime.utcfromtimestamp(int(block['timestamp'])),
        block.get('transactionsRoot', ''),
        block.get('withdrawalsRoot', '')
    )

    transactions = []
    access_list = []
    withdrawals = []

    if 'transactions' in block:
        for tx in block['transactions']:
            transactions.append((
                tx['hash'],
                int(block['number']),
                convert_hex_to_numeric(tx.get('chainId', '0x1')),
                tx.get('from', ''),
                tx.get('to', None),
                convert_hex_to_numeric(tx.get('gas', '0x0')),
                convert_hex_to_numeric(tx.get('gasPrice', '0x0')),
                tx.get('input', ''),
                convert_hex_to_numeric(tx.get('maxFeePerGas', '0x0')),
                convert_hex_to_numeric(tx.get('maxPriorityFeePerGas', '0x0')),
                convert_hex_to_numeric(tx.get('nonce', '0x0')),
                tx.get('r', ''),
                tx.get('s', ''),
                int(tx['transactionIndex']),
                convert_hex_to_numeric(tx.get('type', '0x0')),
                int(tx.get('v', 0)),
                convert_hex_to_numeric(tx.get('value', '0x0'))
            ))

            if 'accessList' in tx:
                for access in tx['accessList']:
                    access_list.append((
                        tx['hash'],
                        access['address'],
                        Json(access['storageKeys'])
                    ))

    if 'withdrawals' in block:
        for wd in block['withdrawals']:
            withdrawals.append((
                int(block['number']),
                int(wd['index']),
                int(wd['validatorIndex']),
                wd['address'],
                int(wd['amount'])
            ))

    return block_data, transactions, access_list, withdrawals

def process_block_range(file_path, start_index, end_index, queue):
    """Process a range of blocks and return the collected data"""
    blocks_data = []
    transactions_data = []
    access_list_data = []
    withdrawals_data = []
    
    with open(file_path, 'r') as f:
        blocks = ijson.items(f, 'item')
        current_index = 0
        
        for block in blocks:
            current_index += 1
            if current_index < start_index:
                continue
            if current_index > end_index:
                break
                
            block_data, transactions, access_list, withdrawals = process_block(block)
            blocks_data.append(block_data)
            transactions_data.extend(transactions)
            access_list_data.extend(access_list)
            withdrawals_data.extend(withdrawals)
            
    queue.put((
        blocks_data,
        transactions_data,
        access_list_data,
        withdrawals_data
    ))

def insert_data_batch(conn, blocks_data, transactions_data, access_list_data, withdrawals_data):
    """Insert a batch of data into the database"""
    with conn.cursor() as cur:
        try:
            # Insert blocks in bulk
            if blocks_data:
                execute_values(
                    cur, BLOCK_INSERT, blocks_data, 
                    template="(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    page_size=500
                )
            
            # Insert transactions in bulk
            if transactions_data:
                execute_values(
                    cur, TRANSACTION_INSERT, transactions_data,
                    template="(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    page_size=500
                )
            
            # Insert access lists in batches
            if access_list_data:
                execute_batch(
                    cur, ACCESS_LIST_INSERT, access_list_data,
                    page_size=500
                )
            
            # Insert withdrawals in batches
            if withdrawals_data:
                execute_batch(
                    cur, WITHDRAWAL_INSERT, withdrawals_data,
                    page_size=500
                )
            
            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"Error inserting batch: {e}")
            raise

def main():
    file_path = os.getenv('JSON_FILE_PATH')
    
    print("Counting total blocks...")
    total_blocks = count_blocks(file_path)
    total_to_process = max(0, total_blocks - (START_FROM - 1))
    print(f"Found {total_blocks} blocks, processing from #{START_FROM} ({total_to_process} blocks)")
    
    # Database connection
    conn = psycopg2.connect(
        dbname=os.getenv('POSTGRESDB_NAME'),
        user=os.getenv('POSTGRESDB_USER'),
        password=os.getenv('POSTGRESDB_PASSWORD'),
        host=os.getenv('POSTGRESDB_HOST'),
        port=os.getenv('POSTGRESDB_PORT')
    )
    
    # Create tables if they don't exist
    print("Creating tables if not exist...")
    with conn.cursor() as cur:
        create_tables(cur)
    conn.commit()

    # Parallel processing setup
    manager = multiprocessing.Manager()
    result_queue = manager.Queue()
    ranges = []
    chunk_size = max(1, total_to_process // (WORKERS * 2))
    
    # Create processing ranges
    start = START_FROM
    while start <= total_blocks:
        end = min(total_blocks, start + chunk_size - 1)
        ranges.append((start, end))
        start = end + 1
    
    print(f"Processing with {len(ranges)} chunks using {WORKERS} workers")
    
    # Process chunks in parallel
    with ProcessPoolExecutor(max_workers=WORKERS) as executor:
        futures = []
        for start_idx, end_idx in ranges:
            futures.append(
                executor.submit(
                    process_block_range, 
                    file_path, 
                    start_idx, 
                    end_idx, 
                    result_queue
                )
            )
        
        # Collect and insert results
        batch_counter = 0
        blocks_data_batch = []
        transactions_data_batch = []
        access_list_data_batch = []
        withdrawals_data_batch = []
        
        with tqdm(total=total_to_process, unit='block') as pbar:
            for future in as_completed(futures):
                blocks_data, transactions_data, access_list_data, withdrawals_data = result_queue.get()
                
                blocks_data_batch.extend(blocks_data)
                transactions_data_batch.extend(transactions_data)
                access_list_data_batch.extend(access_list_data)
                withdrawals_data_batch.extend(withdrawals_data)
                
                # Update progress bar
                pbar.update(len(blocks_data))
                
                # Insert when batch size is reached
                if len(blocks_data_batch) >= BATCH_SIZE:
                    insert_data_batch(
                        conn,
                        blocks_data_batch,
                        transactions_data_batch,
                        access_list_data_batch,
                        withdrawals_data_batch
                    )
                    batch_counter += 1
                    print(f"Inserted batch #{batch_counter} ({len(blocks_data_batch)} blocks)")
                    
                    # Reset batch collections
                    blocks_data_batch = []
                    transactions_data_batch = []
                    access_list_data_batch = []
                    withdrawals_data_batch = []
        
        # Insert remaining data in last batch
        if blocks_data_batch:
            insert_data_batch(
                conn,
                blocks_data_batch,
                transactions_data_batch,
                access_list_data_batch,
                withdrawals_data_batch
            )
            print(f"Inserted final batch ({len(blocks_data_batch)} blocks)")

    # Create indexes after data insertion
    print("Creating indexes...")
    with conn.cursor() as cur:
        create_indexes(cur)
    conn.commit()

    conn.close()
    print("Data import completed successfully!")

if __name__ == "__main__":
    main()