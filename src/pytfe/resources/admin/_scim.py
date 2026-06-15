# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from collections.abc import Iterator
from typing import Any, TypeVar

from pydantic import BaseModel

from ...errors import (
    InvalidSCIMTokenIDError,
    RequiredSCIMTokenDescriptionError,
)
from ...models.admin_identity import (
    AdminSCIMSettings,
    AdminSCIMSettingsUpdateOptions,
    AdminSCIMToken,
    AdminSCIMTokenCreateOptions,
)
from ...utils import valid_string, valid_string_id
from .._base import _Service

_SCIM_SETTINGS_TYPE = "scim-settings"
# The TFE API uses the generic JSON:API type ``authentication-tokens``
# for SCIM tokens; the endpoint path namespaces them under /admin/scim-tokens
# but the resource type string in the body is the shared one.
_SCIM_TOKEN_TYPE = "authentication-tokens"

_M = TypeVar("_M", bound=BaseModel)


def _parse_jsonapi(data: dict[str, Any], model: type[_M]) -> _M:
    attrs = data.get("attributes") or {}
    return model.model_validate({"id": data.get("id"), **attrs})


class _AdminSCIMSettings(_Service):
    def read(self) -> AdminSCIMSettings:
        r = self.t.request("GET", "/api/v2/admin/scim-settings")
        return _parse_jsonapi(r.json()["data"], AdminSCIMSettings)

    def update(self, options: AdminSCIMSettingsUpdateOptions) -> AdminSCIMSettings:
        body = {
            "data": {
                "type": _SCIM_SETTINGS_TYPE,
                "attributes": options.to_payload(),
            }
        }
        r = self.t.request("PATCH", "/api/v2/admin/scim-settings", json_body=body)
        return _parse_jsonapi(r.json()["data"], AdminSCIMSettings)

    def delete(self) -> None:
        self.t.request("DELETE", "/api/v2/admin/scim-settings")


class _AdminSCIMTokens(_Service):
    def list(self) -> Iterator[AdminSCIMToken]:
        # The upstream endpoint is not documented as paginated, but the
        # response is still a JSON:API list. We use a single GET and
        # iterate the returned ``data`` array rather than the generic
        # ``self._list`` helper which adds ``page[]`` params.
        r = self.t.request("GET", "/api/v2/admin/scim-tokens")
        for item in r.json().get("data") or []:
            yield _parse_jsonapi(item, AdminSCIMToken)

    def create(self, options: AdminSCIMTokenCreateOptions) -> AdminSCIMToken:
        if not valid_string(options.description):
            raise RequiredSCIMTokenDescriptionError()
        attrs = options.model_dump(by_alias=True, exclude_none=True, mode="json")
        body = {"data": {"type": _SCIM_TOKEN_TYPE, "attributes": attrs}}
        r = self.t.request("POST", "/api/v2/admin/scim-tokens", json_body=body)
        return _parse_jsonapi(r.json()["data"], AdminSCIMToken)

    def read(self, scim_token_id: str) -> AdminSCIMToken:
        if not valid_string_id(scim_token_id):
            raise InvalidSCIMTokenIDError()
        r = self.t.request("GET", f"/api/v2/admin/scim-tokens/{scim_token_id}")
        return _parse_jsonapi(r.json()["data"], AdminSCIMToken)

    def delete(self, scim_token_id: str) -> None:
        if not valid_string_id(scim_token_id):
            raise InvalidSCIMTokenIDError()
        self.t.request("DELETE", f"/api/v2/admin/scim-tokens/{scim_token_id}")
