"""End-to-end tests simulating real user journeys."""
import pytest
from fastapi.testclient import TestClient


class TestBrowsingJourney:
    """Tests simulating a user browsing the forum."""

    def test_browse_from_home_to_topic(self, client: TestClient):
        """Test complete journey: home -> category -> topic."""
        # Step 1: Visit home page
        home_response = client.get("/")
        assert home_response.status_code == 200
        assert "Test Category" in home_response.text

        # Step 2: Click on a category
        category_response = client.get("/category/1")
        assert category_response.status_code == 200
        assert "First Test Topic" in category_response.text

        # Step 3: Click on a topic
        topic_response = client.get("/topic/100")
        assert topic_response.status_code == 200
        assert "First Test Topic" in topic_response.text
        assert "Section 1" in topic_response.text

    def test_browse_nested_categories(self, client: TestClient):
        """Test browsing through nested categories."""
        # Start at root category
        cat1_response = client.get("/category/1")
        assert cat1_response.status_code == 200
        assert "Test Subcategory" in cat1_response.text

        # Navigate to subcategory
        cat2_response = client.get("/category/2")
        assert cat2_response.status_code == 200
        assert "Subcategory Topic" in cat2_response.text

        # View topic in subcategory
        topic_response = client.get("/topic/102")
        assert topic_response.status_code == 200
        # Verify breadcrumb shows full path
        assert "Test Category" in topic_response.text
        assert "Test Subcategory" in topic_response.text

    def test_navigate_back_to_category(self, client: TestClient):
        """Test navigating from topic back to category."""
        # View a topic
        topic_response = client.get("/topic/100-first-test-topic")
        assert topic_response.status_code == 200

        # Back button link should exist with slug
        assert "/category/1-test-category" in topic_response.text

        # Navigate back
        category_response = client.get("/category/1-test-category")
        assert category_response.status_code == 200


class TestSearchJourney:
    """Tests simulating a user searching for content."""

    def test_search_and_view_result(self, client: TestClient):
        """Test complete search journey: search -> view result."""
        # Step 1: Go to search page
        search_page = client.get("/search")
        assert search_page.status_code == 200

        # Step 2: Perform search
        search_results = client.get("/search?q=first")
        assert search_results.status_code == 200
        assert "First Test Topic" in search_results.text

        # Step 3: Click on search result
        topic_response = client.get("/topic/100")
        assert topic_response.status_code == 200
        assert "First Test Topic" in topic_response.text

    def test_search_from_header(self, client: TestClient):
        """Test search using header search form."""
        # Any page should have search in header
        home = client.get("/")
        assert 'action="/search"' in home.text

        # Perform search
        results = client.get("/search?q=subcategory")
        assert results.status_code == 200
        assert "Subcategory Topic" in results.text

    def test_refine_search(self, client: TestClient):
        """Test refining a search query."""
        # First search
        results1 = client.get("/search?q=topic")
        assert results1.status_code == 200

        # Refined search
        results2 = client.get("/search?q=first+topic")
        assert results2.status_code == 200


class TestAPIConsumerJourney:
    """Tests simulating an API consumer using the REST API."""

    def test_api_explore_categories_and_topics(self, client: TestClient):
        """Test API journey: explore categories and fetch topics."""
        # Step 1: Get root categories
        categories = client.get("/api/v1/categories")
        assert categories.status_code == 200
        cat_data = categories.json()
        assert len(cat_data) > 0
        category_id = cat_data[0]["id"]

        # Step 2: Get category details
        category_detail = client.get(f"/api/v1/categories/{category_id}")
        assert category_detail.status_code == 200
        cat_detail_data = category_detail.json()
        assert "subcategories" in cat_detail_data

        # Step 3: Get topics in category
        topics = client.get(f"/api/v1/categories/{category_id}/topics")
        assert topics.status_code == 200
        topics_data = topics.json()
        assert "items" in topics_data
        assert len(topics_data["items"]) > 0
        topic_id = topics_data["items"][0]["topic_id"]

        # Step 4: Get full topic content
        topic = client.get(f"/api/v1/topics/{topic_id}")
        assert topic.status_code == 200
        topic_data = topic.json()
        assert "content" in topic_data
        assert "content_html" in topic_data

    def test_api_get_full_category_tree(self, client: TestClient):
        """Test getting full category hierarchy."""
        tree = client.get("/api/v1/categories/tree")
        assert tree.status_code == 200
        tree_data = tree.json()

        # Verify tree structure
        assert len(tree_data) > 0
        root = tree_data[0]
        assert "children" in root
        assert len(root["children"]) > 0

    def test_api_paginated_browsing(self, client: TestClient):
        """Test paginated browsing through API."""
        # Get first page
        page1 = client.get("/api/v1/topics?page=1&page_size=2")
        assert page1.status_code == 200
        page1_data = page1.json()

        if page1_data["total_pages"] > 1:
            # Get second page
            page2 = client.get("/api/v1/topics?page=2&page_size=2")
            assert page2.status_code == 200
            page2_data = page2.json()

            # Verify different items
            page1_ids = {t["topic_id"] for t in page1_data["items"]}
            page2_ids = {t["topic_id"] for t in page2_data["items"]}
            assert page1_ids.isdisjoint(page2_ids)

    def test_api_search_workflow(self, client: TestClient):
        """Test API search workflow."""
        # Search for topics
        search = client.get("/api/v1/search?q=test")
        assert search.status_code == 200
        results = search.json()
        assert len(results) > 0

        # Get details for first result
        topic_id = results[0]["topic_id"]
        topic = client.get(f"/api/v1/topics/{topic_id}")
        assert topic.status_code == 200


class TestPaginationJourney:
    """Tests for pagination through content."""

    def test_paginate_through_topics(self, client: TestClient):
        """Test paginating through topics list."""
        # Get first page
        response = client.get("/category/1?page=1&page_size=1")
        assert response.status_code == 200
        assert "Page 1" in response.text or "page=" in response.text

        # Navigate to next page
        response2 = client.get("/category/1?page=2&page_size=1")
        assert response2.status_code == 200


class TestErrorHandling:
    """Tests for error handling in user journeys."""

    def test_handle_not_found_category(self, client: TestClient):
        """Test handling of non-existent category."""
        response = client.get("/category/99999")
        assert response.status_code == 404

    def test_handle_not_found_topic(self, client: TestClient):
        """Test handling of non-existent topic."""
        response = client.get("/topic/99999")
        assert response.status_code == 404

    def test_handle_invalid_pagination(self, client: TestClient):
        """Test handling of invalid pagination parameters."""
        # Very high page number should still work (empty results)
        response = client.get("/category/1?page=9999")
        assert response.status_code == 200


class TestRealDataE2E:
    """End-to-end tests with real data (if available)."""

    def test_real_data_home_page(self, real_client: TestClient):
        """Test home page with real data."""
        response = real_client.get("/")
        assert response.status_code == 200
        # Real data should have meaningful stats
        assert "60" in response.text or "Categories" in response.text

    def test_real_data_category_navigation(self, real_client: TestClient):
        """Test category navigation with real data."""
        # Get categories from API
        cats = real_client.get("/api/v1/categories")
        assert cats.status_code == 200
        categories = cats.json()

        if categories:
            # Visit first category
            cat_id = categories[0]["id"]
            cat_response = real_client.get(f"/category/{cat_id}")
            assert cat_response.status_code == 200

    def test_real_data_search(self, real_client: TestClient):
        """Test search with real data."""
        response = real_client.get("/search?q=training")
        assert response.status_code == 200

    def test_real_data_health_check(self, real_client: TestClient):
        """Test health check with real data."""
        response = real_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["topics_loaded"] > 1000  # Real data has 1220 topics
        assert data["categories_loaded"] == 60
