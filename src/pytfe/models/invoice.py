# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""Model for an organization's billing invoices."""

from __future__ import annotations

from datetime import datetime

from pydantic import ConfigDict, Field

from ._base import TFEModel


class Invoice(TFEModel):
    """A billing invoice (JSON:API type ``billing-invoices``).

    ``total`` is the invoice amount in the smallest currency unit (e.g. cents).
    ``status`` mirrors the billing provider's status (e.g. ``paid``, ``draft``,
    ``open``); it is left untyped so new statuses do not break parsing.
    """

    model_config = ConfigDict(
        populate_by_name=True, validate_by_name=True, extra="allow"
    )

    id: str
    created_at: datetime | None = Field(default=None, alias="created-at")
    external_link: str | None = Field(default=None, alias="external-link")
    number: str | None = None
    paid: bool | None = None
    status: str | None = None
    total: int | None = None
