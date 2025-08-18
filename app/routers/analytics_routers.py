from fastapi import APIRouter, Depends, Query, HTTPException
from app.services.analytics_services import (
    get_client_portfolio_summary,
    get_client_token_distribution,
    get_client_app_summary,
    get_client_nft_summary,
    get_client_transaction_activity
)
from app.services.auth_services import get_current_client  # Updated import
import httpx  # <-- Added import

router = APIRouter()

# Removed old get_client_id dependency

@router.get("/analytics/portfolio-summary")
async def portfolio_summary(user: dict = Depends(get_current_client)):
    return await get_client_portfolio_summary(user["id"])

@router.get("/analytics/token-distribution")
async def token_distribution(user: dict = Depends(get_current_client)):
    return await get_client_token_distribution(user["id"])

@router.get("/analytics/app-summary")
async def app_summary(user: dict = Depends(get_current_client)):
    return await get_client_app_summary(user["id"])

@router.get("/analytics/nft-summary")
async def nft_summary(user: dict = Depends(get_current_client)):
    return await get_client_nft_summary(user["id"])

@router.get("/analytics/transaction-activity")
async def transaction_activity(
    user: dict = Depends(get_current_client),
    range: str = Query("7d", description="Time range: 7d, 1m, or 1y")
):
    if range not in ["7d", "1m", "1y"]:
        raise HTTPException(status_code=400, detail="Invalid range. Use '7d', '1m', or '1y'")
    return await get_client_transaction_activity(user["id"], range)

@router.get("/analytics/last-analytics")
async def last_analytics():
    url = "https://scrapper.helqor.tech/last-analytics"
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
    response.raise_for_status()  # Raise an error if the request failed
    return response.json()
