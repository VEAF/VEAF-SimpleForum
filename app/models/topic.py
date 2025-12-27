from datetime import datetime

from pydantic import BaseModel


class TopicSummary(BaseModel):
    topic_id: int
    title: str
    author_id: int
    category_id: int
    created: datetime
    deleted: bool = False
    locked: bool = False
    pinned: bool = False
    post_count: int = 0
    rating: int = 0
    view_count: int = 0
    tags: list[str] = []
    last_post: datetime | None = None
    slug: str = ""


class TopicDetail(TopicSummary):
    content: str = ""
    content_html: str = ""
