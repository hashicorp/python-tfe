# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from ..._jsonapi import attach_jsonapi
from ...errors import ERR_INVALID_NAME
from ...models.admin_user import AdminUser, AdminUserListOptions
from ...utils import valid_string_id
from .._base import _Service


def _parse_admin_user(data: dict[str, Any]) -> AdminUser:
    attrs = data.get("attributes") or {}
    return attach_jsonapi(
        AdminUser.model_validate({"id": data.get("id"), **attrs}), data
    )


class _AdminUsers(_Service):
    def list(self, options: AdminUserListOptions | None = None) -> Iterator[AdminUser]:
        params: dict[str, Any] = {}
        if options:
            if options.query:
                params["q"] = options.query
            if options.administrators is not None:
                params["filter[admin]"] = str(options.administrators).lower()
            if options.suspended is not None:
                params["filter[suspended]"] = str(options.suspended).lower()
            if options.page_number is not None:
                params["page[number]"] = options.page_number
            if options.page_size is not None:
                params["page[size]"] = options.page_size
        for item in self._list("/api/v2/admin/users", params=params):
            yield _parse_admin_user(item)

    def read(self, user_id: str) -> AdminUser:
        if not valid_string_id(user_id):
            raise ValueError(ERR_INVALID_NAME)
        r = self.t.request("GET", f"/api/v2/admin/users/{user_id}")
        return _parse_admin_user(r.json()["data"])

    def delete(self, user_id: str) -> None:
        if not valid_string_id(user_id):
            raise ValueError(ERR_INVALID_NAME)
        self.t.request("DELETE", f"/api/v2/admin/users/{user_id}")

    def suspend(self, user_id: str) -> AdminUser:
        if not valid_string_id(user_id):
            raise ValueError(ERR_INVALID_NAME)
        r = self.t.request("POST", f"/api/v2/admin/users/{user_id}/actions/suspend")
        return _parse_admin_user(r.json()["data"])

    def unsuspend(self, user_id: str) -> AdminUser:
        if not valid_string_id(user_id):
            raise ValueError(ERR_INVALID_NAME)
        r = self.t.request("POST", f"/api/v2/admin/users/{user_id}/actions/unsuspend")
        return _parse_admin_user(r.json()["data"])

    def grant_admin(self, user_id: str) -> AdminUser:
        if not valid_string_id(user_id):
            raise ValueError(ERR_INVALID_NAME)
        r = self.t.request("POST", f"/api/v2/admin/users/{user_id}/actions/grant_admin")
        return _parse_admin_user(r.json()["data"])

    def revoke_admin(self, user_id: str) -> AdminUser:
        if not valid_string_id(user_id):
            raise ValueError(ERR_INVALID_NAME)
        r = self.t.request(
            "POST", f"/api/v2/admin/users/{user_id}/actions/revoke_admin"
        )
        return _parse_admin_user(r.json()["data"])

    def disable_two_factor(self, user_id: str) -> AdminUser:
        if not valid_string_id(user_id):
            raise ValueError(ERR_INVALID_NAME)
        r = self.t.request(
            "POST", f"/api/v2/admin/users/{user_id}/actions/disable_two_factor"
        )
        return _parse_admin_user(r.json()["data"])
