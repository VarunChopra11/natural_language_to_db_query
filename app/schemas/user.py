from pydantic import BaseModel, EmailStr
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
    wallet_address: str
    email: Optional[EmailStr] = None

class EndUserResponse(BaseModel):
    id: int
    client_id: int
    wallet_address: str
    email: Optional[str]

class TokenData(BaseModel):
    email: str