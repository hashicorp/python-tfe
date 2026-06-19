# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""Read an organization's billing invoices (HCP Terraform only).

- ``GET /api/v2/organizations/{org}/invoices`` — previous invoices
- ``GET /api/v2/organizations/{org}/invoices/next`` — the upcoming invoice

The list endpoint uses a non-standard **cursor** pagination: the page size is
fixed at 10 and the next page is fetched with ``?cursor=<meta.continuation>``
until ``meta.continuation`` is null. ``self._list`` (page[number]/page[size])
does not apply, so the cursor loop is implemented here.

API reference:
https://developer.hashicorp.com/terraform/cloud-docs/api-docs/invoices
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from .._jsonapi import attach_jsonapi
from ..errors import InvalidOrgError
from ..models.invoice import Invoice
from ..utils import valid_string_id
from ._base import _Service


def _invoice_from(data: dict[str, Any]) -> Invoice:
    """Parse a JSON:API billing-invoices resource into an Invoice."""
    attrs = dict(data.get("attributes") or {})
    attrs["id"] = data.get("id")
    return attach_jsonapi(Invoice.model_validate(attrs), data)


class Invoices(_Service):
    """Service for reading organization billing invoices (HCP Terraform only)."""

    def list(self, organization: str) -> Iterator[Invoice]:
        """List an organization's previous invoices.

        The API uses cursor pagination; the SDK follows the continuation cursor until
        all invoices have been yielded.

        Args:
            organization: The organization name (e.g. ``"my-org"``).

        Returns:
            A single-use ``Iterator[Invoice]``. Wrap with ``list(...)`` to
            materialize the results or iterate more than once.

        Raises:
            InvalidOrgError: If ``organization`` is not a valid organization name.
            TFEError: If the API request fails.

        Example:
            >>> for invoice in client.invoices.list("my-org"):
            ...     print(invoice.number, invoice.total)
        """
        if not valid_string_id(organization):
            raise InvalidOrgError()
        path = f"/api/v2/organizations/{organization}/invoices"
        cursor: str | None = None
        while True:
            params = {"cursor": cursor} if cursor else {}
            body = self.t.request("GET", path, params=params).json()
            if not isinstance(body, dict):
                return
            for item in body.get("data") or []:
                yield _invoice_from(item)
            meta = body.get("meta") or {}
            cursor = meta.get("continuation") if isinstance(meta, dict) else None
            if not cursor:
                return

    def read_next(self, organization: str) -> Invoice | None:
        """Read the organization's next upcoming invoice.

        Args:
            organization: The organization name (e.g. ``"my-org"``).

        Returns:
            The :class:`Invoice` or ``None`` when there is no upcoming invoice (for
            example, the API responds ``200`` with a ``null`` body).

        Raises:
            InvalidOrgError: If ``organization`` is not a valid organization name.
            TFEError: If the API request fails.

        Example:
            >>> invoice = client.invoices.read_next("my-org")
            >>> print(invoice.number if invoice else "no upcoming invoice")
        """
        if not valid_string_id(organization):
            raise InvalidOrgError()
        r = self.t.request("GET", f"/api/v2/organizations/{organization}/invoices/next")
        body = r.json()
        data = body.get("data") if isinstance(body, dict) else None
        if not data:
            return None
        return _invoice_from(data)
