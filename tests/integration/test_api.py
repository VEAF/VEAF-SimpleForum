"""Integration tests for API endpoints."""

from fastapi.testclient import TestClient


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    def test_health_check(self, client: TestClient):
        """Test health endpoint returns healthy status."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "topics_loaded" in data
        assert "categories_loaded" in data


class TestInfoEndpoint:
    """Tests for info endpoint."""

    def test_get_info(self, client: TestClient):
        """Test info endpoint returns export info."""
        response = client.get("/api/v1/info")
        assert response.status_code == 200
        data = response.json()
        assert "total_users" in data
        assert "total_categories" in data
        assert "total_topics" in data
        assert "total_posts" in data


class TestCategoriesAPI:
    """Tests for categories API endpoints."""

    def test_list_root_categories(self, client: TestClient):
        """Test listing root categories."""
        response = client.get("/api/v1/categories")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["id"] == 1
        assert data[0]["name"] == "Test Category"

    def test_get_category_tree(self, client: TestClient):
        """Test getting full category tree."""
        response = client.get("/api/v1/categories/tree")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        # Check nested structure
        assert "children" in data[0]
        assert len(data[0]["children"]) == 1
        assert data[0]["children"][0]["id"] == 2

    def test_get_category_detail(self, client: TestClient):
        """Test getting category detail."""
        response = client.get("/api/v1/categories/1")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert data["name"] == "Test Category"
        assert "subcategories" in data
        assert len(data["subcategories"]) == 1

    def test_get_category_not_found(self, client: TestClient):
        """Test getting non-existent category."""
        response = client.get("/api/v1/categories/999")
        assert response.status_code == 404

    def test_list_category_topics(self, client: TestClient):
        """Test listing topics in a category."""
        response = client.get("/api/v1/categories/1/topics")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "total_pages" in data
        assert data["total"] == 2
        assert len(data["items"]) == 2

    def test_list_category_topics_pagination(self, client: TestClient):
        """Test topics pagination."""
        response = client.get("/api/v1/categories/1/topics?page=1&page_size=1")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["total"] == 2
        assert data["total_pages"] == 2

    def test_list_category_topics_sorting(self, client: TestClient):
        """Test topics sorting."""
        response = client.get(
            "/api/v1/categories/1/topics?sort_by=view_count&order=desc"
        )
        assert response.status_code == 200
        data = response.json()
        items = data["items"]
        if len(items) > 1:
            assert items[0]["view_count"] >= items[1]["view_count"]

    def test_list_category_topics_not_found(self, client: TestClient):
        """Test listing topics for non-existent category."""
        response = client.get("/api/v1/categories/999/topics")
        assert response.status_code == 404


class TestTopicsAPI:
    """Tests for topics API endpoints."""

    def test_list_all_topics(self, client: TestClient):
        """Test listing all topics."""
        response = client.get("/api/v1/topics")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert data["total"] == 3

    def test_list_topics_pagination(self, client: TestClient):
        """Test topics pagination."""
        response = client.get("/api/v1/topics?page=1&page_size=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2

    def test_get_topic_detail(self, client: TestClient):
        """Test getting topic detail."""
        response = client.get("/api/v1/topics/100")
        assert response.status_code == 200
        data = response.json()
        assert data["topic_id"] == 100
        assert data["title"] == "First Test Topic"
        assert "content" in data
        assert "content_html" in data
        # Le h1 du titre est supprimé pour éviter la duplication
        assert "<h1>" not in data["content_html"]

    def test_get_topic_not_found(self, client: TestClient):
        """Test getting non-existent topic."""
        response = client.get("/api/v1/topics/999")
        assert response.status_code == 404

    def test_topic_fields(self, client: TestClient):
        """Test that topic has all expected fields."""
        response = client.get("/api/v1/topics/100")
        data = response.json()
        assert "topic_id" in data
        assert "title" in data
        assert "author_id" in data
        assert "category_id" in data
        assert "created" in data
        assert "pinned" in data
        assert "locked" in data
        assert "post_count" in data
        assert "view_count" in data
        assert "rating" in data
        assert "tags" in data


class TestSearchAPI:
    """Tests for search API endpoint."""

    def test_search_topics(self, client: TestClient):
        """Test searching topics."""
        response = client.get("/api/v1/search?q=first")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["topic_id"] == 100

    def test_search_no_results(self, client: TestClient):
        """Test search with no results."""
        response = client.get("/api/v1/search?q=nonexistentterm")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0

    def test_search_requires_query(self, client: TestClient):
        """Test that search requires query parameter."""
        response = client.get("/api/v1/search")
        assert response.status_code == 422  # Validation error

    def test_search_with_limit(self, client: TestClient):
        """Test search with limit."""
        response = client.get("/api/v1/search?q=topic&limit=1")
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 1


class TestAPIValidation:
    """Tests for API input validation."""

    def test_invalid_page_number(self, client: TestClient):
        """Test invalid page number."""
        response = client.get("/api/v1/topics?page=0")
        assert response.status_code == 422

    def test_invalid_page_size(self, client: TestClient):
        """Test invalid page size."""
        response = client.get("/api/v1/topics?page_size=0")
        assert response.status_code == 422

    def test_page_size_too_large(self, client: TestClient):
        """Test page size exceeding maximum."""
        response = client.get("/api/v1/topics?page_size=500")
        assert response.status_code == 422

    def test_invalid_sort_by(self, client: TestClient):
        """Test invalid sort_by parameter."""
        response = client.get("/api/v1/topics?sort_by=invalid")
        assert response.status_code == 422

    def test_invalid_order(self, client: TestClient):
        """Test invalid order parameter."""
        response = client.get("/api/v1/topics?order=invalid")
        assert response.status_code == 422
