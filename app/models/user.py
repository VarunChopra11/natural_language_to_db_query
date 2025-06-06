from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.db import Base

class ClientUser(Base):
    __tablename__ = "client_users"
    
    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String(100), unique=True)
    email = Column(String(100), unique=True, index=True)
    api_key = Column(String(100), unique=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class EndUser(Base):
    __tablename__ = "end_users"
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("client_users.id"))
    wallet_address = Column(String(100), unique=True)
    email = Column(String(100), index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())