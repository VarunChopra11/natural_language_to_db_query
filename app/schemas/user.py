from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class ClientUserCreate(BaseModel):
    company_name: str
    email: EmailStr

class ClientUserLogin(BaseModel):
    email: EmailStr

class ClientUserResponse(BaseModel):
    id: int
    company_name: str
    email: EmailStr
    is_verified: bool

class EndUserCreate(BaseModel):
    wallet_address: str = Field(..., min_length=10, max_length=100, description="Wallet address of the end user")
    email: Optional[EmailStr] = Field(None, description="Email address of the end user")

class EndUserResponse(BaseModel):
    id: int
    client_id: int
    wallet_address: str
    email: Optional[str]
    created_at: str
    message: str

class EndUserSimpleResponse(BaseModel):
    id: int
    client_id: int
    wallet_address: str
    email: Optional[str]

class TokenData(BaseModel):
    email: str

class ErrorResponse(BaseModel):
    error: str
    message: str