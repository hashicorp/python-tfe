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
    plan_id = str(d.get("id") or "")
    return Plan(
        id=plan_id,
        **{k.replace("-", "_"): v for k, v in attr.items()},
    )


class Plans(_Service):
    def read(self, plan_id: str) -> Plan:
        """Read a plan by its ID.

        Args:
            plan_id: The plan ID (e.g. ``"plan-xxxxxxxx"``).

        Returns:
            The :class:`Plan`.

        Raises:
            InvalidPlanIDError: If ``plan_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> plan = client.plans.read("plan-123")
            >>> print(plan.status)
        """
        if not valid_string_id(plan_id):
            raise InvalidPlanIDError()

        r = self.t.request(
            "GET",
            f"/api/v2/plans/{plan_id}",
        )
        return _plan_from_jsonapi(r.json()["data"])

    def read_for_run(self, run_id: str) -> Plan:
        """Read the plan for a run.

        Args:
            run_id: The run ID (e.g. ``"run-xxxxxxxx"``).

        Returns:
            The :class:`Plan`.

        Raises:
            InvalidRunIDError: If ``run_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> plan = client.plans.read_for_run("run-CZcmD7eagjhyX0vN")
            >>> print(plan.id)
        """
        if not valid_string_id(run_id):
            raise InvalidRunIDError()
        r = self.t.request("GET", f"/api/v2/runs/{run_id}/plan")
        return _plan_from_jsonapi(r.json()["data"])

    def logs(self, plan_id: str) -> str:
        """Get logs for a plan.

        Args:
            plan_id: The plan ID (e.g. ``"plan-xxxxxxxx"``).

        Returns:
            The ``str`` log content.

        Raises:
            InvalidPlanIDError: If ``plan_id`` is not a valid resource ID.
            ValueError: If the plan does not have a log URL.
            TFEError: If the API request fails.

        Example:
            >>> logs = client.plans.logs("plan-123")
            >>> print(logs)
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

    def _follow_json_output_redirect(self, path: str) -> dict[str, Any] | None:
        """Fetch a json-output endpoint that returns 307 → presigned blob URL.

        The redirect target is a presigned object-storage URL; the API bearer
        token must not be forwarded to it.

        Returns ``None`` if the API responds with 204 ("plan JSON supported,
        but plan has not yet completed"). Callers should check the plan's
        ``status`` before retrying.
        """
        resp = self.t.request("GET", path, allow_redirects=False)
        if resp.status_code == 204:
            return None
        if resp.status_code in (301, 302, 303, 307, 308):
            location = resp.headers.get("Location") or resp.headers.get("location")
            if not location:
                from ..errors import TFEError

                raise TFEError("json-output redirect did not include a Location header")
            blob = self.t.request("GET", location)
            data = blob.json()
        else:
            # Defensive: 2xx body case (some servers may return inline)
            try:
                data = resp.json()
            except Exception:
                return None
        if data is None:
            return None
        if isinstance(data, dict):
            return data
        return {"data": data}

    def read_json_output(self, plan_id: str) -> dict[str, Any] | None:
        """Read the JSON execution plan for a plan.

        Args:
            plan_id: The plan ID (e.g. ``"plan-xxxxxxxx"``).

        Returns:
            The ``dict[str, Any]`` (the SDK follows the storage/redirect URL
            for you), or ``None`` when the API returns HTTP 204 for an
            incomplete plan, or when the parsed body is empty; inline non-JSON
            responses also return ``None``.

        Raises:
            InvalidPlanIDError: If ``plan_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> output = client.plans.read_json_output("plan-123")
            >>> print(output["format_version"] if output else "not ready")
        """
        if not valid_string_id(plan_id):
            raise InvalidPlanIDError()
        return self._follow_json_output_redirect(f"/api/v2/plans/{plan_id}/json-output")

    def read_json_output_for_run(self, run_id: str) -> dict[str, Any] | None:
        """Read the JSON execution plan for a run.

        Args:
            run_id: The run ID (e.g. ``"run-xxxxxxxx"``).

        Returns:
            The ``dict[str, Any]`` (the SDK follows the storage/redirect URL
            for you), or ``None`` when the API returns HTTP 204 for an
            incomplete plan, or when the parsed body is empty; inline non-JSON
            responses also return ``None``.

        Raises:
            InvalidRunIDError: If ``run_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> output = client.plans.read_json_output_for_run(
            ...     "run-CZcmD7eagjhyX0vN"
            ... )
            >>> print(output["format_version"] if output else "not ready")
        """
        if not valid_string_id(run_id):
            raise InvalidRunIDError()
        return self._follow_json_output_redirect(
            f"/api/v2/runs/{run_id}/plan/json-output"
        )

    def read_json_schema_for_run(self, run_id: str) -> dict[str, Any] | None:
        """Read the provider JSON schema for a run's plan.

        Args:
            run_id: The run ID (e.g. ``"run-xxxxxxxx"``).

        Returns:
            The ``dict[str, Any]`` (the SDK follows the storage/redirect URL
            for you), or ``None`` when the API returns HTTP 204 for an
            incomplete plan, or when the parsed body is empty; inline non-JSON
            responses also return ``None``.

        Raises:
            InvalidRunIDError: If ``run_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> schema = client.plans.read_json_schema_for_run(
            ...     "run-CZcmD7eagjhyX0vN"
            ... )
            >>> print(schema.keys() if schema else "not ready")
        """
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
