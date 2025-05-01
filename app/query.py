from app.config import DB_CONFIG
import psycopg2
from psycopg2 import sql


class ExecuteQuery:
    def execute_query(sql_query):
        """Execute query and return results"""
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        try:
            cur.execute(sql.SQL(sql_query))
            results = cur.fetchall()
            columns = [desc[0] for desc in cur.description]
        finally:
            cur.close()
            conn.close()
        
        return columns, results