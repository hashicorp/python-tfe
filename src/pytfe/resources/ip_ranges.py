# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from datetime import datetime, timezone
from email.utils import format_datetime

from ..models.ip_range import IPRange
from ._base import _Service


class IPRanges(_Service):
    """Service for reading HCP Terraform / Terraform Enterprise IP ranges."""

    def read(self, modified_since: datetime | None = None) -> IPRange | None:
        """Read the published outbound IP ranges.

        ``GET /api/meta/ip-ranges`` returns a bare JSON object of CIDR lists
        (``api``, ``notifications``, ``sentinel``, ``vcs``). The endpoint does
        not require authentication.

        When ``modified_since`` is provided, an ``If-Modified-Since`` request
        header is sent; if the ranges have not changed since that time the API
        replies ``304 Not Modified`` and this returns ``None``.
        """
        headers: dict[str, str] = {"Accept": "application/json, */*"}
        if modified_since is not None:
            dt = modified_since
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            headers["If-Modified-Since"] = format_datetime(
                dt.astimezone(timezone.utc), usegmt=True
            )

        # allow_redirects=False lets the transport surface the 304 response
        # (it would otherwise be raised as an error) so we can map it to None.
        r = self.t.request(
            "GET", "/api/meta/ip-ranges", headers=headers, allow_redirects=False
        )
        if r.status_code == 304:
            return None
        return IPRange.model_validate(r.json())
