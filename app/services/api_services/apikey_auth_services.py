from fastapi import HTTPException, status, Depends, Header
from typing import Optional, Dict, Any
import asyncpg
from app.db.db import get_connection
from app.services.api_services.apikey_services import ApiKeyService

class ApiKeyAuthService:
    @staticmethod
    async def verify_api_key(api_key: str, db_pool: asyncpg.Pool) -> Optional[Dict[str, Any]]:
        """
        Verify an API key and return client information if valid.
        
        Args:
            api_key (str): The API key to validate
            db_pool (asyncpg.Pool): Database connection pool
            
        Returns:
            Optional[Dict[str, Any]]: Client information if valid, None if invalid
        """
        if not api_key:
            return None
            
        # Remove any 'Bearer ' prefix if present
        if api_key.startswith('Bearer '):
            api_key = api_key[7:]
            
        try:
            client_info = await ApiKeyService.validate_api_key(api_key, db_pool)
            return client_info
        except Exception as e:
            print(f"Error verifying API key: {str(e)}")
            return None

async def get_api_key_from_header(
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None)
) -> str:
    """
    Extract API key from Authorization header or X-API-Key header.
    
    Args:
        authorization: Authorization header (Bearer token format)
        x_api_key: X-API-Key header (direct API key)
        
    Returns:
        str: The API key
        
    Raises:
        HTTPException: If no API key is provided
    """
    api_key = None
    
    # Try to get API key from Authorization header
    if authorization:
        if authorization.startswith('Bearer '):
            api_key = authorization[7:]
        else:
            api_key = authorization
    
    # Try to get API key from X-API-Key header
    elif x_api_key:
        api_key = x_api_key
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is required. Provide it via 'Authorization: Bearer <api_key>' or 'X-API-Key: <api_key>' header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return api_key

async def get_current_client_from_api_key(
    api_key: str = Depends(get_api_key_from_header),
    db_pool: asyncpg.Pool = Depends(get_connection)
) -> Dict[str, Any]:
    """
    Get current client information from API key authentication.
    
    Args:
        api_key (str): The API key from headers
        db_pool (asyncpg.Pool): Database connection pool
        
    Returns:
        Dict[str, Any]: Client information
        
    Raises:
        HTTPException: If API key is invalid or client not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid API key or client not authorized",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        client_info = await ApiKeyAuthService.verify_api_key(api_key, db_pool)
        
        if not client_info:
            raise credentials_exception
            
        if not client_info.get("is_verified"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Client account is not verified"
            )
            
        return {
            "id": client_info["client_id"],
            "company_name": client_info["company_name"],
            "email": client_info["email"],
            "is_verified": client_info["is_verified"],
            "api_key_id": client_info["api_key_id"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error authenticating with API key: {str(e)}")
        raise credentials_exception