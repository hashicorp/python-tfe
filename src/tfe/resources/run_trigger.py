from __future__ import annotations

import builtins
from collections.abc import Iterator
from datetime import datetime
from typing import Any

from ..errors import (
    InvalidRunTriggerIDError,
    InvalidRunTriggerTypeError,
    InvalidWorkspaceIDError,
    RequiredRunTriggerListOpsError,
    RequiredSourceableError,
    UnsupportedRunTriggerTypeError,
)
from ..models.run_trigger import (
    RunTrigger,
    RunTriggerCreateOptions,
    RunTriggerFilterOp,
    RunTriggerIncludeOp,
    RunTriggerListOptions,
    SourceableChoice,
)
from ..models.workspace import Workspace
from ..utils import valid_string_id
from ._base import _Service


def _safe_str(v: Any, default: str = "") -> str:
    return v if isinstance(v, str) else (str(v) if v is not None else default)


def _run_trigger_from(d: dict[str, Any], org: str | None = None) -> RunTrigger:
    attr: dict[str, Any] = d.get("attributes", {}) or {}
    relationships: dict[str, Any] = d.get("relationships", {}) or {}

    id_str: str = d.get("id", "")
    created_at_str: str = _safe_str(attr.get("created-at"))
    sourceable_name_str: str = _safe_str(attr.get("sourceable-name"))
    workspace_name_str: str = _safe_str(attr.get("workspace-name"))

    # Extract workspace ID from relationships
    workspace_id = ""
    workspace_rel = relationships.get("workspace", {})
    if workspace_rel and "data" in workspace_rel:
        workspace_id = workspace_rel["data"].get("id", "")

    # Extract sourceable ID from relationships
    sourceable_id = ""
    sourceable_rel = relationships.get("sourceable", {})
    if sourceable_rel and "data" in sourceable_rel:
        sourceable_id = sourceable_rel["data"].get("id", "")

    # Create workspace objects with proper IDs
    workspace = Workspace(
        id=workspace_id, name=workspace_name_str, organization=org or ""
    )
    sourceable = Workspace(
        id=sourceable_id, name=sourceable_name_str, organization=org or ""
    )
    sourceable_choice = SourceableChoice(
        workspace=sourceable
    )  # Should reference sourceable, not workspace

    # Parse created_at as datetime
    created_at = (
        datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
        if created_at_str
        else datetime.now()
    )

    return RunTrigger(
        id=id_str,
        created_at=created_at,
        sourceable_name=sourceable_name_str,
        workspace_name=workspace_name_str,
        sourceable=sourceable,
        sourceable_choice=sourceable_choice,
        workspace=workspace,
    )


class RunTriggers(_Service):
    def list(
        self, workspace_id: str, options: RunTriggerListOptions
    ) -> Iterator[RunTrigger]:
        if not valid_string_id(workspace_id):
            raise InvalidWorkspaceIDError()
        if not options:
            raise RequiredRunTriggerListOpsError()
        self.validate_run_trigger_filter_param(
            options.run_trigger_type, options.include or []
        )
        params: dict[str, str] = {}
        if options.page_size is not None:
            params["page[size]"] = str(options.page_size)
        if options.page_number is not None:
            params["page[number]"] = str(options.page_number)
        if options.run_trigger_type:
            params["filter[run-trigger][type]"] = options.run_trigger_type.value
        if options.include:
            params["include"] = ",".join(options.include)

        path = f"/api/v2/workspaces/{workspace_id}/run-triggers"
        for item in self._list(path, params=params):
            rt = _run_trigger_from(item)
            self.backfill_deprecated_sourceable(rt)
            yield rt

    def create(self, workspace_id: str, options: RunTriggerCreateOptions) -> RunTrigger:
        if not valid_string_id(workspace_id):
            raise InvalidWorkspaceIDError()
        if options.sourceable is None:
            raise RequiredSourceableError()
        body: dict[str, Any] = {
            "data": {
                "relationships": {
                    "sourceable": {
                        "data": {"type": "workspaces", "id": options.sourceable.id}
                    }
                }
            }
        }

        r = self.t.request(
            "POST",
            f"/api/v2/workspaces/{workspace_id}/run-triggers",
            json_body=body,
        )
        rt = _run_trigger_from(r.json()["data"])
        self.backfill_deprecated_sourceable(rt)
        return rt

    def read(self, run_trigger_id: str) -> RunTrigger:
        if not valid_string_id(run_trigger_id):
            raise InvalidRunTriggerIDError()
        path = f"/api/v2/run-triggers/{run_trigger_id}"
        r = self.t.request("GET", path)
        rt = _run_trigger_from(r.json()["data"])
        self.backfill_deprecated_sourceable(rt)
        return rt

    def delete(self, run_trigger_id: str) -> None:
        if not valid_string_id(run_trigger_id):
            raise InvalidRunTriggerIDError()
        path = f"/api/v2/run-triggers/{run_trigger_id}"
        self.t.request("DELETE", path)
        return None

    def validate_run_trigger_filter_param(
        self,
        filter_param: RunTriggerFilterOp,
        include_param: builtins.list[RunTriggerIncludeOp],
    ) -> None:
        if filter_param not in RunTriggerFilterOp:
            raise InvalidRunTriggerTypeError()
        if len(include_param) > 0:
            if filter_param != RunTriggerFilterOp.RUN_TRIGGER_INBOUND:
                raise UnsupportedRunTriggerTypeError()
        return None

    def backfill_deprecated_sourceable(self, rt: RunTrigger) -> None:
        if rt.sourceable or not rt.sourceable_choice:
            return

        rt.sourceable = rt.sourceable_choice.workspace
        return None
