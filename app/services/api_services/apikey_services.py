import secrets
import string
import asyncpg
from datetime import datetime
from typing import List, Dict, Any, Optional
import uuid

class ApiKeyService:
    @staticmethod
    def _generate_secure_api_key(length: int = 32) -> str:
        """
        Generate a secure random API key.
        
        Args:
            length (int): Length of the API key (default: 32)
            
        Returns:
            str: Secure random API key with prefix
        """
        # Use a combination of letters and digits for the API key
        alphabet = string.ascii_letters + string.digits
        api_key = ''.join(secrets.choice(alphabet) for _ in range(length))
        
        # Add a prefix to identify it as an API key
        return f"hq_{api_key}"

    @staticmethod
    def _generate_api_key_id() -> str:
        """
        Generate a unique API key ID.
        
        Returns:
            str: Unique API key ID
        """
        return str(uuid.uuid4())

    @staticmethod
    def _mask_api_key(api_key: str) -> str:
        """
        Mask the API key showing only the last 3 characters.
        
        Args:
            api_key (str): Full API key
            
        Returns:
            str: Masked API key
        """
        if len(api_key) <= 3:
            return "***"
        return "*" * (len(api_key) - 3) + api_key[-3:]

    @staticmethod
    async def generate_api_key(client_id: int, db_pool: asyncpg.Pool) -> Dict[str, Any]:
        """
        Generate a new API key for a client and store it in the database.
        
        Args:
            client_id (int): The client's ID
            db_pool (asyncpg.Pool): Database connection pool
            
        Returns:
            Dict[str, Any]: Dictionary containing api_key_id, api_key, and created_at
            
        Raises:
            Exception: If database operation fails
        """
        api_key = ApiKeyService._generate_secure_api_key()
        api_key_id = ApiKeyService._generate_api_key_id()
        print(f"Generating API key for client {client_id}: {api_key}")
        print(f"Generated API key ID: {api_key_id}")  # Debug statement to show generated ID
        
        try:
            async with db_pool.acquire() as conn:
                async with conn.transaction():
                    # Insert the new API key
                    result = await conn.fetchrow(
                        """INSERT INTO api_keys (api_key_id, client_id, api_key_hash, is_active, created_at)
                           VALUES ($1, $2, $3, TRUE, $4)
                           RETURNING api_key_id, created_at""",
                        api_key_id, client_id, api_key, datetime.now()
                    )
                    
                    return {
                        "api_key_id": result["api_key_id"],
                        "api_key": api_key,
                        "created_at": result["created_at"]
                    }
                    
        except asyncpg.PostgresError as e:
            print(f"Database error generating API key: {str(e)}")
            raise Exception(f"Failed to generate API key: {str(e)}")
        except Exception as e:
            print(f"Error generating API key: {str(e)}")
            raise

    @staticmethod
    async def fetch_client_api_keys(client_id: int, db_pool: asyncpg.Pool) -> List[Dict[str, Any]]:
        """
        Fetch all active API keys for a client with masked keys.
        
        Args:
            client_id (int): The client's ID
            db_pool (asyncpg.Pool): Database connection pool
            
        Returns:
            List[Dict[str, Any]]: List of API keys with masked values
            
        Raises:
            Exception: If database operation fails
        """
        try:
            async with db_pool.acquire() as conn:
                rows = await conn.fetch(
                    """SELECT api_key_id, api_key_hash, created_at, last_used_at
                       FROM api_keys 
                       WHERE client_id = $1 AND is_active = TRUE
                       ORDER BY created_at DESC""",
                    client_id
                )
                
                api_keys = []
                for row in rows:
                    api_keys.append({
                        "api_key_id": row["api_key_id"],
                        "masked_api_key": ApiKeyService._mask_api_key(row["api_key_hash"]),
                        "created_at": row["created_at"],
                        "last_used_at": row["last_used_at"]
                    })
                
                return api_keys
                
        except asyncpg.PostgresError as e:
            print(f"Database error fetching API keys: {str(e)}")
            raise Exception(f"Failed to fetch API keys: {str(e)}")
        except Exception as e:
            print(f"Error fetching API keys: {str(e)}")
            raise

    @staticmethod
    async def delete_api_key(client_id: int, api_key_id: str, db_pool: asyncpg.Pool) -> bool:
        """
        Delete (deactivate) an API key for a client.
        
        Args:
            client_id (int): The client's ID
            api_key_id (str): The API key ID to delete
            db_pool (asyncpg.Pool): Database connection pool
            
        Returns:
            bool: True if API key was deleted, False if not found
            
        Raises:
            Exception: If database operation fails
        """
        try:
            async with db_pool.acquire() as conn:
                async with conn.transaction():
                    # Soft delete by setting is_active to False
                    result = await conn.execute(
                        """UPDATE api_keys 
                           SET is_active = FALSE, updated_at = $1
                           WHERE client_id = $2 AND api_key_id = $3 AND is_active = TRUE""",
                        datetime.now(), client_id, api_key_id
                    )
                    
                    # Check if any row was affected
                    rows_affected = int(result.split()[-1])
                    return rows_affected > 0
                    
        except asyncpg.PostgresError as e:
            print(f"Database error deleting API key: {str(e)}")
            raise Exception(f"Failed to delete API key: {str(e)}")
        except Exception as e:
            print(f"Error deleting API key: {str(e)}")
            raise

    @staticmethod
    async def validate_api_key(api_key: str, db_pool: asyncpg.Pool) -> Optional[Dict[str, Any]]:
        """
        Validate an API key and return client information if valid.
        
        Args:
            api_key (str): The API key to validate
            db_pool (asyncpg.Pool): Database connection pool
            
        Returns:
            Optional[Dict[str, Any]]: Client information if valid, None if invalid
            
        Raises:
            Exception: If database operation fails
        """
        try:
            async with db_pool.acquire() as conn:
                async with conn.transaction():
                    # Find the API key and associated client
                    result = await conn.fetchrow(
                        """SELECT ak.client_id, ak.api_key_id, cu.company_name, cu.email, cu.is_verified
                           FROM api_keys ak
                           JOIN client_users cu ON ak.client_id = cu.id
                           WHERE ak.api_key_hash = $1 AND ak.is_active = TRUE AND cu.is_verified = TRUE""",
                        api_key
                    )
                    
                    if result:
                        # Update last_used_at timestamp
                        await conn.execute(
                            """UPDATE api_keys 
                               SET last_used_at = $1 
                               WHERE api_key_hash = $2""",
                            datetime.now(), api_key
                        )
                        
                        return {
                            "client_id": result["client_id"],
                            "api_key_id": result["api_key_id"],
                            "company_name": result["company_name"],
                            "email": result["email"],
                            "is_verified": result["is_verified"]
                        }
                    
                    return None
                    
        except asyncpg.PostgresError as e:
            print(f"Database error validating API key: {str(e)}")
            raise Exception(f"Failed to validate API key: {str(e)}")
        except Exception as e:
            print(f"Error validating API key: {str(e)}")
            raise