from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from ..types import Project  # type: ignore[attr-defined]
from ._base import _Service


def _safe_str(v: Any, default: str = "") -> str:
    return v if isinstance(v, str) else (str(v) if v is not None else default)


class Projects(_Service):
    def list(self, organization: str) -> Iterator[Project]:
        path = f"/api/v2/organizations/{organization}/projects"
        for item in self._list(path):
            attr = item.get("attributes", {}) or {}
            proj_id = _safe_str(item.get("id"))
            name = _safe_str(attr.get("name"))
            yield Project(id=proj_id, name=name, organization=organization)
