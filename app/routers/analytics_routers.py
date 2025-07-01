from fastapi import APIRouter, Query
from app.services.analytics_services import (
    get_transactions_per_hour,
    get_top_miners,
    get_average_gas_used,
    get_top_withdrawal_addresses
)

router = APIRouter()

@router.get("/analytics/transactions-per-hour")
async def transactions_per_hour(
    range: str = Query(..., description="Time range: 7d, 1m, or 1y")
):
    return await get_transactions_per_hour(range)

@router.get("/analytics/top-miners")
async def top_miners():
    return await get_top_miners()

@router.get("/analytics/average-gas-used")
async def average_gas_used(
    days: int = Query(7, description="Number of days to analyze")
):
    return await get_average_gas_used(days)

@router.get("/analytics/top-withdrawal-addresses")
async def top_withdrawal_addresses():
    return await get_top_withdrawal_addresses()