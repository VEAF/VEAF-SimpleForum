"""Integration tests for web (HTML) endpoints."""

from fastapi.testclient import TestClient


class TestHomePage:
    """Tests for home page."""

    def test_home_page_loads(self, client: TestClient):
        """Test that home page loads successfully."""
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_home_page_contains_title(self, client: TestClient):
        """Test that home page contains title."""
        response = client.get("/")
        assert "VEAF Community" in response.text

    def test_home_page_contains_stats(self, client: TestClient):
        """Test that home page contains statistics."""
        response = client.get("/")
        assert "Catégories" in response.text
        assert "Topics" in response.text
        assert "Posts" in response.text

    def test_home_page_contains_categories(self, client: TestClient):
        """Test that home page shows categories."""
        response = client.get("/")
        assert "Test Category" in response.text

    def test_home_page_has_search_form(self, client: TestClient):
        """Test that home page has search form."""
        response = client.get("/")
        assert 'action="/search"' in response.text
        assert 'name="q"' in response.text

    def test_home_page_category_links_have_slug(self, client: TestClient):
        """Test that category links include slug."""
        response = client.get("/")
        assert "/category/1/test-category" in response.text


class TestCategoryPage:
    """Tests for category page."""

    def test_category_page_loads_with_slug(self, client: TestClient):
        """Test that category page loads with full slug (NodeBB format)."""
        response = client.get("/category/1/test-category")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_category_page_redirects_without_slug(self, client: TestClient):
        """Test that category page redirects when slug is missing."""
        response = client.get("/category/1", follow_redirects=False)
        assert response.status_code == 301
        assert response.headers["location"] == "/category/1/test-category"

    def test_category_page_redirects_wrong_slug(self, client: TestClient):
        """Test that category page redirects with wrong slug."""
        response = client.get("/category/1/wrong-slug", follow_redirects=False)
        assert response.status_code == 301
        assert response.headers["location"] == "/category/1/test-category"

    def test_category_page_redirects_legacy_format(self, client: TestClient):
        """Test that category page redirects legacy format to new format."""
        response = client.get("/category/1-test-category", follow_redirects=False)
        assert response.status_code == 301
        assert response.headers["location"] == "/category/1/test-category"

    def test_category_page_redirect_preserves_query_params(self, client: TestClient):
        """Test that redirect preserves query parameters."""
        response = client.get("/category/1?page=2&page_size=10", follow_redirects=False)
        assert response.status_code == 301
        assert "page=2" in response.headers["location"]
        assert "page_size=10" in response.headers["location"]

    def test_category_page_shows_name(self, client: TestClient):
        """Test that category page shows category name."""
        response = client.get("/category/1/test-category")
        assert "Test Category" in response.text

    def test_category_page_shows_breadcrumb(self, client: TestClient):
        """Test that category page shows breadcrumb."""
        response = client.get("/category/1/test-category")
        assert "Accueil" in response.text

    def test_category_page_shows_topics(self, client: TestClient):
        """Test that category page shows topics."""
        response = client.get("/category/1/test-category")
        assert "First Test Topic" in response.text
        assert "Second Test Topic" in response.text

    def test_category_page_shows_subcategories(self, client: TestClient):
        """Test that category page shows subcategories."""
        response = client.get("/category/1/test-category")
        assert "Test Subcategory" in response.text

    def test_category_page_not_found(self, client: TestClient):
        """Test category page for non-existent category returns HTML 404."""
        response = client.get("/category/999/nonexistent")
        assert response.status_code == 404
        assert "text/html" in response.headers["content-type"]
        assert "Retour à l'accueil" in response.text
        assert "Page non trouvée" in response.text

    def test_subcategory_page_breadcrumb(self, client: TestClient):
        """Test that subcategory page has full breadcrumb."""
        response = client.get("/category/2/test-subcategory")
        # Should show parent category in breadcrumb
        assert "Test Category" in response.text
        assert "Test Subcategory" in response.text

    def test_category_page_pagination(self, client: TestClient):
        """Test category page with pagination."""
        response = client.get("/category/1/test-category?page=1&page_size=1")
        assert response.status_code == 200
        # Should show pagination controls
        assert "Page 1" in response.text or "page=2" in response.text

    def test_category_links_have_slug(self, client: TestClient):
        """Test that subcategory links include slug."""
        response = client.get("/category/1/test-category")
        assert "/category/2/test-subcategory" in response.text

    def test_topic_links_have_slug(self, client: TestClient):
        """Test that topic links include slug."""
        response = client.get("/category/1/test-category")
        assert "/topic/100/first-test-topic" in response.text


class TestTopicPage:
    """Tests for topic page."""

    def test_topic_page_loads_with_slug(self, client: TestClient):
        """Test that topic page loads with full slug (NodeBB format)."""
        response = client.get("/topic/100/first-test-topic")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_topic_page_redirects_without_slug(self, client: TestClient):
        """Test that topic page redirects when slug is missing."""
        response = client.get("/topic/100", follow_redirects=False)
        assert response.status_code == 301
        assert response.headers["location"] == "/topic/100/first-test-topic"

    def test_topic_page_redirects_wrong_slug(self, client: TestClient):
        """Test that topic page redirects with wrong slug."""
        response = client.get("/topic/100/wrong-slug", follow_redirects=False)
        assert response.status_code == 301
        assert response.headers["location"] == "/topic/100/first-test-topic"

    def test_topic_page_redirects_legacy_format(self, client: TestClient):
        """Test that topic page redirects legacy format to new format."""
        response = client.get("/topic/100-first-test-topic", follow_redirects=False)
        assert response.status_code == 301
        assert response.headers["location"] == "/topic/100/first-test-topic"

    def test_topic_page_shows_title(self, client: TestClient):
        """Test that topic page shows topic title."""
        response = client.get("/topic/100/first-test-topic")
        assert "First Test Topic" in response.text

    def test_topic_page_shows_content(self, client: TestClient):
        """Test that topic page shows rendered content."""
        response = client.get("/topic/100/first-test-topic")
        # Should contain rendered markdown
        assert "Section 1" in response.text

    def test_topic_page_shows_metadata(self, client: TestClient):
        """Test that topic page shows metadata."""
        response = client.get("/topic/100/first-test-topic")
        assert "posts" in response.text.lower() or "vues" in response.text.lower()

    def test_topic_page_shows_breadcrumb(self, client: TestClient):
        """Test that topic page shows breadcrumb."""
        response = client.get("/topic/100/first-test-topic")
        assert "Accueil" in response.text
        assert "Test Category" in response.text

    def test_topic_page_shows_tags(self, client: TestClient):
        """Test that topic page shows tags."""
        response = client.get("/topic/100/first-test-topic")
        assert "test" in response.text or "important" in response.text

    def test_topic_page_shows_badges(self, client: TestClient):
        """Test that topic page shows pinned/locked badges."""
        # Topic 100 is pinned
        response = client.get("/topic/100/first-test-topic")
        assert "pinned" in response.text.lower() or "Epingle" in response.text

    def test_topic_page_not_found(self, client: TestClient):
        """Test topic page for non-existent topic returns HTML 404."""
        response = client.get("/topic/999/nonexistent")
        assert response.status_code == 404
        assert "text/html" in response.headers["content-type"]
        assert "Retour à l'accueil" in response.text
        assert "Page non trouvée" in response.text

    def test_topic_page_back_link_has_slug(self, client: TestClient):
        """Test that topic page has back to category link with slug."""
        response = client.get("/topic/100/first-test-topic")
        assert "/category/1/test-category" in response.text


class TestSearchPage:
    """Tests for search page."""

    def test_search_page_loads(self, client: TestClient):
        """Test that search page loads without query."""
        response = client.get("/search")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_search_page_has_form(self, client: TestClient):
        """Test that search page has search form."""
        response = client.get("/search")
        assert 'action="/search"' in response.text
        assert 'name="q"' in response.text

    def test_search_with_query(self, client: TestClient):
        """Test search with query parameter."""
        response = client.get("/search?q=first")
        assert response.status_code == 200
        assert "first" in response.text.lower()

    def test_search_shows_results(self, client: TestClient):
        """Test that search shows matching results."""
        response = client.get("/search?q=first")
        assert "First Test Topic" in response.text

    def test_search_results_have_slug_links(self, client: TestClient):
        """Test that search result links include slug."""
        response = client.get("/search?q=first")
        assert "/topic/100/first-test-topic" in response.text

    def test_search_no_results(self, client: TestClient):
        """Test search with no results."""
        response = client.get("/search?q=nonexistentterm")
        assert response.status_code == 200
        assert "Aucun" in response.text or "0" in response.text

    def test_search_empty_query(self, client: TestClient):
        """Test search with empty query."""
        response = client.get("/search?q=")
        assert response.status_code == 200


class TestStaticFiles:
    """Tests for static file serving."""

    def test_css_file_served(self, client: TestClient):
        """Test that CSS file is served."""
        response = client.get("/static/css/style.css")
        assert response.status_code == 200
        assert "text/css" in response.headers["content-type"]

    def test_css_contains_styles(self, client: TestClient):
        """Test that CSS contains styles."""
        response = client.get("/static/css/style.css")
        assert "body" in response.text
        assert "header" in response.text
