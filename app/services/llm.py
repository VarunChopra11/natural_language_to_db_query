from anthropic import AsyncAnthropicVertex
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from app.config import (
    GCP_PROJECT_ID,
    GCP_LOCATION,
    CLAUDE_MODEL_NAME,
    SA_INFO,
)
import json
import re
import base64
from typing import Dict, Any, Optional


SCOPES = ["https://www.googleapis.com/auth/cloud-platform"]
svc_info = json.loads(base64.b64decode(SA_INFO).decode())
credentials = service_account.Credentials.from_service_account_info(
    svc_info,
    scopes=SCOPES,
)

access_token = credentials.token
if not access_token or credentials.expired:
    credentials.refresh(Request())
    access_token = credentials.token

client = AsyncAnthropicVertex(
    region=GCP_LOCATION,
    project_id=GCP_PROJECT_ID,
    access_token=access_token,
)


SCHEMA_CONTEXT = """
PostgreSQL Database Schema for Client and End User Financial Data:

1. client_users
   - id (PK), company_name, email, is_verified, created_at, updated_at
   - Indexes: UNIQUE on company_name and email

2. api_keys
   - id (PK), api_key_id, client_id (FK to client_users), api_key_hash, is_active, created_at, updated_at, last_used_at
   - Indexes: UNIQUE on api_key_id and api_key_hash

3. end_users
   - id (PK), client_id (FK to client_users), wallet_address, email, created_at
   - Indexes: UNIQUE on wallet_address, idx_end_users_wallet

4. financial_portfolios
   - id (PK), end_user_id (FK to end_users), client_id (FK to client_users), total_balance_usd, updated_at
   - Indexes: UNIQUE (end_user_id), idx_financial_portfolios_client

5. token_balances
   - id (PK), end_user_id (FK to end_users), client_id (FK to client_users), symbol, token_address, balance, balance_usd, price, network, img_url, updated_at
   - Indexes: UNIQUE (end_user_id, token_address), idx_token_balances_end_user, idx_token_balances_client, idx_token_balances_network

6. app_balances
   - id (PK), end_user_id (FK to end_users), client_id (FK to client_users), meta_type, position_count, balance_usd, updated_at
   - Indexes: UNIQUE (end_user_id, meta_type), idx_app_balances_end_user, idx_app_balances_client

7. nft_assets
   - id (PK), end_user_id (FK to end_users), client_id (FK to client_users), token_id, collection_address, name, estimated_value, img_url, network, last_updated
   - Indexes: UNIQUE (end_user_id, token_id, collection_address), idx_nft_assets_end_user, idx_nft_assets_client, idx_nft_assets_collection

8. transaction_history
   - id (PK), end_user_id (FK to end_users), client_id (FK to client_users), tx_hash, block_number, timestamp, from_address, to_address, network, method_signature, method_sighash, processed_description, description, value_usd, value_eth, created_at
   - Indexes: UNIQUE (tx_hash), idx_tx_history_end_user, idx_tx_history_client, idx_tx_history_timestamp, idx_tx_history_hash

Use appropriate indexes for performance. Always include LIMIT and OFFSET for paginated queries. For recent data, sort by timestamp DESC or created_at DESC.
"""


PROMPT_TEMPLATE = """
You are a SQL query generator.  
You convert natural language into PostgreSQL queries **strictly following the given schema**.

Schema Context: {schema_context}

Your output **MUST** follow these hard rules:

✅ RULES:
1. The entire response must be **ONLY valid JSON**, no text or comments outside the JSON.  
2. Wrap the JSON inside a single ```json code block.  
3. Use page_index={page_index} and rows_per_page={rows_per_page} for pagination
4. If a specific small count is requested (e.g. "last 5 transactions"), **omit** "count_query".  
5. Put **all explanations** inside the "explanation" field — never outside the JSON.  
6. Do not say "Sure", "Here is it", or add any notes before or after the JSON.

✅ OUTPUT FORMAT:
```json
{{
  "query": "Your SQL query here",
  "count_query": "Count query if needed, or omit",
  "explanation": "Brief explanation inside the JSON only"
}}
```

For queries requesting a specific number of results (e.g., "show last 5 transactions"), 
return only the main query without count_query since pagination is not needed.

Examples:

1. Input: "Show transactions from 0xabc to 0xdef in the last week"
   Output: {{{{
     "query": "SELECT * FROM transactions WHERE from_address = '0xabc' AND to_address = '0xdef' AND block_number IN (SELECT number FROM blocks WHERE timestamp >= NOW() - INTERVAL '7 DAYS') ORDER BY block_number DESC LIMIT {rows_per_page} OFFSET ({page_index} - 1) * {rows_per_page}",
     "count_query": "SELECT COUNT(*) FROM transactions WHERE from_address = '0xabc' AND to_address = '0xdef' AND block_number IN (SELECT number FROM blocks WHERE timestamp >= NOW() - INTERVAL '7 DAYS')",
     "explanation": "Uses address indexes and timestamp index, to filter transactions from the last week."
   }}}}

2. Input: "Show me the last 5 transactions"
   Output: {{{{
     "query": "SELECT * FROM transactions ORDER BY block_number DESC LIMIT 5",
     "explanation": "Shows the last 5 transactions."
   }}}}

3. Input: "Show all transactions"
   Output: {{{{
     "query": "SELECT * FROM transactions ORDER BY block_number DESC LIMIT {rows_per_page} OFFSET ({page_index} - 1) * {rows_per_page}",
     "count_query": "SELECT COUNT(*) FROM transactions",
     "explanation": "Returns all transactions ordered by block_number."
   }}}}

4. Input: "What's the total ETH transferred by miner 0xminer in March 2024?"
   Output: {{{{
     "query": "SELECT SUM(value) as total_eth FROM transactions WHERE from_address = '0xminer' AND block_number IN (SELECT number FROM blocks WHERE miner = '0xminer' AND timestamp BETWEEN '2024-03-01' AND '2024-04-01')",
     "explanation": "Uses miner index and address index for an aggregation query"
   }}}}

Now convert this natural language query: {query}
"""


class GenerateQuery:
    @staticmethod
    def extract_json_from_llm_response(response: str) -> Optional[Dict[str, Any]]:
        """
        Extract JSON from Claude response, handling code fences.
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
            json_pattern = r"\{[\\s\\S]*?\}"
            for match in re.finditer(json_pattern, response):
                try:
                    return json.loads(match.group(0))
                except json.JSONDecodeError:
                    continue

        return None

    @staticmethod
    async def generate_query(natural_language: str, page_index: int = 1, rows_per_page: int = 10) -> Dict[str, Any]:
        """
        Generate SQL query from natural language using Claude.
        """
        try:
            prompt = PROMPT_TEMPLATE.format(
                schema_context=SCHEMA_CONTEXT,
                query=natural_language,
                page_index=page_index,
                rows_per_page=rows_per_page
            )
        except Exception as e:
            print("Error formatting prompt:", e)
            raise
            
        response = await client.messages.create(
            model=CLAUDE_MODEL_NAME,
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        parsed_json = GenerateQuery.extract_json_from_llm_response(response.content[0].text)

        if not parsed_json:
            raise ValueError(f"Failed to parse Claude response. Received: {response.content[0].text}")

        if "query" not in parsed_json:
            raise ValueError(f"Missing 'query' in LLM output: {parsed_json}")

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
