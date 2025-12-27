from typing import Optional, List
from pydantic import BaseModel, Field


class CategorySummary(BaseModel):
    id: int
    name: str
    slug: str
    parent_cid: int = Field(default=0, description="Parent category ID, 0 for root")
    icon: Optional[str] = None
    bgColor: Optional[str] = None
    color: Optional[str] = None
    order: int = 0
    disabled: bool = False
    is_subcategory: bool = False
    topic_count: int = 0
    post_count: int = 0


class CategoryDetail(CategorySummary):
    subcategories: List["CategorySummary"] = []


class CategoryTree(CategorySummary):
    children: List["CategoryTree"] = []
