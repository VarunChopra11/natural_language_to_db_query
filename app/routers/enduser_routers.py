from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
import asyncpg
from typing import List

from app.services.api_services.apikey_auth_services import get_current_client_from_api_key
from app.services.auth_services import get_current_client
from app.db.db import get_connection
from app.schemas.user import EndUserCreate, EndUserResponse, EndUserSimpleResponse
from app.services.endusers_services import create_end_user, list_end_users, get_end_user, delete_end_user
from app.services.financial_profile_service import FinancialProfileService

router = APIRouter()

@router.post("/apikey/create_enduser", response_model=EndUserResponse)
async def create_end_user_route(
    end_user: EndUserCreate,
    background_tasks: BackgroundTasks,
    client: dict = Depends(get_current_client_from_api_key),
    db_pool: asyncpg.Pool = Depends(get_connection)
):
    client_id = client["id"]
    response = await create_end_user(end_user, client_id, db_pool)
    
    # Add background task to fetch financial data
    background_tasks.add_task(
        FinancialProfileService().fetch_and_store_profile,
        end_user.wallet_address
    )
    
    return response

@router.get("/apikey/list_endusers", response_model=List[EndUserSimpleResponse])
async def list_end_users_apikey(
    client: dict = Depends(get_current_client_from_api_key),
    db_pool: asyncpg.Pool = Depends(get_connection)
):
    client_id = client["id"]
    return await list_end_users(client_id, db_pool)

@router.get("/apikey/get_enduser/{wallet_address}", response_model=EndUserSimpleResponse)
async def get_end_user_route(
    wallet_address: str,
    client: dict = Depends(get_current_client_from_api_key),
    db_pool: asyncpg.Pool = Depends(get_connection)
):
    client_id = client["id"]
    return await get_end_user(wallet_address, client_id, db_pool)

@router.delete("/apikey/delete_enduser/{wallet_address}")
async def delete_end_user_route(
    wallet_address: str,
    client: dict = Depends(get_current_client_from_api_key),
    db_pool: asyncpg.Pool = Depends(get_connection)
):
    client_id = client["id"]
    return await delete_end_user(wallet_address, client_id, db_pool)

@router.get("/api/list_endusers", response_model=List[EndUserSimpleResponse])
async def list_end_users_auth(
    client: dict = Depends(get_current_client),
    db_pool: asyncpg.Pool = Depends(get_connection)
):
    """
    List all end users for the authenticated client using API key.
    
    Args:
        client (dict): Authenticated client information from API key
        db_pool (asyncpg.Pool): Database connection pool
        
    Returns:
        List[EndUserSimpleResponse]: List of end users for the client
        
    Raises:
        HTTPException: If database error occurs
    """
    try:
        client_id = client["id"]
        
        async with db_pool.acquire() as conn:
            end_users = await conn.fetch(
                """SELECT id, client_id, wallet_address, email
                   FROM end_users 
                   WHERE client_id = $1
                   ORDER BY created_at DESC""",
                client_id
            )
            
            return [
                EndUserSimpleResponse(
                    id=user["id"],
                    client_id=user["client_id"],
                    wallet_address=user["wallet_address"],
                    email=user["email"]
                )
                for user in end_users
            ]
            
    except Exception as e:
        print(f"Error listing end users: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing end users: {str(e)}"
        )