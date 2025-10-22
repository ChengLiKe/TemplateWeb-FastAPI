# app/services/auth.py
from typing import List, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel

from app.utils import get_logger, kv

auth_logger = get_logger("AUTH")


class User(BaseModel):
    id: int
    username: str
    scopes: List[str] = []


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


def decode_token(token: str) -> Optional[User]:
    # Skeleton: replace with real JWT verification later
    if token == "demo-token":
        user = User(id=1, username="demo", scopes=["read", "write"])
        auth_logger.info("Token decoded " + kv(valid=True, user=user.username))
        return user
    auth_logger.warning("Token decoded " + kv(valid=False))
    return None


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    user = decode_token(token)
    if not user:
        # Raise 401, unified error handler will format response
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "E_AUTH_FAILED", "message": "Invalid or expired token"},
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user