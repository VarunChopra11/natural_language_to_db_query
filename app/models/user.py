from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db import Base

class ClientUser(Base):
    __tablename__ = "client_users"
    
    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String(100), unique=True)
    email = Column(String(100), unique=True, index=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship to API keys
    api_keys = relationship("ApiKey", back_populates="client", cascade="all, delete-orphan")

class EndUser(Base):
    __tablename__ = "end_users"
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("client_users.id"))
    wallet_address = Column(String(100), unique=True)
    email = Column(String(100), index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ApiKey(Base):
    __tablename__ = "api_keys"
    
    id = Column(Integer, primary_key=True, index=True)
    api_key_id = Column(String(100), unique=True, index=True)
    client_id = Column(Integer, ForeignKey("client_users.id"), index=True)
    api_key_hash = Column(String(100), unique=True, index=True)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_used_at = Column(DateTime(timezone=True))

    # Relationship to client
    client = relationship("ClientUser", back_populates="api_keys")