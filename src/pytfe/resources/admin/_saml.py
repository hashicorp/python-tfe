# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from typing import Any, TypeVar

from pydantic import BaseModel

from ...models.admin_identity import (
    AdminSAMLSettings,
    AdminSAMLSettingsUpdateOptions,
)
from .._base import _Service

_SAML_TYPE = "saml-settings"

_M = TypeVar("_M", bound=BaseModel)


def _parse_jsonapi(data: dict[str, Any], model: type[_M]) -> _M:
    attrs = data.get("attributes") or {}
    return model.model_validate({"id": data.get("id"), **attrs})


class _AdminSAMLSettings(_Service):
    def read(self) -> AdminSAMLSettings:
        r = self.t.request("GET", "/api/v2/admin/saml-settings")
        return _parse_jsonapi(r.json()["data"], AdminSAMLSettings)

    def update(self, options: AdminSAMLSettingsUpdateOptions) -> AdminSAMLSettings:
        attrs = options.model_dump(by_alias=True, exclude_none=True, mode="json")
        body = {"data": {"type": _SAML_TYPE, "attributes": attrs}}
        r = self.t.request("PATCH", "/api/v2/admin/saml-settings", json_body=body)
        return _parse_jsonapi(r.json()["data"], AdminSAMLSettings)

    def revoke_idp_cert(self) -> AdminSAMLSettings:
        r = self.t.request(
            "POST",
            "/api/v2/admin/saml-settings/actions/revoke-old-certificate",
        )
        return _parse_jsonapi(r.json()["data"], AdminSAMLSettings)
