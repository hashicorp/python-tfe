from __future__ import annotations

from collections.abc import Callable

from ..errors import InvalidApplyIDError
from ..log_reader import LogReader
from ..models.apply import (
    Apply,
)
from ..utils import valid_string_id
from ._base import _Service


class Applies(_Service):
    def read(self, apply_id: str) -> Apply:
        """Read a specific apply by its ID."""
        if not valid_string_id(apply_id):
            raise InvalidApplyIDError()

        r = self.t.request(
            "GET",
            f"/api/v2/applies/{apply_id}",
        )
        d = r.json()["data"]
        attr = d.get("attributes", {}) or {}
        return Apply(
            id=d.get("id"),
            **{k.replace("-", "_"): v for k, v in attr.items()},
        )

    def logs_reader(self, apply_id: str) -> LogReader:
        """Get a LogReader for streaming logs from a specific apply.

        This method follows the Go LogReader pattern, providing:
        - Chunked reading with offset/limit parameters
        - Status checking to determine when logs are complete
        - STX/ETX control character handling
        - Exponential backoff for retries

        Returns:
            LogReader instance for streaming logs

        Usage:
            # Stream logs chunk by chunk (async)
            log_reader = applies.logs_reader("apply-123")
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
            all_logs = applies.logs("apply-123")
        """
        # Validate apply ID
        if not valid_string_id(apply_id):
            raise InvalidApplyIDError()

        # Get the apply and validate log URL
        apply = self.read(apply_id)
        self._validate_log_url(apply.log_read_url, apply_id)

        # Create done function for status checking
        done_func = lambda: self._done(apply_id)

        # Return LogReader configured with transport, URL, and done function
        return LogReader(
            transport=self.t,
            log_url=apply.log_read_url,
            done_func=done_func,
        )

    def logs(self, apply_id: str) -> str:
        """Get all logs for a specific apply as a string.

        This is a convenience method that uses logs_reader() internally
        to fetch all logs at once. For streaming logs, use logs_reader() instead.

        Args:
            apply_id: Apply ID to get logs for

        Returns:
            Complete log content as string
        """
        import asyncio
        
        log_reader = self.logs_reader(apply_id)
        return asyncio.run(log_reader.read_all())

    def _done(self, apply_id: str) -> tuple[bool, Exception | None]:
        """
        Check if an apply is in a terminal state.

        Args:
            apply_id: Apply ID to check

        Returns:
            Tuple of (is_complete, error)
        """
        try:
            apply_obj = self.read(apply_id)
            terminal_states = {"canceled", "errored", "finished", "unreachable"}
            is_complete = apply_obj.status in terminal_states
            return is_complete, None
        except Exception as e:
            return False, e

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
            raise ValueError(f"Apply {resource_id} does not have a log URL")

        from urllib.parse import urlparse

        try:
            parsed_url = urlparse(log_url)
            if not parsed_url.scheme or not parsed_url.netloc:
                raise ValueError(f"Invalid log URL format: {log_url}")
        except Exception as e:
            raise ValueError(f"Invalid log URL: {log_url}") from e
