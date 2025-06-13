from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class ApiKeyResponse(BaseModel):
    """Schema for API key creation response"""
    api_key_id: str
    api_key: str
    created_at: datetime

    class Config:
        from_attributes = True

class ApiKeyInfo(BaseModel):
    """Schema for API key information (masked)"""
    api_key_id: str
    masked_api_key: str
    created_at: datetime
    last_used_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ApiKeyListResponse(BaseModel):
    """Schema for API key list response"""
    api_keys: List[ApiKeyInfo]
    total_count: int

class ApiKeyDelete(BaseModel):
    """Schema for API key deletion response"""
    message: str