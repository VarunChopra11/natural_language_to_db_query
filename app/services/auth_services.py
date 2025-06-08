from fastapi import Depends, HTTPException, status
from datetime import datetime, timedelta, timezone
from fastapi.security import APIKeyHeader
from app.config import SECRET_KEY, GMAIL_ADDRESS, GMAIL_APP_PASSWORD
from app.db.db import get_connection
from jose import JWTError, jwt
from typing import Optional
import asyncpg
import asyncio

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib

api_key_scheme = APIKeyHeader(name="Authorization")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
VERIFICATION_TOKEN_EXPIRE_MINUTES = 1

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_verification_token(email: str):
    return create_access_token(
        {"sub": email},
        timedelta(minutes=VERIFICATION_TOKEN_EXPIRE_MINUTES)
    )

async def get_current_client(
    token: str = Depends(api_key_scheme),
    conn: asyncpg.Connection = Depends(get_connection)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = await conn.fetchrow(
        "SELECT id, company_name, email, is_verified FROM client_users WHERE email = $1",
        email
    )
    if user is None or not user["is_verified"]:
        raise credentials_exception

    return user

def send_email(recipient_email, subject, plain_body, html_body=None):
    try:
        msg = MIMEMultipart('alternative')
        msg['From'] = GMAIL_ADDRESS
        msg['To'] = recipient_email
        msg['Subject'] = subject

        msg.attach(MIMEText(plain_body, 'plain'))
        if html_body:
            msg.attach(MIMEText(html_body, 'html'))

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_ADDRESS, recipient_email, msg.as_string())
    except Exception as e:
        print(f"Error sending mail: {e}")
        raise

async def send_verification_email(email: str, company_name: str, verification_link: str):
    plain_content = f"""Hi {company_name},
Thank you for signing up with our monitoring service.
Please verify your email address by clicking: {verification_link}
If you didn't request this, ignore this email.
Best,
Crypto Monitoring Team"""

    html_content = f"""
    <html>
        <body>
            <p>Hi {company_name},</p>
            <p>Thank you for signing up with our monitoring service.</p>
            <p>
                Please verify your email:<br>
                <a href="{verification_link}">{verification_link}</a>
            </p>
            <p>If you didn't request this, ignore this email.</p>
            <p>Best,<br>Crypto Monitoring Team</p>
        </body>
    </html>
    """

    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: send_email(
                email,
                "Verify your Crypto Monitoring Account",
                plain_content,
                html_content
            )
        )
    except Exception as e:
        print(f"Error sending verification email: {e}")
        raise