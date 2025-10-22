# app/api/auth.py
from fastapi import APIRouter
from pydantic import BaseModel

from app.utils import get_logger, kv

auth_router = APIRouter(prefix="/auth", tags=["Auth"])
app_logger = get_logger("APP")


class TokenRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@auth_router.post("/token", response_model=TokenResponse)
async def issue_token(body: TokenRequest) -> TokenResponse:
    # Skeleton: always return demo token; replace with real auth later
    app_logger.info("Issue token " + kv(user=body.username))
    return TokenResponse(access_token="demo-token")