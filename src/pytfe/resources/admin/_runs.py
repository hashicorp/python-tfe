# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from ..._jsonapi import attach_jsonapi
from ...errors import ERR_INVALID_NAME
from ...models.admin_run import AdminRun, AdminRunListOptions
from ...utils import valid_string_id
from .._base import _Service


def _parse_admin_run(data: dict[str, Any]) -> AdminRun:
    attrs = data.get("attributes") or {}
    rels = data.get("relationships") or {}
    ws_data = (rels.get("workspace") or {}).get("data") or {}
    # organization is a compound include (workspace.organization) — only
    # present when the caller passes ?include=workspace.organization.
    # We don't surface that parameter yet, so organization_name stays None.
    return attach_jsonapi(
        AdminRun.model_validate(
            {
                "id": data.get("id"),
                "workspace_id": ws_data.get("id"),
                **attrs,
            }
        ),
        data,
    )


class _AdminRuns(_Service):
    def list(self, options: AdminRunListOptions | None = None) -> Iterator[AdminRun]:
        """List Terraform Enterprise admin runs.

        Args:
            options: Optional filters and pagination, as a :class:`AdminRunListOptions`.

        Returns:
            A single-use ``Iterator[AdminRun]``. Wrap with ``list(...)`` to
            materialize the results or iterate more than once.

        Raises:
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import AdminRunListOptions
            >>> runs = client.admin.runs.list(AdminRunListOptions(run_status="planned"))
            >>> for run in runs:
            ...     print(run.id, run.workspace_id)
        """
        params: dict[str, Any] = {}
        if options:
            if options.run_status:
                params["filter[status]"] = options.run_status
            if options.query:
                params["q"] = options.query
            if options.page_number is not None:
                params["page[number]"] = options.page_number
            if options.page_size is not None:
                params["page[size]"] = options.page_size
        for item in self._list("/api/v2/admin/runs", params=params):
            yield _parse_admin_run(item)

    def force_cancel(self, run_id: str) -> None:
        """Forcefully cancel a Terraform Enterprise admin run.

        Args:
            run_id: The run ID (e.g. ``"run-xxxxxxxx"``).

        Returns:
            None.

        Raises:
            ValueError: If ``run_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> client.admin.runs.force_cancel("run-CZcmD7eagjhyX0vN")
        """
        if not valid_string_id(run_id):
            raise ValueError(ERR_INVALID_NAME)
        self.t.request("POST", f"/api/v2/admin/runs/{run_id}/actions/force-cancel")
