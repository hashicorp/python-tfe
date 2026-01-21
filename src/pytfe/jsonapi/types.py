from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class JSONAPINode:
    """Represents a JSON:API resource object node."""

    def __init__(self, data: dict[str, Any]):
        self.id: str = data.get("id", "")
        self.type: str = data.get("type", "")
        self.attributes: dict[str, Any] = data.get("attributes", {})
        self.relationships: dict[str, Any] = data.get("relationships", {})
        self.links: dict[str, Any] | None = data.get("links")
        self.meta: dict[str, Any] | None = data.get("meta")
        self._raw_data = data

    def get_relationship_linkage(
        self, rel_name: str
    ) -> dict[str, Any] | list[dict[str, Any]] | None:
        """Extract relationship linkage data (type and id)."""
        if not self.relationships or rel_name not in self.relationships:
            return None

        rel_data = self.relationships[rel_name].get("data")
        if rel_data is None:
            return None
        # Can be dict or list of dicts based on relationship type
        return rel_data  # type: ignore[no-any-return]


class IncludedIndex:
    """Index for fast lookup of included resources."""

    def __init__(self, included: list[dict[str, Any]] | None = None):
        self._index: dict[tuple[str, str], JSONAPINode] = {}

        if included:
            for item in included:
                node = JSONAPINode(item)
                if node.type and node.id:
                    key = (node.type, node.id)
                    self._index[key] = node

    def get(self, resource_type: str, resource_id: str) -> JSONAPINode | None:
        """Lookup a resource by type and id."""
        return self._index.get((resource_type, resource_id))

    def resolve_relationship(
        self, rel_data: dict[str, Any] | None
    ) -> JSONAPINode | None:
        """Resolve a relationship linkage to full node."""
        if not rel_data or not isinstance(rel_data, dict):
            return None

        resource_type = rel_data.get("type")
        resource_id = rel_data.get("id")

        if not resource_type or not resource_id:
            return None

        return self.get(resource_type, resource_id)


class JSONAPIResponse(Generic[T]):
    """Complete JSON:API response with data and included."""

    def __init__(self, response_dict: dict[str, Any]):
        self.data: dict[str, Any] | list[dict[str, Any]] = response_dict.get("data", {})
        self.included: list[dict[str, Any]] = response_dict.get("included", [])
        self.links: dict[str, Any] | None = response_dict.get("links")
        self.meta: dict[str, Any] | None = response_dict.get("meta")

        # Build included index
        self.included_index = IncludedIndex(self.included)

    def is_collection(self) -> bool:
        """Check if data is a collection (list) or single resource."""
        return isinstance(self.data, list)
