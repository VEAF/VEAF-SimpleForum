from fastapi import APIRouter, Request, Query, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path

from app.services.data_loader import get_data_store
from app.services.search import SearchService

router = APIRouter()
templates = Jinja2Templates(directory=Path(__file__).parent.parent / "templates")

_search_service = None


def parse_id_from_path(path: str) -> int:
    """Extract ID from path like '20-some-slug' or '20'."""
    parts = path.split("-", 1)
    return int(parts[0])


def get_category_url_slug(category: dict) -> str:
    """Get URL slug for category (id-slug-text)."""
    slug = category.get("slug", "")
    slug_part = slug.split("/")[-1] if "/" in slug else slug
    return f"{category['id']}-{slug_part}" if slug_part else str(category["id"])


def get_topic_url_slug(topic: dict) -> str:
    """Get URL slug for topic. The slug is the filename stem which already contains id-title."""
    slug = topic.get("slug", "")
    if slug:
        return slug
    return str(topic["topic_id"])


def get_search_service() -> SearchService:
    global _search_service
    if _search_service is None:
        _search_service = SearchService(get_data_store())
    return _search_service


@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    store = get_data_store()
    category_tree = store.build_category_tree(0)
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "categories": category_tree,
            "export_info": store.export_info,
            "get_category_url_slug": get_category_url_slug,
        },
    )


@router.get("/category/{category_path:path}", response_model=None)
async def category_page(
    request: Request,
    category_path: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    try:
        category_id = parse_id_from_path(category_path)
    except (ValueError, IndexError):
        raise HTTPException(status_code=404, detail="Category not found")

    store = get_data_store()
    category = store.get_category(category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    canonical_path = get_category_url_slug(category)
    if category_path != canonical_path:
        query = str(request.query_params)
        url = f"/category/{canonical_path}"
        if query:
            url += f"?{query}"
        return RedirectResponse(url=url, status_code=301)

    topics, total = store.get_category_topics(category_id, page, page_size)
    subcategories = store.get_subcategories(category_id)
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1

    breadcrumbs = []
    current_cat = category
    while current_cat:
        breadcrumbs.insert(0, current_cat)
        parent_cid = current_cat.get("parent_cid", 0)
        if parent_cid == 0:
            break
        current_cat = store.get_category(parent_cid)

    return templates.TemplateResponse(
        "category.html",
        {
            "request": request,
            "category": category,
            "subcategories": subcategories,
            "topics": topics,
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": total_pages,
            "breadcrumbs": breadcrumbs,
            "get_category_url_slug": get_category_url_slug,
            "get_topic_url_slug": get_topic_url_slug,
        },
    )


@router.get("/topic/{topic_path:path}", response_model=None)
async def topic_page(
    request: Request,
    topic_path: str,
):
    try:
        topic_id = parse_id_from_path(topic_path)
    except (ValueError, IndexError):
        raise HTTPException(status_code=404, detail="Topic not found")

    store = get_data_store()
    topic = store.get_topic(topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    canonical_path = get_topic_url_slug(topic)
    if topic_path != canonical_path:
        return RedirectResponse(url=f"/topic/{canonical_path}", status_code=301)

    category = store.get_category(topic.get("category_id"))

    breadcrumbs = []
    current_cat = category
    while current_cat:
        breadcrumbs.insert(0, current_cat)
        parent_cid = current_cat.get("parent_cid", 0)
        if parent_cid == 0:
            break
        current_cat = store.get_category(parent_cid)

    return templates.TemplateResponse(
        "topic.html",
        {
            "request": request,
            "topic": topic,
            "category": category,
            "breadcrumbs": breadcrumbs,
            "get_category_url_slug": get_category_url_slug,
            "get_topic_url_slug": get_topic_url_slug,
        },
    )


@router.get("/search", response_class=HTMLResponse)
async def search_page(
    request: Request,
    q: str = Query("", min_length=0),
):
    results = []
    if q:
        search_service = get_search_service()
        results = search_service.search(q, limit=50)

    return templates.TemplateResponse(
        "search.html",
        {
            "request": request,
            "query": q,
            "results": results,
            "total": len(results),
            "get_topic_url_slug": get_topic_url_slug,
        },
    )
