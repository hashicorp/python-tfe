from __future__ import annotations

from collections.abc import Callable
from typing import Any

from ..errors import InvalidPlanIDError
from ..log_reader import LogReader
from ..models.plan import (
    Plan,
    PlanStatus,
)
from ..utils import valid_string_id
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

    def logs_reader(self, plan_id: str) -> LogReader:
        """Get a LogReader for streaming logs from a specific plan.

        This method follows the Go LogReader pattern, providing:
        - Chunked reading with offset/limit parameters
        - Status checking to determine when logs are complete
        - STX/ETX control character handling
        - Exponential backoff for retries

        Returns:
            LogReader instance for streaming logs

        Usage:
            # Stream logs chunk by chunk (async)
            log_reader = plans.logs_reader("plan-123")
            buffer = bytearray(4096)
            while True:
                n, err = await log_reader.read(buffer)
                if n > 0:
                    print(buffer[:n].decode('utf-8', errors='ignore'), end='')
                if err:
                    break

            # Or get all logs at once (async)
            all_logs = await log_reader.read_all()

            # Or use the convenience logs() method for synchronous access
            all_logs = plans.logs("plan-123")
        """
        # Validate plan ID
        if not valid_string_id(plan_id):
            raise InvalidPlanIDError()

        # Get the plan and validate log URL
        plan = self.read(plan_id)
        self._validate_log_url(plan.log_read_url, plan_id)

        # Create done function for status checking
        done_func = lambda: self._done(plan_id)

        # Return LogReader configured with transport, URL, and done function
        return LogReader(
            transport=self.t,
            log_url=plan.log_read_url,
            done_func=done_func,
        )

    def logs(self, plan_id: str) -> str:
        """Get all logs for a specific plan as a string.

        This is a convenience method that uses logs_reader() internally
        to fetch all logs at once. For streaming logs, use logs_reader() instead.

        Args:
            plan_id: Plan ID to get logs for

        Returns:
            Complete log content as string
        """
        import asyncio
        
        log_reader = self.logs_reader(plan_id)
        return asyncio.run(log_reader.read_all())

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
        """
        Create a done function for plan log reading.

        Args:
            plan_id: Plan ID to check

        Returns:
            Function that returns boolean
        """
        plan = self.read(plan_id)
        terminal_states = {
            PlanStatus.PLAN_CANCELED,
            PlanStatus.PLAN_ERRORED,
            PlanStatus.PLAN_FINISHED,
            PlanStatus.PLAN_UNREACHABLE,
        }
        return plan.status in terminal_states

    def _validate_log_url(self, log_url: str, resource_id: str) -> None:
        """
        Validate that a log URL exists and has the correct format.

        Args:
            log_url: The log URL to validate
            resource_id: The resource ID for error messages

        Raises:
            ValueError: If the log URL is invalid or empty
        """
        if not log_url:
            raise ValueError(f"Plan {resource_id} does not have a log URL")

        from urllib.parse import urlparse

        try:
            parsed_url = urlparse(log_url)
            if not parsed_url.scheme or not parsed_url.netloc:
                raise ValueError(f"Invalid log URL format: {log_url}")
        except Exception as e:
            raise ValueError(f"Invalid log URL: {log_url}") from e
