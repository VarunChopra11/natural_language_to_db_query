import os
import ijson
import psycopg2
from psycopg2.extras import execute_batch, Json
from datetime import datetime
from tqdm import tqdm
from dotenv import load_dotenv

load_dotenv()

START_FROM = 1

def convert_hex_to_numeric(value):
    """Convert hexadecimal string to numeric. If not hex, convert directly."""
    if isinstance(value, str) and value.startswith('0x'):
        return int(value, 16)
    return int(value) if value else 0

def count_blocks(filename):
    """Count total blocks in JSON file"""
    with open(filename, 'r') as f:
        return sum(1 for _ in ijson.items(f, 'item'))

def process_block(block, cur):
    block_values = (
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

    cur.execute("""
        INSERT INTO blocks (
            number, hash, parent_hash, base_fee_per_gas, blob_gas_used, difficulty,
            excess_blob_gas, extra_data, gas_limit, gas_used, logs_bloom, miner,
            mix_hash, nonce, parent_beacon_block_root, receipts_root, sha3_uncles,
            size, state_root, timestamp, transactions_root, withdrawals_root
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
            %s, %s, %s, %s, %s, %s, %s, %s
        )
    """, block_values)

    if 'transactions' in block:
        # transactions = []
        access_list = []
        for tx in block['transactions']:
            tx_values = (
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
            )
            
            cur.execute("""
                INSERT INTO transactions (
                    hash, block_number, chain_id, from_address, to_address, gas, gas_price,
                    input, max_fee_per_gas, max_priority_fee_per_gas, nonce, r, s,
                    transaction_index, type, v, value
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, tx_values)

            if 'accessList' in tx:
                for access in tx['accessList']:
                    access_list.append((
                        tx['hash'],
                        access['address'],
                        Json(access['storageKeys'])
                    ))

        if access_list:
            execute_batch(cur,
                """INSERT INTO access_list (transaction_hash, address, storage_keys)
                   VALUES (%s, %s, %s)""",
                access_list
            )

    if 'withdrawals' in block:
        withdrawals = []
        for wd in block['withdrawals']:
            withdrawals.append((
                int(block['number']),
                int(wd['index']),
                int(wd['validatorIndex']),
                wd['address'],
                int(wd['amount'])
            ))
        
        if withdrawals:
            execute_batch(cur,
                """INSERT INTO withdrawals (block_number, index, validator_index, address, amount)
                   VALUES (%s, %s, %s, %s, %s)""",
                withdrawals
            )



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
    cur = conn.cursor()

    #Progress bar
    with open(file_path, 'r') as f, \
         tqdm(total=total_to_process, unit='block') as pbar:
        
        blocks = ijson.items(f, 'item')
        current_index = 0
        
        for block in blocks:
            current_index += 1
            if current_index < START_FROM:
                continue
                
            process_block(block, cur)
            conn.commit()
            pbar.update(1)

    cur.close()
    conn.close()

if __name__ == "__main__":
    main()