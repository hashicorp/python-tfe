# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from typing import Any

from ..errors import InvalidPlanIDError, InvalidRunIDError
from ..models.plan import (
    Plan,
    PlanStatus,
)
from ..utils import valid_string_id, validate_log_url
from ._base import _Service


def _plan_from_jsonapi(d: dict[str, Any]) -> Plan:
    attr = d.get("attributes", {}) or {}
    return Plan(
        id=d.get("id"),
        **{k.replace("-", "_"): v for k, v in attr.items()},
    )


class Plans(_Service):
    def read(self, plan_id: str) -> Plan:
        """Read a specific plan by its ID."""
        if not valid_string_id(plan_id):
            raise InvalidPlanIDError()

        r = self.t.request(
            "GET",
            f"/api/v2/plans/{plan_id}",
        )
        return _plan_from_jsonapi(r.json()["data"])

    def read_for_run(self, run_id: str) -> Plan:
        """Read the plan belonging to a run, via the run id."""
        if not valid_string_id(run_id):
            raise InvalidRunIDError()
        r = self.t.request("GET", f"/api/v2/runs/{run_id}/plan")
        return _plan_from_jsonapi(r.json()["data"])

    def logs(self, plan_id: str) -> str:
        """Get logs for a specific plan.

        Args:
            plan_id: Plan ID to get logs for

        Returns:
            Log content as string (placeholder implementation)
        """
        # Validate plan ID
        if not valid_string_id(plan_id):
            raise InvalidPlanIDError()

        # Get the plan and validate log URL
        plan = self.read(plan_id)
        if not plan.log_read_url:
            raise ValueError(f"Plan {plan_id} does not have a log URL")

        validate_log_url(plan.log_read_url)

        # Placeholder implementation - in future this would stream logs
        return ""

    def _follow_json_output_redirect(self, path: str) -> dict[str, Any]:
        """Fetch a json-output endpoint that returns 307 → presigned blob URL.

        The redirect target is a presigned object-storage URL; the API bearer
        token must not be forwarded to it.
        """
        resp = self.t.request("GET", path, allow_redirects=False)
        if resp.status_code in (301, 302, 303, 307, 308):
            location = resp.headers.get("Location") or resp.headers.get("location")
            if not location:
                from ..errors import TFEError

                raise TFEError(
                    "json-output redirect did not include a Location header"
                )
            blob = self.t.request("GET", location, include_auth=False)
            data = blob.json()
        else:
            data = resp.json()
        if isinstance(data, dict):
            return data
        return {"data": data}

    def read_json_output(self, plan_id: str) -> dict[str, Any]:
        """Get the JSON execution plan for a specific plan by its ID.

        Returns the JSON representation of the Terraform execution plan,
        which includes detailed information about planned changes.
        """
        if not valid_string_id(plan_id):
            raise InvalidPlanIDError()
        return self._follow_json_output_redirect(
            f"/api/v2/plans/{plan_id}/json-output"
        )

    def read_json_output_for_run(self, run_id: str) -> dict[str, Any]:
        """Get the JSON execution plan for a run, via the run id."""
        if not valid_string_id(run_id):
            raise InvalidRunIDError()
        return self._follow_json_output_redirect(
            f"/api/v2/runs/{run_id}/plan/json-output"
        )

    def read_json_schema_for_run(self, run_id: str) -> dict[str, Any]:
        """Get the provider JSON schema corresponding to a plan, via the run id."""
        if not valid_string_id(run_id):
            raise InvalidRunIDError()
        return self._follow_json_output_redirect(
            f"/api/v2/runs/{run_id}/plan/json-schema"
        )

    def _done(self, plan_id: str) -> bool:
        """Create a done function for plan log reading."""
        plan = self.read(plan_id)
        terminal_states = {
            PlanStatus.PLAN_CANCELED,
            PlanStatus.PLAN_ERRORED,
            PlanStatus.PLAN_FINISHED,
            PlanStatus.PLAN_UNREACHABLE,
        }
        return plan.status in terminal_states
