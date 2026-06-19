# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from .._jsonapi import RelationMap, attach_jsonapi, parse_relationships
from ..errors import (
    InvalidOrgError,
    InvalidRunIDError,
    InvalidWorkspaceIDError,
    RequiredWorkspaceError,
    TerraformVersionValidForPlanOnlyError,
)
from ..models.apply import Apply
from ..models.comment import Comment
from ..models.configuration_version import ConfigurationVersion
from ..models.cost_estimate import CostEstimate
from ..models.plan import Plan
from ..models.policy_check import PolicyCheck
from ..models.run import (
    Run,
    RunApplyOptions,
    RunCancelOptions,
    RunCreateOptions,
    RunDiscardOptions,
    RunForceCancelOptions,
    RunListForOrganizationOptions,
    RunListOptions,
    RunReadOptions,
)
from ..models.run_event import RunEvent
from ..models.task_stage import TaskStage
from ..models.user import User
from ..models.workspace import Workspace
from ..utils import _safe_str, valid_string, valid_string_id
from ._base import _Service

_RUN_REL_MAP: RelationMap = {
    "apply": Apply,
    "configuration-version": ConfigurationVersion,
    "cost-estimate": CostEstimate,
    "created-by": User,
    "confirmed-by": User,
    "plan": Plan,
    "workspace": Workspace,
    "policy-checks": PolicyCheck,
    "run-events": RunEvent,
    "task-stages": TaskStage,
    "comments": Comment,
}


def _run_from(d: dict[str, Any], included: list[dict[str, Any]] | None = None) -> Run:
    """Parse a JSON:API run resource into a Run, hydrating relations."""
    attr = dict(d.get("attributes") or {})
    attr["id"] = _safe_str(d.get("id"))
    attr.update(
        parse_relationships(d.get("relationships"), _RUN_REL_MAP, included=included)
    )
    # Keep raw relationships + included so unmodeled relations are never lost.
    return attach_jsonapi(Run.model_validate(attr), d, included)


class Runs(_Service):
    def list(
        self, workspace_id: str, options: RunListOptions | None = None
    ) -> Iterator[Run]:
        """List all runs in a workspace.

        Args:
            workspace_id: The workspace ID (e.g. ``"ws-xxxxxxxx"``).
            options: Optional filters and pagination, as a :class:`RunListOptions`.

        Returns:
            A single-use ``Iterator[Run]``. Wrap with ``list(...)`` to materialize
            the results or iterate more than once.

        Raises:
            InvalidWorkspaceIDError: If ``workspace_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import RunListOptions
            >>> for run in client.runs.list(
            ...     "ws-6fHMCom98SDXSQUv",
            ...     RunListOptions(status="planned"),
            ... ):
            ...     print(run.id, run.status)
        """
        if not valid_string_id(workspace_id):
            raise InvalidWorkspaceIDError()
        params = options.model_dump(by_alias=True) if options else {}
        path = f"/api/v2/workspaces/{workspace_id}/runs"
        for item in self._list(path, params=params):
            yield _run_from(item)

    def list_for_organization(
        self, organization: str, options: RunListForOrganizationOptions | None = None
    ) -> Iterator[Run]:
        """List all runs in an organization.

        Args:
            organization: The organization name (e.g. ``"my-org"``).
            options: Optional filters and pagination, as a
                :class:`RunListForOrganizationOptions`.

        Returns:
            A single-use ``Iterator[Run]``. Wrap with ``list(...)`` to materialize
            the results or iterate more than once.

        Raises:
            InvalidOrgError: If ``organization`` is not a valid organization name.
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import RunListForOrganizationOptions
            >>> runs = client.runs.list_for_organization(
            ...     "my-org",
            ...     RunListForOrganizationOptions(status="applied,planned"),
            ... )
            >>> for run in runs:
            ...     print(run.id, run.status)
        """
        if not valid_string_id(organization):
            raise InvalidOrgError()
        path = f"/api/v2/organizations/{organization}/runs"
        params = options.model_dump(by_alias=True, exclude_none=True) if options else {}
        # meta = jd.get("meta", {})
        # pagination = meta.get("pagination", {})
        for item in self._list(path, params=params):
            yield _run_from(item)

    def create(self, options: RunCreateOptions) -> Run:
        """Create a new run.

        Args:
            options: The run configuration, as a :class:`RunCreateOptions`; include
                a ``Workspace`` with an ID such as ``"ws-xxxxxxxx"``.

        Returns:
            The created :class:`Run`.

        Raises:
            RequiredWorkspaceError: If ``options.workspace`` is missing.
            TerraformVersionValidForPlanOnlyError: If ``terraform_version`` is set
                without ``plan_only=True``.
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import RunCreateOptions, Workspace
            >>> run = client.runs.create(
            ...     RunCreateOptions(
            ...         workspace=Workspace(id="ws-6fHMCom98SDXSQUv"),
            ...         message="Run from automation",
            ...     )
            ... )
        """
        if options.workspace is None:
            raise RequiredWorkspaceError()
        if valid_string(options.terraform_version) and (
            options.plan_only is None or not options.plan_only
        ):
            raise TerraformVersionValidForPlanOnlyError()
        attrs = options.model_dump(by_alias=True, exclude_none=True)
        body: dict[str, Any] = {
            "data": {
                "attributes": attrs,
                "type": "runs",
            }
        }
        if options.workspace:
            body["data"]["relationships"] = {
                "workspace": {
                    "data": {
                        "type": "workspaces",
                        "id": options.workspace.id,
                    }
                }
            }
        if options.configuration_version:
            if "relationships" not in body["data"]:
                body["data"]["relationships"] = {}
            body["data"]["relationships"]["configuration-version"] = {
                "data": {
                    "type": "configuration-versions",
                    "id": options.configuration_version.id,
                }
            }
        r = self.t.request(
            "POST",
            "/api/v2/runs",
            json_body=body,
        )
        return _run_from(r.json().get("data", {}))

    def read(self, run_id: str) -> Run:
        """Read a run by its ID.

        Args:
            run_id: The run ID (e.g. ``"run-xxxxxxxx"``).

        Returns:
            The :class:`Run`.

        Raises:
            TFEError: If the API request fails.

        Example:
            >>> run = client.runs.read("run-CZcmD7eagjhyX0vN")
            >>> print(run.status)
        """
        return self.read_with_options(run_id)

    def read_with_options(
        self, run_id: str, options: RunReadOptions | None = None
    ) -> Run:
        """Read a run by its ID with include options.

        Args:
            run_id: The run ID (e.g. ``"run-xxxxxxxx"``).
            options: Optional relationship includes, as a :class:`RunReadOptions`.

        Returns:
            The :class:`Run`.

        Raises:
            InvalidRunIDError: If ``run_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import RunIncludeOpt, RunReadOptions
            >>> run = client.runs.read_with_options(
            ...     "run-CZcmD7eagjhyX0vN",
            ...     RunReadOptions(include=[RunIncludeOpt.RUN_PLAN]),
            ... )
        """
        if not valid_string_id(run_id):
            raise InvalidRunIDError()
        params: dict[str, Any] = {}
        if options and options.include:
            params["include"] = ",".join(options.include)
        r = self.t.request(
            "GET",
            f"/api/v2/runs/{run_id}",
            params=params,
        )
        payload = r.json()
        return _run_from(payload.get("data", {}), payload.get("included"))

    def apply(self, run_id: str, options: RunApplyOptions | None = None) -> None:
        """Apply a run by its ID.

        Args:
            run_id: The run ID (e.g. ``"run-xxxxxxxx"``).
            options: Optional apply comment, as a :class:`RunApplyOptions`.

        Returns:
            None.

        Raises:
            InvalidRunIDError: If ``run_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import RunApplyOptions
            >>> client.runs.apply(
            ...     "run-CZcmD7eagjhyX0vN",
            ...     RunApplyOptions(comment="Approved by automation"),
            ... )
        """
        if not valid_string_id(run_id):
            raise InvalidRunIDError()
        body = {"comment": options.comment} if options and options.comment else None
        self.t.request("POST", f"/api/v2/runs/{run_id}/actions/apply", json_body=body)

        return None

    def cancel(self, run_id: str, options: RunCancelOptions | None = None) -> None:
        """Cancel a run by its ID.

        Args:
            run_id: The run ID (e.g. ``"run-xxxxxxxx"``).
            options: Optional cancel comment, as a :class:`RunCancelOptions`.

        Returns:
            None.

        Raises:
            InvalidRunIDError: If ``run_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import RunCancelOptions
            >>> client.runs.cancel(
            ...     "run-CZcmD7eagjhyX0vN",
            ...     RunCancelOptions(comment="Superseded by a newer run"),
            ... )
        """
        if not valid_string_id(run_id):
            raise InvalidRunIDError()
        body = {"comment": options.comment} if options and options.comment else None
        self.t.request("POST", f"/api/v2/runs/{run_id}/actions/cancel", json_body=body)
        return None

    def force_cancel(
        self, run_id: str, options: RunForceCancelOptions | None = None
    ) -> None:
        """Forcefully cancel a run by its ID.

        Args:
            run_id: The run ID (e.g. ``"run-xxxxxxxx"``).
            options: Optional force-cancel comment, as a
                :class:`RunForceCancelOptions`.

        Returns:
            None.

        Raises:
            InvalidRunIDError: If ``run_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import RunForceCancelOptions
            >>> client.runs.force_cancel(
            ...     "run-CZcmD7eagjhyX0vN",
            ...     RunForceCancelOptions(comment="Run is stuck"),
            ... )
        """
        if not valid_string_id(run_id):
            raise InvalidRunIDError()
        body = {"comment": options.comment} if options and options.comment else None
        self.t.request(
            "POST", f"/api/v2/runs/{run_id}/actions/force-cancel", json_body=body
        )
        return None

    def force_execute(self, run_id: str) -> None:
        """Forcefully execute a run by its ID.

        Args:
            run_id: The run ID (e.g. ``"run-xxxxxxxx"``).

        Returns:
            None.

        Raises:
            InvalidRunIDError: If ``run_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> client.runs.force_execute("run-CZcmD7eagjhyX0vN")
        """
        if not valid_string_id(run_id):
            raise InvalidRunIDError()
        self.t.request("POST", f"/api/v2/runs/{run_id}/actions/force-execute")
        return None

    def discard(self, run_id: str, options: RunDiscardOptions | None = None) -> None:
        """Discard a run by its ID.

        Args:
            run_id: The run ID (e.g. ``"run-xxxxxxxx"``).
            options: Optional discard comment, as a :class:`RunDiscardOptions`.

        Returns:
            None.

        Raises:
            InvalidRunIDError: If ``run_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import RunDiscardOptions
            >>> client.runs.discard(
            ...     "run-CZcmD7eagjhyX0vN",
            ...     RunDiscardOptions(comment="No longer needed"),
            ... )
        """
        if not valid_string_id(run_id):
            raise InvalidRunIDError()
        body = {"comment": options.comment} if options and options.comment else None
        self.t.request("POST", f"/api/v2/runs/{run_id}/actions/discard", json_body=body)
        return None
