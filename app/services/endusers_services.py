import asyncpg
from datetime import datetime
from typing import List
from fastapi import HTTPException, status
from app.schemas.user import EndUserCreate, EndUserResponse, EndUserSimpleResponse

async def create_end_user(
    end_user: EndUserCreate,
    client_id: int,
    db_pool: asyncpg.Pool
) -> EndUserResponse:
    try:
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
            
            new_user = await conn.fetchrow(
                """INSERT INTO end_users (client_id, wallet_address, email, created_at)
                   VALUES ($1, $2, $3, $4)
                   RETURNING id, client_id, wallet_address, email, created_at""",
                client_id, end_user.wallet_address, end_user.email, datetime.now()
            )
            
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
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating end user: {str(e)}"
        )

async def list_end_users(
    client_id: int,
    db_pool: asyncpg.Pool
) -> List[EndUserSimpleResponse]:
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

async def get_end_user(
    wallet_address: str,
    client_id: int,
    db_pool: asyncpg.Pool
) -> EndUserSimpleResponse:
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

async def delete_end_user(
    wallet_address: str,
    client_id: int,
    db_pool: asyncpg.Pool
) -> dict:
    async with db_pool.acquire() as conn:
        result = await conn.execute(
            """DELETE FROM end_users 
               WHERE wallet_address = $1 AND client_id = $2""",
            wallet_address, client_id
        )
        
        rows_affected = int(result.split()[-1])
        
        if rows_affected == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="End user not found or not authorized to delete"
            )
        
        return {"message": "End user deleted successfully"}