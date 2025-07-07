from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class TokenBalance(BaseModel):
    symbol: str
    token_address: str
    balance: float
    balance_usd: float
    price: float
    img_url: Optional[str] = None
    name: str
    network: str

class PortfolioV2(BaseModel):
    total_balance_usd: float
    tokens: List[TokenBalance]

class MetaTypeBalance(BaseModel):
    meta_type: str  # e.g., "SUPPLIED", "BORROWED"
    position_count: int
    balance_usd: float

class AppBalances(BaseModel):
    by_meta_type: List[MetaTypeBalance]

class NFTAsset(BaseModel):
    token_id: str
    name: str
    collection_address: str
    estimated_value: Optional[float] = None
    img_url: Optional[str] = None
    network: str

class Transaction(BaseModel):
    tx_hash: str
    block_number: int
    timestamp: datetime
    from_address: str
    to_address: Optional[str] = None
    network: str
    method_signature: Optional[str] = None
    method_sighash: Optional[str] = None
    processed_description: Optional[str] = None
    description: Optional[str] = None
    value_usd: Optional[float] = None
    value_eth: Optional[float] = None

class FinancialProfile(BaseModel):
    wallet_address: str
    portfolio: PortfolioV2
    app_balances: AppBalances
    nft_assets: List[NFTAsset]
    transactions: List[Transaction]