from __future__ import annotations

from typing import Any

from ..errors import InvalidPlanIDError
from ..models.plan import (
    Plan,
    PlanStatus,
)
from ..utils import valid_string_id, validate_log_url
from ._base import _Service


class Plans(_Service):
    def read(self, plan_id: str) -> Plan:
        """Read a specific plan by its ID."""
        if not valid_string_id(plan_id):
            raise InvalidPlanIDError()

        r = self.t.request(
            "GET",
            f"/api/v2/plans/{plan_id}",
        )
        d = r.json()["data"]
        attr = d.get("attributes", {}) or {}
        return Plan(
            id=d.get("id"),
            **{k.replace("-", "_"): v for k, v in attr.items()},
        )

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

    def read_json_output(self, plan_id: str) -> dict[str, Any]:
        """Get the JSON execution plan for a specific plan by its ID.

        Returns the JSON representation of the Terraform execution plan,
        which includes detailed information about planned changes.
        """
        if not valid_string_id(plan_id):
            raise InvalidPlanIDError()

        r = self.t.request(
            "GET",
            f"/api/v2/plans/{plan_id}/json-output",
        )

        # Return the raw JSON data - this endpoint returns JSON directly
        # not wrapped in a JSON:API format
        json_data = r.json()
        # Ensure we return a dictionary, not Any
        if isinstance(json_data, dict):
            return json_data
        else:
            # If somehow the response isn't a dict, wrap it
            return {"data": json_data}

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
