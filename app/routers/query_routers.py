from fastapi import APIRouter, Depends, HTTPException
from app.services.llm import GenerateQuery
from app.services.query import ExecuteQuery
from app.services.auth_services import get_current_client
from fastapi import status

router = APIRouter()

@router.get("/create_query")
async def create_query(
    natural_language: str, 
    page_index: int = 1, 
    rows_per_page: int = 10, 
    user: dict = Depends(get_current_client)
):
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

        if not user or not user.get("is_verified"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User not authenticated or verified"
            )

        sql_query = await GenerateQuery.generate_query(natural_language, page_index, rows_per_page)
        if "query" not in sql_query:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Failed to parse Gemini response. Received: {sql_query}"
            )
        
        total_rows = None
        if "count_query" in sql_query:
            total_rows = await ExecuteQuery.count_rows(sql_query["count_query"])
        
        columns, data = await ExecuteQuery.execute_query(sql_query["query"])

        response_data = {
            "query": sql_query["query"],
            "columns": columns,
            "data": data,
            "total_rows": total_rows if total_rows is not None else len(data),
            "has_next_page": (page_index * rows_per_page) < (total_rows if total_rows is not None else len(data)),
            "page_index": page_index,
            "rows_per_page": rows_per_page
        }

        if "count_query" in sql_query:
            response_data["count_query"] = sql_query["count_query"]

        return response_data

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing query: {str(e)}"
        )