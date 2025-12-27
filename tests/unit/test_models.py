"""Unit tests for Pydantic models."""
import pytest
from datetime import datetime

from app.models.category import CategorySummary, CategoryDetail, CategoryTree
from app.models.topic import TopicSummary, TopicDetail
from app.models.common import PaginatedResponse, ExportInfo, ErrorResponse


class TestCategoryModels:
    """Tests for category models."""

    def test_category_summary_minimal(self):
        """Test CategorySummary with minimal fields."""
        cat = CategorySummary(id=1, name="Test", slug="1/test")
        assert cat.id == 1
        assert cat.name == "Test"
        assert cat.slug == "1/test"
        assert cat.parent_cid == 0
        assert cat.icon is None
        assert cat.topic_count == 0

    def test_category_summary_full(self):
        """Test CategorySummary with all fields."""
        cat = CategorySummary(
            id=1,
            name="Test Category",
            slug="1/test-category",
            parent_cid=0,
            icon="fa-folder",
            bgColor="#3498db",
            color="#ffffff",
            order=5,
            disabled=False,
            is_subcategory=False,
            topic_count=10,
            post_count=50,
        )
        assert cat.bgColor == "#3498db"
        assert cat.order == 5
        assert cat.topic_count == 10

    def test_category_detail_with_subcategories(self):
        """Test CategoryDetail with subcategories."""
        subcats = [
            CategorySummary(id=2, name="Sub1", slug="2/sub1", parent_cid=1),
            CategorySummary(id=3, name="Sub2", slug="3/sub2", parent_cid=1),
        ]
        cat = CategoryDetail(
            id=1,
            name="Parent",
            slug="1/parent",
            subcategories=subcats,
        )
        assert len(cat.subcategories) == 2
        assert cat.subcategories[0].name == "Sub1"

    def test_category_tree_nested(self):
        """Test CategoryTree with nested children."""
        child = CategoryTree(id=2, name="Child", slug="2/child", parent_cid=1, children=[])
        parent = CategoryTree(
            id=1,
            name="Parent",
            slug="1/parent",
            children=[child],
        )
        assert len(parent.children) == 1
        assert parent.children[0].name == "Child"
        assert parent.children[0].parent_cid == 1


class TestTopicModels:
    """Tests for topic models."""

    def test_topic_summary_minimal(self):
        """Test TopicSummary with minimal required fields."""
        topic = TopicSummary(
            topic_id=100,
            title="Test Topic",
            author_id=1,
            category_id=1,
            created=datetime(2024, 1, 15, 10, 30, 0),
        )
        assert topic.topic_id == 100
        assert topic.title == "Test Topic"
        assert topic.deleted is False
        assert topic.pinned is False
        assert topic.tags == []

    def test_topic_summary_full(self):
        """Test TopicSummary with all fields."""
        topic = TopicSummary(
            topic_id=100,
            title="Full Topic",
            author_id=1,
            category_id=1,
            created=datetime(2024, 1, 15, 10, 30, 0),
            deleted=False,
            locked=True,
            pinned=True,
            post_count=10,
            rating=5,
            view_count=200,
            tags=["tag1", "tag2"],
            last_post=datetime(2024, 1, 16, 14, 0, 0),
            slug="100-full-topic",
        )
        assert topic.locked is True
        assert topic.pinned is True
        assert topic.rating == 5
        assert len(topic.tags) == 2

    def test_topic_detail_with_content(self):
        """Test TopicDetail with content fields."""
        topic = TopicDetail(
            topic_id=100,
            title="Content Topic",
            author_id=1,
            category_id=1,
            created=datetime(2024, 1, 15),
            content="# Markdown content",
            content_html="<h1>Markdown content</h1>",
        )
        assert topic.content == "# Markdown content"
        assert "<h1>" in topic.content_html


class TestCommonModels:
    """Tests for common models."""

    def test_paginated_response(self):
        """Test PaginatedResponse model."""
        items = [{"id": 1}, {"id": 2}]
        response = PaginatedResponse(
            items=items,
            total=50,
            page=2,
            page_size=20,
            total_pages=3,
        )
        assert len(response.items) == 2
        assert response.total == 50
        assert response.page == 2
        assert response.total_pages == 3

    def test_export_info(self):
        """Test ExportInfo model."""
        info = ExportInfo(
            total_users=100,
            total_categories=20,
            total_topics=500,
            total_posts=5000,
        )
        assert info.total_users == 100
        assert info.total_posts == 5000

    def test_error_response(self):
        """Test ErrorResponse model."""
        error = ErrorResponse(detail="Not found", code="NOT_FOUND")
        assert error.detail == "Not found"
        assert error.code == "NOT_FOUND"

    def test_error_response_without_code(self):
        """Test ErrorResponse without code."""
        error = ErrorResponse(detail="Internal error")
        assert error.detail == "Internal error"
        assert error.code is None
