from __future__ import annotations

import builtins
from collections.abc import Iterator
from typing import Any

from ..types import ExecutionMode, Workspace  # type: ignore[attr-defined]
from ._base import _Service


def _safe_str(v: Any, default: str = "") -> str:
    return v if isinstance(v, str) else (str(v) if v is not None else default)


def _em_safe(v: Any) -> ExecutionMode | None:
    # Only accept strings; map to enum if known, else None
    if not isinstance(v, str):
        return None
    return ExecutionMode._value2member_map_.get(v)


def _ws_from(d: dict[str, Any], org: str | None = None) -> Workspace:
    attr: dict[str, Any] = d.get("attributes", {}) or {}

    # Coerce to required string fields (empty string fallback keeps mypy happy)
    id_str: str = _safe_str(d.get("id"))
    name_str: str = _safe_str(attr.get("name"))
    org_str: str = _safe_str(org if org is not None else attr.get("organization"))

    # Optional fields
    em: ExecutionMode | None = _em_safe(attr.get("execution-mode"))

    proj_id: str | None = None
    proj = attr.get("project")
    if isinstance(proj, dict):
        proj_id = proj.get("id") if isinstance(proj.get("id"), str) else None

    tags_val = attr.get("tags", []) or []
    tags_list: list[str] = list(tags_val) if isinstance(tags_val, list | tuple) else []

    return Workspace(
        id=id_str,
        name=name_str,
        organization=org_str,
        execution_mode=em,
        project_id=proj_id,
        tags=tags_list,
    )


class Workspaces(_Service):
    def list(
        self, organization: str, *, search: str | None = None
    ) -> Iterator[Workspace]:
        params: dict[str, Any] = {}
        if search:
            params["search[name]"] = search
        path = f"/api/v2/organizations/{organization}/workspaces"
        for item in self._list(path, params=params):
            yield _ws_from(item, organization)

    def get(self, id_or_name: str, organization: str | None = None) -> Workspace:
        if organization:
            r = self.t.request(
                "GET", f"/api/v2/organizations/{organization}/workspaces/{id_or_name}"
            )
        else:
            r = self.t.request("GET", f"/api/v2/workspaces/{id_or_name}")
        return _ws_from(r.json()["data"], organization)

    def create(
        self,
        organization: str,
        name: str,
        *,
        execution_mode: str | None = "remote",
        project_id: str | None = None,
        tags: builtins.list[str] | None = None,
    ) -> Workspace:
        body: dict[str, Any] = {
            "data": {"type": "workspaces", "attributes": {"name": name}}
        }
        if execution_mode:
            body["data"]["attributes"]["execution-mode"] = execution_mode
        if project_id:
            body["data"].setdefault("relationships", {})
            body["data"]["relationships"]["project"] = {
                "data": {"type": "projects", "id": project_id}
            }
        if tags:
            body["data"]["attributes"]["tags"] = list(tags)

        r = self.t.request(
            "POST", f"/api/v2/organizations/{organization}/workspaces", json_body=body
        )
        return _ws_from(r.json()["data"], organization)

    def update(self, id: str, **attrs: Any) -> Workspace:
        body: dict[str, Any] = {
            "data": {"type": "workspaces", "id": id, "attributes": {}}
        }
        for k, v in attrs.items():
            kk = k.replace("_", "-")
            # Map enum back to string if provided
            if kk == "execution-mode" and isinstance(v, ExecutionMode):
                v = v.value
            body["data"]["attributes"][kk] = v
        r = self.t.request("PATCH", f"/api/v2/workspaces/{id}", json_body=body)
        return _ws_from(r.json()["data"], None)

    def delete(self, id: str) -> None:
        self.t.request("DELETE", f"/api/v2/workspaces/{id}")
