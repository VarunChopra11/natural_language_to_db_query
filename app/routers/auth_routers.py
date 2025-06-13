from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import RedirectResponse
from jose import jwt, JWTError
from datetime import timedelta
import asyncpg
import os

from app.services.auth_services import (
    create_access_token,
    create_verification_token,
    send_verification_email,
    SECRET_KEY,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    get_current_client
)
from app.db.db import get_connection
from app.schemas.user import ClientUserCreate, ClientUserLogin, ClientUserResponse

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@router.post("/signup", response_model=ClientUserResponse)
async def signup(user: ClientUserCreate, request: Request, db_pool: asyncpg.Pool = Depends(get_connection)):
    async with db_pool.acquire() as conn:
        existing_user = await conn.fetchrow(
            "SELECT email FROM client_users WHERE email = $1",
            user.email
        )
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")

        try:
            async with conn.transaction():
                new_user = await conn.fetchrow(
                    """INSERT INTO client_users (company_name, email)
                       VALUES ($1, $2)
                       RETURNING id, company_name, email, is_verified, created_at""",
                    user.company_name, user.email
                )
        except asyncpg.UniqueViolationError:
            raise HTTPException(status_code=400, detail="Email already registered")
        try:
            verification_token = create_verification_token(new_user["email"])
            base_url = str(request.base_url)
            verification_url = f"{base_url}auth/verify-email?token={verification_token}"
            await send_verification_email(new_user["email"], user.company_name, verification_url)
        except Exception as e:
            print(f"Error sending email: {e}")
            raise HTTPException(status_code=500, detail="Failed to send verification email")

        return ClientUserResponse(**new_user)

@router.post("/login")
async def login(user: ClientUserLogin, request: Request, db_pool: asyncpg.Pool = Depends(get_connection)):
    async with db_pool.acquire() as conn:
        db_user = await conn.fetchrow(
            "SELECT email, company_name, is_verified FROM client_users WHERE email = $1",
            user.email
        )

        if not db_user:
            raise HTTPException(status_code=404, detail="User not found")

        try:
            verification_token = create_verification_token(db_user["email"])
            base_url = str(request.base_url)
            verification_url = f"{base_url}auth/verify-email?token={verification_token}"
            await send_verification_email(db_user["email"], db_user["company_name"], verification_url)
        except Exception as e:
            print(f"Error sending email: {e}")
            raise HTTPException(status_code=500, detail="Failed to send verification email")

        return {"message": "Verification email sent"}

@router.get("/verify-email")
async def verify_email(token: str, pool=Depends(get_connection)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=400, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token expired or invalid")

    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute(
                """UPDATE client_users 
                   SET is_verified = TRUE 
                   WHERE email = $1 AND is_verified = FALSE""",
                email
            )

            access_token = create_access_token(
                {"sub": email},
                timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            )

            frontend_url = os.getenv("FRONTEND_URL")
            response = RedirectResponse(url=frontend_url)
            response.set_cookie(
                key="token",
                value=access_token,
                httponly=True,
                max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                secure=True,
                samesite="none",
                domain=".helqor.tech",
            )
            return response
        
@router.get("/get-current-client")
async def get_current_client_endpoint(user: dict = Depends(get_current_client)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user

@router.post("/logout")
async def logout():
    response = Response(content="Logged out successfully")
    response.delete_cookie("token")
    return response
