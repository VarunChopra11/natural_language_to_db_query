from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi import status
import asyncpg

from app.services.auth_services import get_current_client
from app.services.api_services.apikey_services import ApiKeyService
from app.db.db import get_connection
from app.schemas.apikey import ApiKeyResponse, ApiKeyListResponse

router = APIRouter()

@router.post("/create_apikey", response_model=ApiKeyResponse)
async def create_api_key(
    user: dict = Depends(get_current_client),
    db_pool: asyncpg.Pool = Depends(get_connection)
):
    """
    Create a new API key for the authenticated client.
    Maximum of 5 API keys per client allowed.
    
    Returns:
        ApiKeyResponse: Contains the generated API key and its ID
    """
    try:
        print("Creating API key for user:", user)

        if not user or not user.get("is_verified"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User not authenticated or verified"
            )

        client_id = user["id"]
        
        # Check if client already has maximum number of API keys
        async with db_pool.acquire() as conn:
            existing_keys_count = await conn.fetchval(
                "SELECT COUNT(*) FROM api_keys WHERE client_id = $1 AND is_active = TRUE",
                client_id
            )
            
            if existing_keys_count >= 5:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Maximum number of API keys (5) reached"
                )

        # Generate new API key
        api_key_data = await ApiKeyService.generate_api_key(client_id, db_pool)
        
        return ApiKeyResponse(
            api_key_id=api_key_data["api_key_id"],
            api_key=api_key_data["api_key"],
            created_at=api_key_data["created_at"]
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating API key: {str(e)}"
        )

@router.get("/fetch_apikeys", response_model=ApiKeyListResponse)
async def fetch_api_keys(
    request: Request,
    user: dict = Depends(get_current_client),
    db_pool: asyncpg.Pool = Depends(get_connection)
):
    """
    Fetch all API keys for the authenticated client.
    Returns masked API keys (only last 3 characters visible) with complete API key IDs.
    
    Returns:
        ApiKeyListResponse: List of masked API keys with their IDs
    """
    try:
        if not user or not user.get("is_verified"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User not authenticated or verified"
            )

        client_id = user["id"]
        
        # Fetch API keys for the client
        api_keys = await ApiKeyService.fetch_client_api_keys(client_id, db_pool)
        
        return ApiKeyListResponse(
            api_keys=api_keys,
            total_count=len(api_keys)
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching API keys: {str(e)}"
        )

@router.delete("/delete_apikey")
async def delete_api_key(
    request: Request,
    user: dict = Depends(get_current_client),
    db_pool: asyncpg.Pool = Depends(get_connection)
):
    """
    Delete a specific API key for the authenticated client.
    
    Args:
        api_key_id (str): The ID of the API key to delete
        
    Returns:
        dict: Success message
    """
    try:
        if not user or not user.get("is_verified"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User not authenticated or verified"
            )

        client_id = user["id"]
        body = await request.json()
        api_key_id = body.get("api_key_id")

        if not api_key_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="api_key_id is required"
            )
        
        # Delete the API key
        deleted = await ApiKeyService.delete_api_key(client_id, api_key_id, db_pool)
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found or not authorized to delete"
            )
        
        return {"message": "API key deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting API key: {str(e)}"
        )