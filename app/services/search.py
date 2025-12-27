import re
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.services.data_loader import DataStore


class SearchService:
    def __init__(self, data_store: "DataStore") -> None:
        self.store = data_store
        self.title_index: dict[str, list[int]] = {}
        self._build_index()

    def _build_index(self) -> None:
        for tid, topic in self.store.topics.items():
            title = topic.get("title", "").lower()
            words = re.findall(r"\w+", title, re.UNICODE)
            for word in words:
                if len(word) < 2:
                    continue
                if word not in self.title_index:
                    self.title_index[word] = []
                self.title_index[word].append(tid)

    def search(self, query: str, limit: int = 20) -> list[dict[str, Any]]:
        words = re.findall(r"\w+", query.lower(), re.UNICODE)
        if not words:
            return []

        result_sets = []
        for word in words:
            matching_ids = set()
            for indexed_word, tids in self.title_index.items():
                if word in indexed_word or indexed_word.startswith(word):
                    matching_ids.update(tids)
            result_sets.append(matching_ids)

        if not result_sets:
            return []

        matching_ids = result_sets[0]
        for s in result_sets[1:]:
            matching_ids &= s

        results = [
            self.store.topics[tid] for tid in matching_ids if tid in self.store.topics
        ]
        results.sort(key=lambda t: t.get("view_count", 0), reverse=True)

        return results[:limit]
