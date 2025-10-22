# app/models/pagination.py
from typing import Optional, Literal
from pydantic import BaseModel, Field

from app.models.response import PaginationMeta


class PageQuery(BaseModel):
    page: int = Field(default=1, ge=1, description="Page number starts from 1")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page (1-100)")
    sort_by: Optional[str] = Field(default=None, description="Field to sort by")
    order: Literal["asc", "desc"] = Field(default="asc", description="Sort order")

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        return self.page_size

    def to_meta(self, total: int) -> PaginationMeta:
        has_next = self.page * self.page_size < total
        return PaginationMeta(total=total, page=self.page, page_size=self.page_size, has_next=has_next)