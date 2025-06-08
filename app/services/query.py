from app.db.db import get_connection
import asyncpg
import time
from typing import Dict, List, Tuple, Any

class ExecuteQuery:
    @staticmethod
    async def execute_query(sql_query: str) -> Tuple[List[str], List[Dict[str, Any]]]:
        """
        Execute a SQL query and return the results asynchronously.
        """
        start_time = time.time()
        try:
            pool = await get_connection()
            async with pool.acquire() as conn:
                async with conn.transaction():
                    stmt = await conn.prepare(sql_query)
                    columns = [col.name for col in stmt.get_attributes()]
                    rows = await stmt.fetch()
                    
                    dict_results = [dict(row) for row in rows] if rows else []
                    
                    execution_time = time.time() - start_time
                    print(f"Query executed in {execution_time:.2f} seconds")
                    # print(f"Columns: {columns}")
                    # print(f"Results count: {len(dict_results)}")
                    
                    return columns, dict_results
                    
        except asyncpg.PostgresError as e:
            print(f"Database error: {str(e)}")
            raise
        except Exception as e:
            print(f"Error executing query: {str(e)}")
            raise

    @staticmethod
    async def count_rows(count_query: str) -> int:
        """
        Execute a count query and return the total number of rows asynchronously.
        """
        start_time = time.time()
        try:
            pool = await get_connection()
            async with pool.acquire() as conn:
                async with conn.transaction():
                    result = await conn.fetchrow(count_query)
                    total_rows = result[0] if result else 0
                    
                    execution_time = time.time() - start_time
                    print(f"Count query executed in {execution_time:.2f} seconds")
                    # print(f"Total rows: {total_rows}")
                    
                    return total_rows
                    
        except asyncpg.PostgresError as e:
            print(f"Database error in count query: {str(e)}")
            return 0
        except Exception as e:
            print(f"Error executing count query: {str(e)}")
            return 0