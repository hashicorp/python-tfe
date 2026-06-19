# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import builtins
from collections.abc import Iterator
from datetime import datetime
from typing import Any

from .._jsonapi import attach_jsonapi
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
from ..utils import _safe_str, valid_string_id
from ._base import _Service


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
    workspace = Workspace.model_validate(
        {"id": workspace_id, "name": workspace_name_str, "organization": org}
    )
    sourceable = Workspace.model_validate(
        {"id": sourceable_id, "name": sourceable_name_str, "organization": org}
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

    return attach_jsonapi(
        RunTrigger(
            id=id_str,
            created_at=created_at,
            sourceable_name=sourceable_name_str,
            workspace_name=workspace_name_str,
            sourceable=sourceable,
            sourceable_choice=sourceable_choice,
            workspace=workspace,
        ),
        d,
    )


class RunTriggers(_Service):
    def list(
        self, workspace_id: str, options: RunTriggerListOptions | None = None
    ) -> Iterator[RunTrigger]:
        """List run triggers for a workspace.

        Args:
            workspace_id: The workspace ID (e.g. ``"ws-xxxxxxxx"``).
            options: The required run-trigger filters, as a
                :class:`RunTriggerListOptions`.

        Returns:
            A single-use ``Iterator[RunTrigger]``. Wrap with ``list(...)`` to
            materialize the results or iterate more than once.

        Raises:
            InvalidWorkspaceIDError: If ``workspace_id`` is not a valid resource ID.
            RequiredRunTriggerListOpsError: If ``options`` is not supplied.
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import RunTriggerFilterOp, RunTriggerListOptions
            >>> options = RunTriggerListOptions(
            ...     run_trigger_type=RunTriggerFilterOp.RUN_TRIGGER_OUTBOUND
            ... )
            >>> for trigger in client.run_triggers.list("ws-4j8p6jX1w33MiDC7", options):
            ...     print(trigger.id, trigger.sourceable_name)
        """
        if not valid_string_id(workspace_id):
            raise InvalidWorkspaceIDError()
        if not options:
            raise RequiredRunTriggerListOpsError()
        self.validate_run_trigger_filter_param(
            options.run_trigger_type, options.include or []
        )
        params: dict[str, str] = {}
        if options is not None:
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
        """Create a run trigger for a workspace.

        Args:
            workspace_id: The destination workspace ID (e.g. ``"ws-xxxxxxxx"``).
            options: The source workspace relationship, as a
                :class:`RunTriggerCreateOptions`.

        Returns:
            The :class:`RunTrigger`.

        Raises:
            InvalidWorkspaceIDError: If ``workspace_id`` is not a valid resource ID.
            RequiredSourceableError: If ``options.sourceable`` is not supplied.
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import RunTriggerCreateOptions, Workspace
            >>> trigger = client.run_triggers.create(
            ...     "ws-4j8p6jX1w33MiDC7",
            ...     RunTriggerCreateOptions(
            ...         sourceable=Workspace.model_construct(id="ws-W2iULzoRNB5YHXXA")
            ...     ),
            ... )
        """
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
        """Read a run trigger by ID.

        Args:
            run_trigger_id: The run trigger ID (e.g. ``"rt-xxxxxxxx"``).

        Returns:
            The :class:`RunTrigger`.

        Raises:
            InvalidRunTriggerIDError: If ``run_trigger_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> trigger = client.run_triggers.read("rt-4j8p6jX1w33MiDC7")
            >>> print(trigger.workspace_name)
        """
        if not valid_string_id(run_trigger_id):
            raise InvalidRunTriggerIDError()
        path = f"/api/v2/run-triggers/{run_trigger_id}"
        r = self.t.request("GET", path)
        rt = _run_trigger_from(r.json()["data"])
        self.backfill_deprecated_sourceable(rt)
        return rt

    def delete(self, run_trigger_id: str) -> None:
        """Delete a run trigger by ID.

        Args:
            run_trigger_id: The run trigger ID (e.g. ``"rt-xxxxxxxx"``).

        Returns:
            None.

        Raises:
            InvalidRunTriggerIDError: If ``run_trigger_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> client.run_triggers.delete("rt-4j8p6jX1w33MiDC7")
        """
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
        """Validate run trigger filter and include compatibility.

        Args:
            filter_param: The run trigger filter, as a :class:`RunTriggerFilterOp`.
            include_param: Include relationships, as a list of
                :class:`RunTriggerIncludeOp` values.

        Returns:
            None.

        Raises:
            InvalidRunTriggerTypeError: If ``filter_param`` is invalid.
            UnsupportedRunTriggerTypeError: If includes are used with a non-inbound
                run trigger filter.

        Example:
            >>> from pytfe.models import RunTriggerFilterOp
            >>> client.run_triggers.validate_run_trigger_filter_param(
            ...     RunTriggerFilterOp.RUN_TRIGGER_OUTBOUND, []
            ... )
        """
        if filter_param not in RunTriggerFilterOp:
            raise InvalidRunTriggerTypeError()
        if len(include_param) > 0:
            if filter_param != RunTriggerFilterOp.RUN_TRIGGER_INBOUND:
                raise UnsupportedRunTriggerTypeError()
        return None

    def backfill_deprecated_sourceable(self, rt: RunTrigger) -> None:
        """Backfill the deprecated sourceable field from sourceable_choice.

        Args:
            rt: The run trigger to mutate, as a :class:`RunTrigger`.

        Returns:
            None.

        Example:
            >>> trigger = client.run_triggers.read("rt-4j8p6jX1w33MiDC7")
            >>> client.run_triggers.backfill_deprecated_sourceable(trigger)
        """
        if rt.sourceable or not rt.sourceable_choice:
            return

        rt.sourceable = rt.sourceable_choice.workspace
        return None
