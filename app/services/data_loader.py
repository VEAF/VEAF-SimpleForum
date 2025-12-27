from datetime import datetime
from pathlib import Path
from typing import Any

import frontmatter
import markdown
import yaml

from app.config import settings


def parse_datetime(value: Any) -> datetime | None:
    """Parse a datetime value from various formats."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        # Try ISO format with microseconds
        for fmt in [
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S.%f",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
        ]:
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue
    return None


class DataStore:
    def __init__(self, data_path: Path) -> None:
        self.data_path = data_path
        self.categories: dict[int, dict[str, Any]] = {}
        self.topics: dict[int, dict[str, Any]] = {}
        self.category_topics: dict[int, list[int]] = {}
        self.category_tree: dict[int, list[int]] = {}
        self.export_info: dict[str, Any] = {}
        self._md = markdown.Markdown(extensions=["tables", "fenced_code", "nl2br"])

    def load_all(self) -> None:
        self._load_export_info()
        self._load_categories()
        self._load_topics()
        self._build_indices()

    def _load_export_info(self) -> None:
        export_file = self.data_path / "_export.yml"
        if export_file.exists():
            with open(export_file, encoding="utf-8") as f:
                data = yaml.safe_load(f)
                self.export_info = data.get("export_info", {})

    def _load_categories(self) -> None:
        for cat_file in self.data_path.rglob("_category.yml"):
            try:
                with open(cat_file, encoding="utf-8") as f:
                    cat_data = yaml.safe_load(f)
                    if cat_data and "id" in cat_data:
                        cat_data["_path"] = str(cat_file.parent)
                        cat_data.setdefault("parent_cid", 0)
                        cat_data.setdefault("order", 0)
                        cat_data.setdefault("disabled", False)
                        cat_data.setdefault(
                            "is_subcategory", cat_data.get("parent_cid", 0) != 0
                        )
                        cat_data.setdefault("icon", None)
                        cat_data.setdefault("bgColor", None)
                        cat_data.setdefault("color", None)
                        cat_data.setdefault("postcount", 0)
                        # topiccount: valeur statique de NodeBB, non utilisée
                        # (topic_count calculé dynamiquement)
                        cat_data.setdefault("topiccount", 0)
                        self.categories[cat_data["id"]] = cat_data
            except Exception:
                pass

    def _load_topics(self) -> None:
        for md_file in self.data_path.rglob("*.md"):
            if md_file.name == "index.md":
                continue
            try:
                post = frontmatter.load(md_file)
                topic_data = dict(post.metadata)
                if "topic_id" not in topic_data:
                    continue

                topic_data["content"] = post.content
                self._md.reset()
                topic_data["content_html"] = self._md.convert(post.content)
                topic_data["_path"] = str(md_file)
                topic_data["slug"] = md_file.stem

                topic_data.setdefault("deleted", False)
                topic_data.setdefault("locked", False)
                topic_data.setdefault("pinned", False)
                topic_data.setdefault("post_count", 0)
                topic_data.setdefault("rating", 0)
                topic_data.setdefault("view_count", 0)
                topic_data.setdefault("tags", [])
                topic_data.setdefault("last_post", None)

                # Parse date fields
                if "created" in topic_data:
                    topic_data["created"] = parse_datetime(topic_data["created"])
                if "last_post" in topic_data:
                    topic_data["last_post"] = parse_datetime(topic_data["last_post"])

                self.topics[topic_data["topic_id"]] = topic_data
            except Exception:
                pass

    def _build_indices(self) -> None:
        for cid, cat in self.categories.items():
            parent = cat.get("parent_cid", 0)
            if parent not in self.category_tree:
                self.category_tree[parent] = []
            self.category_tree[parent].append(cid)

        for parent_id in self.category_tree:
            self.category_tree[parent_id].sort(
                key=lambda cid: self.categories.get(cid, {}).get("order", 0)
            )

        for tid, topic in self.topics.items():
            cat_id = topic.get("category_id")
            if cat_id is not None:
                if cat_id not in self.category_topics:
                    self.category_topics[cat_id] = []
                self.category_topics[cat_id].append(tid)

    def get_root_categories(self) -> list[dict[str, Any]]:
        root_ids = self.category_tree.get(0, [])
        return [self.categories[cid] for cid in root_ids if cid in self.categories]

    def get_category(self, category_id: int) -> dict[str, Any] | None:
        return self.categories.get(category_id)

    def get_subcategories(self, category_id: int) -> list[dict[str, Any]]:
        sub_ids = self.category_tree.get(category_id, [])
        return [self.categories[cid] for cid in sub_ids if cid in self.categories]

    def get_category_topics(
        self,
        category_id: int,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created",
        order: str = "desc",
    ) -> tuple[list[dict[str, Any]], int]:
        topic_ids = self.category_topics.get(category_id, [])
        topics = [self.topics[tid] for tid in topic_ids if tid in self.topics]

        reverse = order == "desc"

        def sort_key(t: dict[str, Any]) -> Any:
            val = t.get(sort_by)
            if val is None:
                return datetime.min if reverse else datetime.max
            return val

        topics.sort(key=sort_key, reverse=reverse)

        total = len(topics)
        start = (page - 1) * page_size
        end = start + page_size
        return topics[start:end], total

    def get_topic(self, topic_id: int) -> dict[str, Any] | None:
        return self.topics.get(topic_id)

    def get_all_topics(
        self,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created",
        order: str = "desc",
    ) -> tuple[list[dict[str, Any]], int]:
        topics = list(self.topics.values())

        reverse = order == "desc"

        def sort_key(t: dict[str, Any]) -> Any:
            val = t.get(sort_by)
            if val is None:
                return datetime.min if reverse else datetime.max
            return val

        topics.sort(key=sort_key, reverse=reverse)

        total = len(topics)
        start = (page - 1) * page_size
        end = start + page_size
        return topics[start:end], total

    def get_recent_topics(self, limit: int = 10) -> list[dict[str, Any]]:
        topics = sorted(
            self.topics.values(),
            key=lambda t: t.get("created") or datetime.min,
            reverse=True,
        )
        return topics[:limit]

    def build_category_tree(self, parent_id: int = 0) -> list[dict[str, Any]]:
        result = []
        for cid in self.category_tree.get(parent_id, []):
            cat = self.categories.get(cid)
            if cat:
                node = dict(cat)
                node["children"] = self.build_category_tree(cid)
                node["topic_count"] = len(self.category_topics.get(cid, []))
                result.append(node)
        return result


data_store: DataStore | None = None


def get_data_store() -> DataStore:
    global data_store
    if data_store is None:
        data_store = DataStore(settings.DATA_PATH)
        data_store.load_all()
    return data_store


def init_data_store() -> DataStore:
    global data_store
    data_store = DataStore(settings.DATA_PATH)
    data_store.load_all()
    return data_store
