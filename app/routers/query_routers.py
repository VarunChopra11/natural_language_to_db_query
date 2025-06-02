from fastapi import APIRouter
from app.services.llm import GenerateQuery
from app.services.query import ExecuteQuery

router = APIRouter()

@router.get("/create_query")
async def create_query(natural_language: str, page_index: int = 1, rows_per_page: int = 10):
    """
    Create a SQL query from natural language using the Gemini model.
    
    Args:
        natural_language (str): The natural language query to convert.
        page_index (int): The page index for pagination.
        rows_per_page (int): The number of rows per page.
        
    Returns:
        dict: A dictionary containing the generated SQL query and other related information.
    """
    try:
        sql_query = await GenerateQuery.generate_query(natural_language, page_index, rows_per_page)
        if "query" not in sql_query:
            raise ValueError(f"Failed to parse Gemini response. Received: {sql_query}")
        
        if "count_query" in sql_query:
            total_rows = await ExecuteQuery.count_rows(sql_query["count_query"])
        
        columns, data = await ExecuteQuery.execute_query(sql_query["query"])

        sql_query["columns"] = columns
        sql_query["data"] = data
        sql_query["total_rows"] = total_rows if "count_query" in sql_query else len(data)
        sql_query["has_next_page"] = (page_index * rows_per_page) < sql_query["total_rows"]
    except Exception as e:
        return {"error": str(e)}
    return sql_query