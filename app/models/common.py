from typing import Generic, TypeVar, List, Optional
from pydantic import BaseModel

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int = 1
    page_size: int = 20
    total_pages: int


class ExportInfo(BaseModel):
    total_users: int
    total_categories: int
    total_topics: int
    total_posts: int


class ErrorResponse(BaseModel):
    detail: str
    code: Optional[str] = None
