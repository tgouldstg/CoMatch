from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from hmac import compare_digest

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

ALGORITHM = "HS256"
TOKEN_TTL_HOURS = int(os.getenv("APP_AUTH_TOKEN_TTL_HOURS", "24"))

security = HTTPBearer(auto_error=False)


def _auth_secret() -> str:
    secret = os.getenv("APP_AUTH_SECRET", "")
    if not secret:
        # Dev fallback; set APP_AUTH_SECRET in production
        secret = "dev-change-this-secret"
    return secret


def _username() -> str:
    return os.getenv("APP_AUTH_USERNAME", "admin")


def _password() -> str:
    # Dev fallback; set APP_AUTH_PASSWORD in production
    return os.getenv("APP_AUTH_PASSWORD", "change-me-now")


def authenticate(username: str, password: str) -> bool:
    return compare_digest(username, _username()) and compare_digest(password, _password())


def create_token(username: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": username,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=TOKEN_TTL_HOURS)).timestamp()),
    }
    return jwt.encode(payload, _auth_secret(), algorithm=ALGORITHM)


def verify_token(token: str) -> dict:
    try:
        return jwt.decode(token, _auth_secret(), algorithms=[ALGORITHM])
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")


def require_user(credentials: HTTPAuthorizationCredentials | None = Depends(security)) -> dict:
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    claims = verify_token(credentials.credentials)
    return {"username": claims.get("sub", "unknown")}
