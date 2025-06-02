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

PROMPT_TEMPLATE = """
Convert this natural language query into a PostgreSQL query using the following schema.
Use proper indexes and optimize for performance.

For ALL queries, enforce proper pagination and limit the results to prevent application crashes.

Schema Context: {schema_context}

IMPORTANT PAGINATION RULES:
1. ALWAYS include LIMIT and OFFSET for queries that return multiple rows 
2. Use page_index={page_index} and rows_per_page={rows_per_page} for pagination
3. Return both a main query and a count query for total rows
4. Sort by recent data first when appropriate (latest blocks/transactions)
5. For time-based queries, leverage block.timestamp index
6. For specific count queries (like "show me 5 transactions"), respect the user's request

Your response MUST be valid JSON with this format:
{{
  "query": "SQL query with LIMIT/OFFSET for pagination",
  "count_query": "Query to count total results for pagination",
  "explanation": "Brief explanation of the query"
}}

For queries requesting a specific number of results (e.g., "show last 5 transactions"), 
return only the main query without count_query since pagination is not needed.

Examples:

1. Input: "Show transactions from 0xabc to 0xdef in the last week"
   Output: {{
     "query": "SELECT * FROM transactions WHERE from_address = '0xabc' AND to_address = '0xdef' AND block_number IN (SELECT number FROM blocks WHERE timestamp >= NOW() - INTERVAL '7 DAYS') ORDER BY block_number DESC LIMIT {rows_per_page} OFFSET ({page_index} - 1) * {rows_per_page}",
     "count_query": "SELECT COUNT(*) FROM transactions WHERE from_address = '0xabc' AND to_address = '0xdef' AND block_number IN (SELECT number FROM blocks WHERE timestamp >= NOW() - INTERVAL '7 DAYS')",
     "explanation": "Uses address indexes and timestamp index, to filter transactions from the last week."
   }}

2. Input: "Show me the last 5 transactions"
   Output: {{
     "query": "SELECT * FROM transactions ORDER BY block_number DESC LIMIT 5",
     "explanation": "Shows the last 5 transactions."
   }}

3. Input: "Show all transactions"
   Output: {{
     "query": "SELECT * FROM transactions ORDER BY block_number DESC LIMIT {rows_per_page} OFFSET ({page_index} - 1) * {rows_per_page}",
     "count_query": "SELECT COUNT(*) FROM transactions",
     "explanation": "Returns all transactions ordered by block_number."
   }}

4. Input: "What's the total ETH transferred by miner 0xminer in March 2024?"
   Output: {{
     "query": "SELECT SUM(value) as total_eth FROM transactions WHERE from_address = '0xminer' AND block_number IN (SELECT number FROM blocks WHERE miner = '0xminer' AND timestamp BETWEEN '2024-03-01' AND '2024-04-01')",
     "explanation": "Uses miner index and address index for an aggregation query"
   }}

Now convert this natural language query: {query}
"""


class GenerateQuery:
    @staticmethod
    def extract_json_from_llm_response(response: str) -> Optional[Dict[str, Any]]:
        """
        Extract and parse JSON from an LLM response that might be wrapped in markdown code fences.
        """
        code_block_pattern = r"```(?:json)?\s*([\s\S]*?)\s*```"
        code_blocks = re.findall(code_block_pattern, response)
        
        if code_blocks:
            for block in code_blocks:
                try:
                    return json.loads(block)
                except json.JSONDecodeError:
                    continue
        
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
    async def generate_query(natural_language: str, page_index: int = 1, rows_per_page: int = 10) -> Dict[str, Any]:
        """
        Generate SQL query from natural language using Gemini model.
        """
        prompt = PROMPT_TEMPLATE.format(
            schema_context=SCHEMA_CONTEXT,
            query=natural_language,
            page_index=page_index,
            rows_per_page=rows_per_page
        )
        
        response = await model.generate_content_async(prompt)
        
        print("Response:", response.text)
        print("----------------------------------------")
        
        parsed_json = GenerateQuery.extract_json_from_llm_response(response.text)
        
        if not parsed_json:
            raise ValueError(f"Failed to parse Gemini response. Received: {response.text}")
        
        print("Parsed JSON response:", parsed_json)
        
        if "query" not in parsed_json:
            raise ValueError(f"Response missing required 'query' field: {parsed_json}")
        
        parsed_json['query'] = parsed_json['query'].format(
            page_index=page_index,
            rows_per_page=rows_per_page
        )
        
        if "count_query" in parsed_json:
            parsed_json['count_query'] = parsed_json['count_query'].format(
                page_index=page_index,
                rows_per_page=rows_per_page
            )

        print("Final parsed JSON:", parsed_json)
        
        return parsed_json