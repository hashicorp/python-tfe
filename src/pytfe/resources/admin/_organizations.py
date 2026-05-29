# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from ...errors import ERR_INVALID_NAME
from ...models.admin_organization import (
    AdminOrganization,
    AdminOrganizationListOptions,
    AdminOrganizationUpdateOptions,
)
from ...utils import valid_string_id
from .._base import _Service

_ADMIN_ORG_TYPE = "organizations"


def _parse_admin_organization(data: dict[str, Any]) -> AdminOrganization:
    attrs = data.get("attributes") or {}
    return AdminOrganization.model_validate({"id": data.get("id"), **attrs})


class _AdminOrganizations(_Service):
    def list(self, options: AdminOrganizationListOptions | None = None) -> Iterator[AdminOrganization]:
        params: dict[str, Any] = {}
        if options:
            if options.query:
                params["q"] = options.query
            if options.page_number is not None:
                params["page[number]"] = options.page_number
            if options.page_size is not None:
                params["page[size]"] = options.page_size
        for item in self._list("/api/v2/admin/organizations", params=params):
            yield _parse_admin_organization(item)

    def read(self, name: str) -> AdminOrganization:
        if not valid_string_id(name):
            raise ValueError(ERR_INVALID_NAME)
        r = self.t.request("GET", f"/api/v2/admin/organizations/{name}")
        return _parse_admin_organization(r.json()["data"])

    def update(self, name: str, options: AdminOrganizationUpdateOptions) -> AdminOrganization:
        if not valid_string_id(name):
            raise ValueError(ERR_INVALID_NAME)
        attrs = options.model_dump(by_alias=True, exclude_none=True, mode="json")
        body = {"data": {"type": _ADMIN_ORG_TYPE, "attributes": attrs}}
        r = self.t.request(
            "PATCH", f"/api/v2/admin/organizations/{name}", json_body=body
        )
        return _parse_admin_organization(r.json()["data"])

    def delete(self, name: str) -> None:
        if not valid_string_id(name):
            raise ValueError(ERR_INVALID_NAME)
        self.t.request("DELETE", f"/api/v2/admin/organizations/{name}")
