# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from ..errors import InvalidApplyIDError
from ..models.apply import (
    Apply,
)
from ..utils import valid_string_id, validate_log_url
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

    def logs(self, apply_id: str) -> str:
        """Get logs for a specific apply"""
        # Validate apply ID
        if not valid_string_id(apply_id):
            raise InvalidApplyIDError()

        # Get the apply and validate log URL
        apply = self.read(apply_id)
        if not apply.log_read_url:
            raise ValueError(f"Apply {apply_id} does not have a log URL")

        validate_log_url(apply.log_read_url)

        # Placeholder implementation - in future this would stream logs
        return ""

    def _done(self, apply_id: str) -> tuple[bool, Exception | None]:
        """Check if an apply is in a terminal state."""
        try:
            apply_obj = self.read(apply_id)
            terminal_states = {"canceled", "errored", "finished", "unreachable"}
            is_complete = apply_obj.status in terminal_states
            return is_complete, None
        except Exception as e:
            return False, e

    def errored_state(self, apply_id: str) -> bytes:
        """Recover the raw state bytes from an apply that failed during state upload.

        The TFE endpoint returns a 307 redirect to a signed object-storage URL.
        We follow it manually so the API bearer token is not forwarded to the
        third-party blob host.

        Raises NotFound if the apply has no recoverable errored state.
        """
        if not valid_string_id(apply_id):
            raise InvalidApplyIDError()

        # Do not auto-follow: the redirect target is presigned and must not
        # receive our Authorization header.
        resp = self.t.request(
            "GET",
            f"/api/v2/applies/{apply_id}/errored-state",
            allow_redirects=False,
        )
        if resp.status_code in (301, 302, 303, 307, 308):
            location = resp.headers.get("Location") or resp.headers.get("location")
            if not location:
                from ..errors import TFEError

                raise TFEError(
                    "errored-state redirect did not include a Location header"
                )
            blob = self.t.request("GET", location)
            return blob.content
        # 2xx body case (some servers may return inline); honour it
        return resp.content
