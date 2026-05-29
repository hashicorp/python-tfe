# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from ...errors import ERR_INVALID_NAME
from ...models.admin_workspace import AdminWorkspace, AdminWorkspaceListOptions
from ...utils import valid_string_id
from .._base import _Service


def _parse_admin_workspace(data: dict[str, Any]) -> AdminWorkspace:
    attrs = data.get("attributes") or {}
    rels = data.get("relationships") or {}
    org_data = (rels.get("organization") or {}).get("data") or {}
    run_data = (rels.get("current-run") or {}).get("data") or {}
    return AdminWorkspace.model_validate({
        "id": data.get("id"),
        "organization_name": org_data.get("id"),
        "current_run_id": run_data.get("id"),
        **attrs,
    })


class _AdminWorkspaces(_Service):
    def list(self, options: AdminWorkspaceListOptions | None = None) -> Iterator[AdminWorkspace]:
        params: dict[str, Any] = {}
        if options:
            if options.query:
                params["q"] = options.query
            if options.page_number is not None:
                params["page[number]"] = options.page_number
            if options.page_size is not None:
                params["page[size]"] = options.page_size
        for item in self._list("/api/v2/admin/workspaces", params=params):
            yield _parse_admin_workspace(item)

    def read(self, workspace_id: str) -> AdminWorkspace:
        if not valid_string_id(workspace_id):
            raise ValueError(ERR_INVALID_NAME)
        r = self.t.request("GET", f"/api/v2/admin/workspaces/{workspace_id}")
        return _parse_admin_workspace(r.json()["data"])
