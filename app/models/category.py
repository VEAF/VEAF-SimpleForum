
from pydantic import BaseModel, Field


class CategorySummary(BaseModel):
    id: int
    name: str
    slug: str
    parent_cid: int = Field(default=0, description="Parent category ID, 0 for root")
    icon: str | None = None
    bgColor: str | None = None
    color: str | None = None
    order: int = 0
    disabled: bool = False
    is_subcategory: bool = False
    topic_count: int = 0
    post_count: int = 0


class CategoryDetail(CategorySummary):
    subcategories: list["CategorySummary"] = []


class CategoryTree(CategorySummary):
    children: list["CategoryTree"] = []
