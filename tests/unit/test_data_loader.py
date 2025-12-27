"""Unit tests for data_loader service."""
import pytest
from pathlib import Path
from datetime import datetime

from app.services.data_loader import DataStore


class TestDataStore:
    """Tests for DataStore class."""

    def test_load_categories(self, test_data_store: DataStore):
        """Test that categories are loaded correctly."""
        assert len(test_data_store.categories) == 2
        assert 1 in test_data_store.categories
        assert 2 in test_data_store.categories

    def test_category_data(self, test_data_store: DataStore):
        """Test category data structure."""
        cat = test_data_store.categories[1]
        assert cat["name"] == "Test Category"
        assert cat["slug"] == "1/test-category"
        assert cat["parent_cid"] == 0
        assert cat["icon"] == "fa-folder"
        assert cat["bgColor"] == "#3498db"

    def test_subcategory_data(self, test_data_store: DataStore):
        """Test subcategory data structure."""
        subcat = test_data_store.categories[2]
        assert subcat["name"] == "Test Subcategory"
        assert subcat["parent_cid"] == 1
        assert subcat["is_subcategory"] is True

    def test_load_topics(self, test_data_store: DataStore):
        """Test that topics are loaded correctly."""
        assert len(test_data_store.topics) == 3
        assert 100 in test_data_store.topics
        assert 101 in test_data_store.topics
        assert 102 in test_data_store.topics

    def test_topic_data(self, test_data_store: DataStore):
        """Test topic data structure."""
        topic = test_data_store.topics[100]
        assert topic["title"] == "First Test Topic"
        assert topic["author_id"] == 1
        assert topic["category_id"] == 1
        assert topic["pinned"] is True
        assert topic["post_count"] == 5
        assert topic["view_count"] == 150
        assert "test" in topic["tags"]

    def test_topic_content_parsed(self, test_data_store: DataStore):
        """Test that markdown content is parsed."""
        topic = test_data_store.topics[100]
        assert "# First Test Topic" in topic["content"]
        assert topic["content_html"] is not None
        assert "<h1>" in topic["content_html"]
        assert "<strong>bold</strong>" in topic["content_html"]

    def test_category_tree_built(self, test_data_store: DataStore):
        """Test that category tree is built correctly."""
        assert 0 in test_data_store.category_tree
        assert 1 in test_data_store.category_tree[0]
        assert 2 in test_data_store.category_tree[1]

    def test_category_topics_indexed(self, test_data_store: DataStore):
        """Test that topics are indexed by category."""
        assert 1 in test_data_store.category_topics
        assert 2 in test_data_store.category_topics
        assert len(test_data_store.category_topics[1]) == 2
        assert len(test_data_store.category_topics[2]) == 1

    def test_export_info_loaded(self, test_data_store: DataStore):
        """Test that export info is loaded."""
        assert test_data_store.export_info["total_users"] == 10
        assert test_data_store.export_info["total_categories"] == 2
        assert test_data_store.export_info["total_topics"] == 3

    def test_get_root_categories(self, test_data_store: DataStore):
        """Test getting root categories."""
        roots = test_data_store.get_root_categories()
        assert len(roots) == 1
        assert roots[0]["id"] == 1

    def test_get_category(self, test_data_store: DataStore):
        """Test getting a specific category."""
        cat = test_data_store.get_category(1)
        assert cat is not None
        assert cat["name"] == "Test Category"

        not_found = test_data_store.get_category(999)
        assert not_found is None

    def test_get_subcategories(self, test_data_store: DataStore):
        """Test getting subcategories."""
        subcats = test_data_store.get_subcategories(1)
        assert len(subcats) == 1
        assert subcats[0]["id"] == 2

        no_subcats = test_data_store.get_subcategories(2)
        assert len(no_subcats) == 0

    def test_get_category_topics_default_sort(self, test_data_store: DataStore):
        """Test getting topics with default sort (created desc)."""
        topics, total = test_data_store.get_category_topics(1)
        assert total == 2
        assert len(topics) == 2
        # Should be sorted by created desc (most recent first)
        assert topics[0]["topic_id"] == 100  # 2024-01-15
        assert topics[1]["topic_id"] == 101  # 2024-01-10

    def test_get_category_topics_sort_by_views(self, test_data_store: DataStore):
        """Test getting topics sorted by view count."""
        topics, _ = test_data_store.get_category_topics(1, sort_by="view_count", order="desc")
        assert topics[0]["view_count"] >= topics[1]["view_count"]

    def test_get_category_topics_pagination(self, test_data_store: DataStore):
        """Test topic pagination."""
        topics, total = test_data_store.get_category_topics(1, page=1, page_size=1)
        assert len(topics) == 1
        assert total == 2

        topics_page2, _ = test_data_store.get_category_topics(1, page=2, page_size=1)
        assert len(topics_page2) == 1
        assert topics_page2[0]["topic_id"] != topics[0]["topic_id"]

    def test_get_topic(self, test_data_store: DataStore):
        """Test getting a specific topic."""
        topic = test_data_store.get_topic(100)
        assert topic is not None
        assert topic["title"] == "First Test Topic"

        not_found = test_data_store.get_topic(999)
        assert not_found is None

    def test_get_all_topics(self, test_data_store: DataStore):
        """Test getting all topics."""
        topics, total = test_data_store.get_all_topics()
        assert total == 3
        assert len(topics) == 3

    def test_get_recent_topics(self, test_data_store: DataStore):
        """Test getting recent topics."""
        recent = test_data_store.get_recent_topics(limit=2)
        assert len(recent) == 2
        # Most recent should be first
        assert recent[0]["topic_id"] == 102  # 2024-01-20

    def test_build_category_tree(self, test_data_store: DataStore):
        """Test building category tree structure."""
        tree = test_data_store.build_category_tree(0)
        assert len(tree) == 1
        assert tree[0]["id"] == 1
        assert len(tree[0]["children"]) == 1
        assert tree[0]["children"][0]["id"] == 2


class TestDataStoreEmpty:
    """Tests for DataStore with empty/missing data."""

    def test_empty_data_store(self, tmp_path: Path):
        """Test DataStore with empty directory."""
        store = DataStore(tmp_path)
        store.load_all()
        assert len(store.categories) == 0
        assert len(store.topics) == 0

    def test_missing_export_info(self, tmp_path: Path):
        """Test DataStore without _export.yml."""
        store = DataStore(tmp_path)
        store.load_all()
        assert store.export_info == {}

    def test_invalid_yaml_category(self, tmp_path: Path):
        """Test handling of invalid category YAML."""
        cat_dir = tmp_path / "bad-cat"
        cat_dir.mkdir()
        (cat_dir / "_category.yml").write_text("invalid: yaml: content:")

        store = DataStore(tmp_path)
        store.load_all()
        assert len(store.categories) == 0

    def test_invalid_frontmatter_topic(self, tmp_path: Path):
        """Test handling of invalid topic frontmatter."""
        (tmp_path / "bad-topic.md").write_text("No frontmatter here")

        store = DataStore(tmp_path)
        store.load_all()
        assert len(store.topics) == 0
