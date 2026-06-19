# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from typing import Any, TypeVar

from pydantic import BaseModel

from ...models.admin_identity import (
    AdminSMTPSettings,
    AdminSMTPSettingsUpdateOptions,
)
from .._base import _Service

_SMTP_TYPE = "smtp-settings"

_M = TypeVar("_M", bound=BaseModel)


def _parse_jsonapi(data: dict[str, Any], model: type[_M]) -> _M:
    attrs = data.get("attributes") or {}
    return model.model_validate({"id": data.get("id"), **attrs})


class _AdminSMTPSettings(_Service):
    def read(self) -> AdminSMTPSettings:
        """Read the TFE site SMTP settings.

        Returns:
            The :class:`AdminSMTPSettings`.

        Raises:
            TFEError: If the API request fails.

        Example:
            >>> settings = client.admin.smtp_settings.read()
            >>> print(settings.host)
        """
        r = self.t.request("GET", "/api/v2/admin/smtp-settings")
        return _parse_jsonapi(r.json()["data"], AdminSMTPSettings)

    def update(self, options: AdminSMTPSettingsUpdateOptions) -> AdminSMTPSettings:
        """Update the TFE site SMTP settings.

        Args:
            options: SMTP settings to update, as a
                :class:`AdminSMTPSettingsUpdateOptions`.

        Returns:
            The updated :class:`AdminSMTPSettings`.

        Raises:
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import AdminSMTPSettingsUpdateOptions, SMTPAuthType
            >>> settings = client.admin.smtp_settings.update(
            ...     AdminSMTPSettingsUpdateOptions(
            ...         host="smtp.example.com", port=587, auth=SMTPAuthType.PLAIN
            ...     )
            ... )
        """
        attrs = options.model_dump(by_alias=True, exclude_none=True, mode="json")
        body = {"data": {"type": _SMTP_TYPE, "attributes": attrs}}
        r = self.t.request("PATCH", "/api/v2/admin/smtp-settings", json_body=body)
        return _parse_jsonapi(r.json()["data"], AdminSMTPSettings)
