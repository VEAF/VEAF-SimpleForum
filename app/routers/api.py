from typing import Any

from fastapi import APIRouter, HTTPException, Query

from app.models.category import CategoryDetail, CategorySummary, CategoryTree
from app.models.common import ExportInfo, PaginatedResponse
from app.models.topic import TopicDetail, TopicSummary
from app.services.data_loader import get_data_store
from app.services.search import SearchService

router = APIRouter(prefix="/api/v1")

_search_service: SearchService | None = None


def parse_id_from_path(path: str) -> int:
    """Extract ID from path like '20/some-slug', '20-some-slug' (legacy), or '20'."""
    # Nouveau format: id/slug
    if "/" in path:
        return int(path.split("/", 1)[0])
    # Ancien format (legacy): id-slug
    if "-" in path:
        return int(path.split("-", 1)[0])
    # ID seul
    return int(path)


def get_search_service() -> SearchService:
    global _search_service
    if _search_service is None:
        _search_service = SearchService(get_data_store())
    return _search_service


@router.get("/info", response_model=ExportInfo)
async def get_info() -> ExportInfo:
    store = get_data_store()
    info = store.export_info
    return ExportInfo(
        total_users=info.get("total_users", 0),
        total_categories=info.get("total_categories", 0),
        total_topics=info.get("total_topics", 0),
        total_posts=info.get("total_posts", 0),
    )


@router.get("/categories", response_model=list[CategorySummary])
async def list_root_categories() -> list[CategorySummary]:
    store = get_data_store()
    categories = store.get_root_categories()
    return [
        CategorySummary(
            id=c["id"],
            name=c["name"],
            slug=c.get("slug", ""),
            parent_cid=c.get("parent_cid", 0),
            icon=c.get("icon"),
            bgColor=c.get("bgColor"),
            color=c.get("color"),
            order=c.get("order", 0),
            disabled=c.get("disabled", False),
            is_subcategory=c.get("is_subcategory", False),
            topic_count=len(store.category_topics.get(c["id"], [])),
            post_count=c.get("postcount", 0),
        )
        for c in categories
    ]


@router.get("/categories/tree", response_model=list[CategoryTree])
async def get_category_tree() -> list[CategoryTree]:
    store = get_data_store()

    def build_tree(cat_data: dict[str, Any]) -> CategoryTree:
        return CategoryTree(
            id=cat_data["id"],
            name=cat_data["name"],
            slug=cat_data.get("slug", ""),
            parent_cid=cat_data.get("parent_cid", 0),
            icon=cat_data.get("icon"),
            bgColor=cat_data.get("bgColor"),
            color=cat_data.get("color"),
            order=cat_data.get("order", 0),
            disabled=cat_data.get("disabled", False),
            is_subcategory=cat_data.get("is_subcategory", False),
            topic_count=len(store.category_topics.get(cat_data["id"], [])),
            post_count=cat_data.get("postcount", 0),
            children=[build_tree(child) for child in cat_data.get("children", [])],
        )

    tree_data = store.build_category_tree(0)
    return [build_tree(c) for c in tree_data]


@router.get(
    "/categories/{category_path:path}/topics",
    response_model=PaginatedResponse[TopicSummary],
)
async def list_category_topics(
    category_path: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("created", pattern="^(created|last_post|view_count|rating)$"),
    order: str = Query("desc", pattern="^(asc|desc)$"),
) -> PaginatedResponse[TopicSummary]:
    try:
        category_id = parse_id_from_path(category_path)
    except (ValueError, IndexError):
        raise HTTPException(status_code=404, detail="Category not found") from None

    store = get_data_store()
    if category_id not in store.categories:
        raise HTTPException(status_code=404, detail="Category not found")

    topics, total = store.get_category_topics(
        category_id, page, page_size, sort_by, order
    )
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1

    return PaginatedResponse(
        items=[
            TopicSummary(
                topic_id=t["topic_id"],
                title=t["title"],
                author_id=t["author_id"],
                category_id=t["category_id"],
                created=t["created"],
                deleted=t.get("deleted", False),
                locked=t.get("locked", False),
                pinned=t.get("pinned", False),
                post_count=t.get("post_count", 0),
                rating=t.get("rating", 0),
                view_count=t.get("view_count", 0),
                tags=t.get("tags", []),
                last_post=t.get("last_post"),
                slug=t.get("slug", ""),
            )
            for t in topics
        ],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/categories/{category_path:path}", response_model=CategoryDetail)
async def get_category(category_path: str) -> CategoryDetail:
    try:
        category_id = parse_id_from_path(category_path)
    except (ValueError, IndexError):
        raise HTTPException(status_code=404, detail="Category not found") from None

    store = get_data_store()
    cat = store.get_category(category_id)
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")

    subcategories = store.get_subcategories(category_id)

    return CategoryDetail(
        id=cat["id"],
        name=cat["name"],
        slug=cat.get("slug", ""),
        parent_cid=cat.get("parent_cid", 0),
        icon=cat.get("icon"),
        bgColor=cat.get("bgColor"),
        color=cat.get("color"),
        order=cat.get("order", 0),
        disabled=cat.get("disabled", False),
        is_subcategory=cat.get("is_subcategory", False),
        topic_count=len(store.category_topics.get(cat["id"], [])),
        post_count=cat.get("postcount", 0),
        subcategories=[
            CategorySummary(
                id=s["id"],
                name=s["name"],
                slug=s.get("slug", ""),
                parent_cid=s.get("parent_cid", 0),
                icon=s.get("icon"),
                bgColor=s.get("bgColor"),
                color=s.get("color"),
                order=s.get("order", 0),
                disabled=s.get("disabled", False),
                is_subcategory=s.get("is_subcategory", False),
                topic_count=len(store.category_topics.get(s["id"], [])),
                post_count=s.get("postcount", 0),
            )
            for s in subcategories
        ],
    )


@router.get("/topics", response_model=PaginatedResponse[TopicSummary])
async def list_all_topics(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("created", pattern="^(created|last_post|view_count|rating)$"),
    order: str = Query("desc", pattern="^(asc|desc)$"),
) -> PaginatedResponse[TopicSummary]:
    store = get_data_store()
    topics, total = store.get_all_topics(page, page_size, sort_by, order)
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1

    return PaginatedResponse(
        items=[
            TopicSummary(
                topic_id=t["topic_id"],
                title=t["title"],
                author_id=t["author_id"],
                category_id=t["category_id"],
                created=t["created"],
                deleted=t.get("deleted", False),
                locked=t.get("locked", False),
                pinned=t.get("pinned", False),
                post_count=t.get("post_count", 0),
                rating=t.get("rating", 0),
                view_count=t.get("view_count", 0),
                tags=t.get("tags", []),
                last_post=t.get("last_post"),
                slug=t.get("slug", ""),
            )
            for t in topics
        ],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/topics/{topic_path:path}", response_model=TopicDetail)
async def get_topic(topic_path: str) -> TopicDetail:
    try:
        topic_id = parse_id_from_path(topic_path)
    except (ValueError, IndexError):
        raise HTTPException(status_code=404, detail="Topic not found") from None

    store = get_data_store()
    topic = store.get_topic(topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    return TopicDetail(
        topic_id=topic["topic_id"],
        title=topic["title"],
        author_id=topic["author_id"],
        category_id=topic["category_id"],
        created=topic["created"],
        deleted=topic.get("deleted", False),
        locked=topic.get("locked", False),
        pinned=topic.get("pinned", False),
        post_count=topic.get("post_count", 0),
        rating=topic.get("rating", 0),
        view_count=topic.get("view_count", 0),
        tags=topic.get("tags", []),
        last_post=topic.get("last_post"),
        slug=topic.get("slug", ""),
        content=topic.get("content", ""),
        content_html=topic.get("content_html", ""),
    )


@router.get("/search", response_model=list[TopicSummary])
async def search_topics(
    q: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=100),
) -> list[TopicSummary]:
    search_service = get_search_service()
    results = search_service.search(q, limit)

    return [
        TopicSummary(
            topic_id=t["topic_id"],
            title=t["title"],
            author_id=t["author_id"],
            category_id=t["category_id"],
            created=t["created"],
            deleted=t.get("deleted", False),
            locked=t.get("locked", False),
            pinned=t.get("pinned", False),
            post_count=t.get("post_count", 0),
            rating=t.get("rating", 0),
            view_count=t.get("view_count", 0),
            tags=t.get("tags", []),
            last_post=t.get("last_post"),
            slug=t.get("slug", ""),
        )
        for t in results
    ]
