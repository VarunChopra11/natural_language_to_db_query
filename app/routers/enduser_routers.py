from fastapi import APIRouter, Depends, HTTPException, status
import asyncpg
from datetime import datetime
from typing import List

from app.services.api_services.apikey_auth_services import get_current_client_from_api_key
from app.db.db import get_connection
from app.schemas.user import EndUserCreate, EndUserResponse, EndUserSimpleResponse

router = APIRouter()

@router.post("/create", response_model=EndUserResponse)
async def create_end_user(
    end_user: EndUserCreate,
    client: dict = Depends(get_current_client_from_api_key),
    db_pool: asyncpg.Pool = Depends(get_connection)
):
    """
    Create a new end user using API key authentication.
    
    Args:
        end_user (EndUserCreate): End user data (wallet_address, email)
        client (dict): Authenticated client information from API key
        db_pool (asyncpg.Pool): Database connection pool
        
    Returns:
        EndUserResponse: Created end user information with success message
        
    Raises:
        HTTPException: If wallet address already exists or database error occurs
    """
    try:
        print(f"Creating end user for client: {client['company_name']} (ID: {client['id']})")
        print(f"End user data: wallet={end_user.wallet_address}, email={end_user.email}")

        client_id = client["id"]
        
        async with db_pool.acquire() as conn:
            # Check if wallet address already exists for this client
            existing_user = await conn.fetchrow(
                "SELECT id FROM end_users WHERE wallet_address = $1 AND client_id = $2",
                end_user.wallet_address, client_id
            )
            
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Wallet address already exists for this client"
                )
            
            try:
                async with conn.transaction():
                    # Insert new end user
                    new_user = await conn.fetchrow(
                        """INSERT INTO end_users (client_id, wallet_address, email, created_at)
                           VALUES ($1, $2, $3, $4)
                           RETURNING id, client_id, wallet_address, email, created_at""",
                        client_id, end_user.wallet_address, end_user.email, datetime.now()
                    )
                    
                    print(f"Successfully created end user with ID: {new_user['id']}")
                    
                    return EndUserResponse(
                        id=new_user["id"],
                        client_id=new_user["client_id"],
                        wallet_address=new_user["wallet_address"],
                        email=new_user["email"],
                        created_at=new_user["created_at"].isoformat(),
                        message="End user created successfully"
                    )
                    
            except asyncpg.UniqueViolationError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Wallet address already exists"
                )
                
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error creating end user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating end user: {str(e)}"
        )

@router.get("/list", response_model=List[EndUserSimpleResponse])
async def list_end_users(
    client: dict = Depends(get_current_client_from_api_key),
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

@router.get("/get/{wallet_address}", response_model=EndUserSimpleResponse)
async def get_end_user(
    wallet_address: str,
    client: dict = Depends(get_current_client_from_api_key),
    db_pool: asyncpg.Pool = Depends(get_connection)
):
    """
    Get a specific end user by wallet address for the authenticated client.
    
    Args:
        wallet_address (str): Wallet address of the end user
        client (dict): Authenticated client information from API key
        db_pool (asyncpg.Pool): Database connection pool
        
    Returns:
        EndUserSimpleResponse: End user information
        
    Raises:
        HTTPException: If end user not found or database error occurs
    """
    try:
        client_id = client["id"]
        
        async with db_pool.acquire() as conn:
            end_user = await conn.fetchrow(
                """SELECT id, client_id, wallet_address, email
                   FROM end_users 
                   WHERE wallet_address = $1 AND client_id = $2""",
                wallet_address, client_id
            )
            
            if not end_user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="End user not found"
                )
            
            return EndUserSimpleResponse(
                id=end_user["id"],
                client_id=end_user["client_id"],
                wallet_address=end_user["wallet_address"],
                email=end_user["email"]
            )
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting end user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting end user: {str(e)}"
        )

@router.delete("/delete/{wallet_address}")
async def delete_end_user(
    wallet_address: str,
    client: dict = Depends(get_current_client_from_api_key),
    db_pool: asyncpg.Pool = Depends(get_connection)
):
    """
    Delete a specific end user by wallet address for the authenticated client.
    
    Args:
        wallet_address (str): Wallet address of the end user to delete
        client (dict): Authenticated client information from API key
        db_pool (asyncpg.Pool): Database connection pool
        
    Returns:
        dict: Success message
        
    Raises:
        HTTPException: If end user not found or database error occurs
    """
    try:
        client_id = client["id"]
        
        async with db_pool.acquire() as conn:
            async with conn.transaction():
                # Delete the end user
                result = await conn.execute(
                    """DELETE FROM end_users 
                       WHERE wallet_address = $1 AND client_id = $2""",
                    wallet_address, client_id
                )
                
                # Check if any row was affected
                rows_affected = int(result.split()[-1])
                
                if rows_affected == 0:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="End user not found or not authorized to delete"
                    )
                
                return {"message": "End user deleted successfully"}
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting end user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting end user: {str(e)}"
        )