"""Unit tests for search service."""


from app.services.data_loader import DataStore
from app.services.search import SearchService


class TestSearchService:
    """Tests for SearchService class."""

    def test_search_single_word(self, test_data_store: DataStore):
        """Test search with a single word."""
        search = SearchService(test_data_store)
        results = search.search("first")
        assert len(results) == 1
        assert results[0]["topic_id"] == 100

    def test_search_multiple_words(self, test_data_store: DataStore):
        """Test search with multiple words."""
        search = SearchService(test_data_store)
        results = search.search("test topic")
        # Should match topics containing both "test" and "topic"
        assert len(results) >= 1

    def test_search_partial_word(self, test_data_store: DataStore):
        """Test search with partial word match."""
        search = SearchService(test_data_store)
        results = search.search("sub")
        assert len(results) == 1
        assert results[0]["topic_id"] == 102

    def test_search_case_insensitive(self, test_data_store: DataStore):
        """Test that search is case insensitive."""
        search = SearchService(test_data_store)
        results_lower = search.search("first")
        results_upper = search.search("FIRST")
        results_mixed = search.search("FiRsT")
        assert len(results_lower) == len(results_upper) == len(results_mixed)

    def test_search_no_results(self, test_data_store: DataStore):
        """Test search with no matching results."""
        search = SearchService(test_data_store)
        results = search.search("nonexistent")
        assert len(results) == 0

    def test_search_empty_query(self, test_data_store: DataStore):
        """Test search with empty query."""
        search = SearchService(test_data_store)
        results = search.search("")
        assert len(results) == 0

    def test_search_with_limit(self, test_data_store: DataStore):
        """Test search result limit."""
        search = SearchService(test_data_store)
        results = search.search("topic", limit=1)
        assert len(results) <= 1

    def test_search_results_sorted_by_views(self, test_data_store: DataStore):
        """Test that results are sorted by view count."""
        search = SearchService(test_data_store)
        results = search.search("topic")
        if len(results) > 1:
            for i in range(len(results) - 1):
                assert results[i]["view_count"] >= results[i + 1]["view_count"]

    def test_search_unicode(self, test_data_store: DataStore):
        """Test search with unicode characters."""
        search = SearchService(test_data_store)
        # Should not crash with unicode
        results = search.search("catégorie")
        assert isinstance(results, list)

    def test_search_special_characters(self, test_data_store: DataStore):
        """Test search with special characters."""
        search = SearchService(test_data_store)
        # Should handle special chars gracefully
        results = search.search("test-topic")
        assert isinstance(results, list)

    def test_index_built_correctly(self, test_data_store: DataStore):
        """Test that search index is built correctly."""
        search = SearchService(test_data_store)
        # Check that words from titles are indexed
        assert "first" in search.title_index
        assert "second" in search.title_index
        assert "subcategory" in search.title_index

    def test_short_words_excluded(self, test_data_store: DataStore):
        """Test that very short words are excluded from index."""
        search = SearchService(test_data_store)
        # Single character words should be excluded
        assert "a" not in search.title_index
