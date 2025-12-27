import pytest
import tempfile
import shutil
from pathlib import Path
from typing import Generator

from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.services import data_loader
from app.routers import web as web_router
from app.routers import api as api_router
from app.config import settings


@pytest.fixture(scope="session")
def test_data_dir() -> Generator[Path, None, None]:
    """Create a temporary directory with test data."""
    temp_dir = Path(tempfile.mkdtemp())

    # Create category structure
    cat_dir = temp_dir / "1-test-category"
    cat_dir.mkdir(parents=True)

    sub_cat_dir = cat_dir / "2-test-subcategory"
    sub_cat_dir.mkdir(parents=True)

    images_dir = temp_dir / "images"
    images_dir.mkdir(parents=True)

    # Create _export.yml
    export_yml = temp_dir / "_export.yml"
    export_yml.write_text("""
categories:
  - id: 1
    name: Test Category
    parent_cid: 0
    slug: 1/test-category
  - id: 2
    name: Test Subcategory
    parent_cid: 1
    slug: 2/test-subcategory
export_info:
  total_users: 10
  total_categories: 2
  total_topics: 3
  total_posts: 15
""")

    # Create category metadata
    cat_yml = cat_dir / "_category.yml"
    cat_yml.write_text("""
id: 1
name: Test Category
slug: 1/test-category
parent_cid: 0
icon: fa-folder
bgColor: "#3498db"
color: "#ffffff"
order: 1
disabled: false
is_subcategory: false
postcount: 10
topiccount: 2
""")

    sub_cat_yml = sub_cat_dir / "_category.yml"
    sub_cat_yml.write_text("""
id: 2
name: Test Subcategory
slug: 2/test-subcategory
parent_cid: 1
icon: fa-file
bgColor: "#2ecc71"
color: "#ffffff"
order: 1
disabled: false
is_subcategory: true
postcount: 5
topiccount: 1
""")

    # Create topic files
    topic1 = cat_dir / "100-first-test-topic.md"
    topic1.write_text("""---
author_id: 1
category_id: 1
created: '2024-01-15T10:30:00.000000'
deleted: false
last_post: '2024-01-16T14:00:00.000000'
locked: false
pinned: true
post_count: 5
rating: 3
tags:
  - test
  - important
title: First Test Topic
topic_id: 100
view_count: 150
---

# First Test Topic

This is the content of the first test topic.

## Section 1

Some **bold** text and *italic* text.

- Item 1
- Item 2
- Item 3
""")

    topic2 = cat_dir / "101-second-test-topic.md"
    topic2.write_text("""---
author_id: 2
category_id: 1
created: '2024-01-10T08:00:00.000000'
deleted: false
last_post: '2024-01-12T09:30:00.000000'
locked: true
pinned: false
post_count: 3
rating: 1
tags: []
title: Second Test Topic
topic_id: 101
view_count: 50
---

# Second Test Topic

Content of the second topic.
""")

    topic3 = sub_cat_dir / "102-subcategory-topic.md"
    topic3.write_text("""---
author_id: 1
category_id: 2
created: '2024-01-20T12:00:00.000000'
deleted: false
last_post: '2024-01-21T16:00:00.000000'
locked: false
pinned: false
post_count: 7
rating: 5
tags:
  - training
title: Subcategory Topic
topic_id: 102
view_count: 200
---

# Subcategory Topic

This topic belongs to a subcategory.
""")

    # Create a test image
    test_image = images_dir / "test.jpg"
    test_image.write_bytes(b'\xff\xd8\xff\xe0\x00\x10JFIF')

    yield temp_dir

    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture(scope="session")
def test_data_store(test_data_dir: Path):
    """Create a DataStore with test data."""
    store = data_loader.DataStore(test_data_dir)
    store.load_all()
    return store


@pytest.fixture
def mock_data_store(test_data_store, monkeypatch):
    """Replace the global data store with test data store."""
    monkeypatch.setattr(data_loader, "data_store", test_data_store)

    def mock_get_data_store():
        return test_data_store

    def mock_init_data_store():
        return test_data_store

    monkeypatch.setattr(data_loader, "get_data_store", mock_get_data_store)
    monkeypatch.setattr(data_loader, "init_data_store", mock_init_data_store)

    # Reset search service caches in routers
    monkeypatch.setattr(web_router, "_search_service", None)
    monkeypatch.setattr(api_router, "_search_service", None)

    return test_data_store


@pytest.fixture
def client(mock_data_store) -> TestClient:
    """Create a test client for synchronous tests."""
    return TestClient(app)


@pytest.fixture
async def async_client(mock_data_store) -> AsyncClient:
    """Create an async test client for async tests."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def real_data_store():
    """Create a DataStore with real data (for e2e tests)."""
    if not settings.DATA_PATH.exists():
        pytest.skip("Real data not available")
    store = data_loader.DataStore(settings.DATA_PATH)
    store.load_all()
    return store


@pytest.fixture
def real_client(real_data_store, monkeypatch) -> TestClient:
    """Create a test client with real data (for e2e tests)."""
    monkeypatch.setattr(data_loader, "data_store", real_data_store)

    def mock_get_data_store():
        return real_data_store

    def mock_init_data_store():
        return real_data_store

    monkeypatch.setattr(data_loader, "get_data_store", mock_get_data_store)
    monkeypatch.setattr(data_loader, "init_data_store", mock_init_data_store)

    # Reset search service caches in routers
    monkeypatch.setattr(web_router, "_search_service", None)
    monkeypatch.setattr(api_router, "_search_service", None)

    return TestClient(app)
