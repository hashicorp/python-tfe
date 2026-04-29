# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

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


def transform_relationships(relationships: dict) -> Any:
    """
    Transform relationships dict to map relationship names to their model objects.
    Single IDs become model instances, multiple IDs become lists of model instances.
    """
    result = {}

    # Map relationship keys to their model constructors
    model_map = {
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

    for key, value in relationships.items():
        data = value.get("data")

        if data is None:
            continue

        model_class = model_map.get(key)
        if not model_class:
            # Unknown relationship type, skip it
            continue

        if isinstance(data, list):
            # Multiple entries - create list of model instances
            result[key] = [model_class(id=item["id"]) for item in data if "id" in item]
        elif isinstance(data, dict) and "id" in data:
            # Single entry - create model instance
            result[key] = model_class(id=data["id"])

    return result


class Runs(_Service):
    def list(
        self, workspace_id: str, options: RunListOptions | None = None
    ) -> Iterator[Run]:
        """List all the runs of the given workspace."""
        if not valid_string_id(workspace_id):
            raise InvalidWorkspaceIDError()
        params = options.model_dump(by_alias=True) if options else {}
        path = f"/api/v2/workspaces/{workspace_id}/runs"
        for item in self._list(path, params=params):
            attrs = item.get("attributes", {})
            attrs["id"] = item.get("id")
            yield Run.model_validate(attrs)

    def list_for_organization(
        self, organization: str, options: RunListForOrganizationOptions | None = None
    ) -> Iterator[Run]:
        """List all the runs of the given organization."""
        if not valid_string_id(organization):
            raise InvalidOrgError()
        path = f"/api/v2/organizations/{organization}/runs"
        params = options.model_dump(by_alias=True, exclude_none=True) if options else {}
        # meta = jd.get("meta", {})
        # pagination = meta.get("pagination", {})
        for item in self._list(path, params=params):
            attrs = item.get("attributes", {})
            attrs["id"] = item.get("id")
            yield Run.model_validate(attrs)

    def create(self, options: RunCreateOptions) -> Run:
        """Create a new run for the given workspace."""
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
        d = r.json().get("data", {})
        attrs = d.get("attributes", {})
        relationships = transform_relationships(d.get("relationships", {}))
        combined = {
            k.replace("-", "_"): v for k, v in {**attrs, **relationships}.items()
        }
        return Run(id=_safe_str(d.get("id")), **combined)

    def read(self, run_id: str) -> Run:
        """Read a run by its ID."""
        return self.read_with_options(run_id)

    def read_with_options(
        self, run_id: str, options: RunReadOptions | None = None
    ) -> Run:
        """Read a run by its ID with the given options."""
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
        d = r.json().get("data", {})
        attrs = d.get("attributes", {})
        relationships = transform_relationships(d.get("relationships", {}))
        combined = {
            k.replace("-", "_"): v for k, v in {**attrs, **relationships}.items()
        }
        return Run(id=_safe_str(d.get("id")), **combined)

    def apply(self, run_id: str, options: RunApplyOptions | None = None) -> None:
        """Apply a run by its ID."""
        if not valid_string_id(run_id):
            raise InvalidRunIDError()
        body = {"comment": options.comment} if options and options.comment else None
        self.t.request("POST", f"/api/v2/runs/{run_id}/actions/apply", json_body=body)

        return None

    def cancel(self, run_id: str, options: RunCancelOptions | None = None) -> None:
        """Cancel a run by its ID."""
        if not valid_string_id(run_id):
            raise InvalidRunIDError()
        body = {"comment": options.comment} if options and options.comment else None
        self.t.request("POST", f"/api/v2/runs/{run_id}/actions/cancel", json_body=body)
        return None

    def force_cancel(
        self, run_id: str, options: RunForceCancelOptions | None = None
    ) -> None:
        """ForceCancel is used to forcefully cancel a run by its ID."""
        if not valid_string_id(run_id):
            raise InvalidRunIDError()
        body = {"comment": options.comment} if options and options.comment else None
        self.t.request(
            "POST", f"/api/v2/runs/{run_id}/actions/force-cancel", json_body=body
        )
        return None

    def force_execute(self, run_id: str) -> None:
        """ForceExecute is used to forcefully execute a run by its ID."""
        if not valid_string_id(run_id):
            raise InvalidRunIDError()
        self.t.request("POST", f"/api/v2/runs/{run_id}/actions/force-execute")
        return None

    def discard(self, run_id: str, options: RunDiscardOptions | None = None) -> None:
        """Discard a run by its ID."""
        if not valid_string_id(run_id):
            raise InvalidRunIDError()
        body = {"comment": options.comment} if options and options.comment else None
        self.t.request("POST", f"/api/v2/runs/{run_id}/actions/discard", json_body=body)
        return None
