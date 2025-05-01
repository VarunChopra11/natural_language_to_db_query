import google.generativeai as genai
from app.config import GEMINI_API_KEY
import json
import re
from typing import Dict, Any, Optional

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')

SCHEMA_CONTEXT = """
Ethereum Blockchain Database Schema (Optimized for Query Performance):

1. BLOCKS Table Structure & Indexes:
- Columns:
  number (PK), hash (UNIQUE), parent_hash, base_fee_per_gas, 
  blob_gas_used, difficulty, excess_blob_gas, extra_data, gas_limit, 
  gas_used, logs_bloom, miner, mix_hash, nonce, parent_beacon_block_root,
  receipts_root, sha3_uncles, size, state_root, timestamp, 
  transactions_root, withdrawals_root
- Indexed Columns (Optimized For):
  • timestamp → Time-range queries
  • miner → Miner activity analysis
  • parent_hash → Chain reorganization tracking

2. TRANSACTIONS Table Structure & Indexes:
- Columns:
  hash (PK), block_number (FK), chain_id, from_address, to_address, gas,
  gas_price, input, max_fee_per_gas, max_priority_fee_per_gas, nonce, r, s,
  transaction_index, type, v, value
- Indexed Columns (Optimized For):
  • block_number → Block-Transaction relationships
  • from_address → Sender activity analysis
  • to_address → Receiver activity analysis
  • gas_price → Fee market analysis
  • type → Transaction type filtering (Legacy/EIP-1559)

3. WITHDRAWALS Table Structure & Indexes:
- Columns:
  block_number (PK,FK), index (PK), validator_index, address, amount
- Indexed Columns (Optimized For):
  • validator_index → Validator-specific queries
  • address → Withdrawal destination analysis

4. ACCESS_LIST Table Structure & Indexes:
- Columns:
  transaction_hash (PK,FK), address (PK), storage_keys
- Indexed Column:
  • address → Contract storage access patterns

Important Indexes for Query Optimization:
 Time-based Analysis → Use blocks.timestamp index
 Address Activity → Use from_address/to_address (transactions) or address (withdrawals/access_list)
 Block-Transaction Relationships → Use transactions.block_number index
 Validator Operations → Use withdrawals.validator_index index
 Gas Market Analysis → Use transactions.gas_price index
 Transaction Type Filtering → Use transactions.type index
 Storage Access Patterns → Use access_list.address index
"""

PROMPT_TEMPLATE = f"""
Convert this natural language query into a PostgreSQL query using the following schema.
Use proper indexes and optimize for performance. 
Return ONLY the SQL query in this format: {{"query": "SQL_QUERY", "explanation": "brief explanation"}}

Schema Context: {SCHEMA_CONTEXT}

Examples:
1. Input: "Show transactions from 0xabc to 0xdef in the last week"
   Output: {{
     "query": "SELECT * FROM transactions WHERE from_address = '0xabc' AND to_address = '0xdef' AND block_number IN (SELECT number FROM blocks WHERE timestamp >= NOW() - INTERVAL '7 DAYS')",
     "explanation": "Uses address indexes and timestamp index"
   }}

2. Input: "What's the total ETH transferred by miner 0xminer in March 2024?"
   Output: {{
     "query": "SELECT SUM(value) FROM transactions WHERE from_address = '0xminer' AND block_number IN (SELECT number FROM blocks WHERE miner = '0xminer' AND timestamp BETWEEN '2024-03-01' AND '2024-04-01')",
     "explanation": "Uses miner index and address index"
   }}

Now convert this: 
"""


class GenerateQuery:
    @staticmethod
    def extract_json_from_llm_response(response: str) -> Optional[Dict[str, Any]]:
        """
        Extract and parse JSON from an LLM response that might be wrapped in markdown code fences.
        """
        # Pattern to match code blocks with or without language specifier
        code_block_pattern = r"```(?:json)?\s*([\s\S]*?)\s*```"
        code_blocks = re.findall(code_block_pattern, response)
        
        if code_blocks:
            # Try each code block until we find valid JSON
            for block in code_blocks:
                try:
                    return json.loads(block)
                except json.JSONDecodeError:
                    continue
        
        # If no code blocks or none contained valid JSON, try the entire response
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            json_pattern = r"\{[\s\S]*?\}"
            for match in re.finditer(json_pattern, response):
                try:
                    return json.loads(match.group(0))
                except json.JSONDecodeError:
                    continue
        
        return None

    @staticmethod
    def generate_query(natural_language: str) -> Dict[str, Any]:
        """
        Generate SQL query from natural language using Gemini model.
        """
        prompt = PROMPT_TEMPLATE + natural_language
        response = model.generate_content(prompt)
        
        print("Response:", response.text)
        print("----------------------------------------")
        
        parsed_json = GenerateQuery.extract_json_from_llm_response(response.text)
        
        if not parsed_json:
            raise ValueError(f"Failed to parse Gemini response. Received: {response.text}")
        
        print("Parsed JSON response:", parsed_json)
        
        if "query" not in parsed_json:
            raise ValueError(f"Response missing required 'query' field: {parsed_json}")
        
        return parsed_json