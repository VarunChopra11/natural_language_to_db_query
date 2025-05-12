from app.config import DB_CONFIG
import psycopg2
from psycopg2 import sql
import time
from typing import Dict, List, Tuple, Any


class ExecuteQuery:
    @staticmethod
    def execute_query(sql_query: str) -> Tuple[List[str], List[Dict[str, Any]]]:
        """
        Execute a SQL query and return the results.
        
        Args:
            sql_query: SQL query to execute
            
        Returns:
            Tuple of (column_names, result_rows)
        """
        start_time = time.time()
        conn = None
        cur = None
        
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()
            
            cur.execute(sql.SQL(sql_query))
            
            if cur.description:
                results = cur.fetchall()
                columns = [desc[0] for desc in cur.description]

                dict_results = []
                for row in results:
                    dict_results.append(dict(zip(columns, row)))
            else:
                columns = []
                dict_results = []
                
            execution_time = time.time() - start_time
            print(f"Query executed in {execution_time:.2f} seconds")
            print(f"Columns: {columns}")
            print(f"Results count: {len(dict_results)}")
            
            return columns, dict_results
            
        except psycopg2.Error as e:
            print(f"Database error: {str(e)}")
            raise
        except Exception as e:
            print(f"Error executing query: {str(e)}")
            raise
        finally:
            if cur:
                cur.close()
            if conn:
                conn.close()

    @staticmethod
    def count_rows(count_query: str) -> int:
        """
        Execute a count query and return the total number of rows.
        
        Args:
            count_query: SQL count query to execute
            
        Returns:
            Total number of rows as integer
        """
        start_time = time.time()
        conn = None
        cur = None
        
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()
            
            # Execute the count query
            cur.execute(sql.SQL(count_query))
            result = cur.fetchone()
            
            total_rows = result[0] if result else 0
            
            execution_time = time.time() - start_time
            print(f"Count query executed in {execution_time:.2f} seconds")
            print(f"Total rows: {total_rows}")
            
            return total_rows
            
        except psycopg2.Error as e:
            print(f"Database error in count query: {str(e)}")
            return 0
        except Exception as e:
            print(f"Error executing count query: {str(e)}")
            return 0
        finally:
            if cur:
                cur.close()
            if conn:
                conn.close()