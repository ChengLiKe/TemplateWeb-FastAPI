# app/models/response.py
from typing import Any, Generic, Optional, TypeVar
from pydantic import BaseModel

T = TypeVar("T")


class PaginationMeta(BaseModel):
    total: int
    page: int
    page_size: int
    has_next: bool


class SuccessResponse(BaseModel, Generic[T]):
    code: str = "OK"
    message: str = "success"
    data: Optional[T] = None
    meta: Optional[PaginationMeta] = None


class ErrorResponse(BaseModel):
    code: str
    message: str
    detail: Optional[Any] = None