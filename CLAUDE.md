# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

VEAF Community Forum - A FastAPI web application that serves archived NodeBB forum content as both an HTML interface and a REST API. The forum data consists of Markdown files with YAML frontmatter stored in `var/data/`.

## Commands

```bash
# Install dependencies
poetry install
poetry install --with dev  # Include test dependencies

# Run development server (with hot reload)
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Run tests
poetry run pytest                                    # All tests
poetry run pytest -v                                 # Verbose
poetry run pytest tests/unit/                        # Unit tests only
poetry run pytest tests/integration/                 # Integration tests only
poetry run pytest tests/e2e/                         # End-to-end tests only
poetry run pytest tests/unit/test_models.py -v      # Single file
poetry run pytest -k "test_search"                   # Tests matching pattern
poetry run pytest --cov=app --cov-report=term-missing  # With coverage
```

## Architecture

### Data Flow
1. **Startup**: `init_data_store()` loads all Markdown files and category YAML into memory
2. **DataStore** (`app/services/data_loader.py`): Central in-memory store holding all categories and topics with indices for fast lookups
3. **Routers**: `web.py` serves HTML pages via Jinja2, `api.py` serves JSON responses
4. **SearchService** (`app/services/search.py`): In-memory inverted index on topic titles

### Key Components
- **DataStore**: Singleton pattern via `get_data_store()`. Parses `_category.yml` files for categories and `*.md` files (with frontmatter) for topics. Builds indices: `category_tree` (parent→children) and `category_topics` (category→topic_ids)
- **Two parallel interfaces**: Web routes (`/`, `/category/{id}`, `/topic/{id}`, `/search`) return HTML; API routes (`/api/v1/...`) return JSON
- **Global search service caches**: Both `web.py` and `api.py` have `_search_service` globals that must be reset in tests

### Data Format
- Categories: `var/data/<slug>/_category.yml` with `id`, `name`, `parent_cid`, `slug`
- Topics: `var/data/<path>/<topic_id>-<slug>.md` with YAML frontmatter containing `topic_id`, `title`, `author_id`, `category_id`, `created`, etc.

### Testing
Tests use fixtures in `tests/conftest.py` that create temporary test data and mock the global `data_store`. The `mock_data_store` fixture also resets `_search_service` in both routers to ensure test isolation.

#### Test Structure (GIVEN / WHEN / THEN)
Use comments to structure tests following the GIVEN/WHEN/THEN pattern:

```python
def test_example():
    # GIVEN a user with valid credentials
    user = create_user(name="test", role="admin")

    # WHEN the user attempts to login
    result = login(user.name, user.password)

    # THEN the login should succeed
    assert result.success is True
    assert result.token is not None
```
