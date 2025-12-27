from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import settings
from app.services.data_loader import init_data_store
from app.routers import web, api


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_data_store()
    yield


app = FastAPI(
    title="VEAF Community",
    description="Web interface to display old forum content",
    version="1.0.0",
    lifespan=lifespan,
)

static_path = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=static_path), name="static")

if settings.IMAGES_PATH.exists():
    app.mount("/images", StaticFiles(directory=settings.IMAGES_PATH), name="images")

app.include_router(api.router)
app.include_router(web.router)

templates = Jinja2Templates(directory=Path(__file__).parent / "templates")


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 404:
        accept = request.headers.get("accept", "")
        if "application/json" in accept:
            return JSONResponse(
                status_code=404,
                content={"detail": exc.detail}
            )
        return templates.TemplateResponse(
            request,
            "404.html",
            status_code=404
        )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )


@app.get("/health")
async def health_check():
    from app.services.data_loader import get_data_store
    store = get_data_store()
    return {
        "status": "healthy",
        "topics_loaded": len(store.topics),
        "categories_loaded": len(store.categories),
    }
