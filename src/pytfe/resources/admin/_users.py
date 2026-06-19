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
        """List Terraform Enterprise site users.

        Args:
            options: Optional filters and pagination, as an
                :class:`AdminUserListOptions`.

        Returns:
            A single-use ``Iterator[AdminUser]``. Wrap with ``list(...)`` to
            materialize the results or iterate more than once.

        Raises:
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import AdminUserListOptions
            >>> for user in client.admin.users.list(
            ...     AdminUserListOptions(query="alice"),
            ... ):
            ...     print(user.id, user.username)
        """
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
        """Read a Terraform Enterprise site user by ID.

        Args:
            user_id: The user ID (e.g. ``"user-xxxxxxxx"``).

        Returns:
            The :class:`AdminUser`.

        Raises:
            ValueError: If ``user_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> user = client.admin.users.read("user-47qC3LmA47piVan7")
            >>> print(user.email)
        """
        if not valid_string_id(user_id):
            raise ValueError(ERR_INVALID_NAME)
        r = self.t.request("GET", f"/api/v2/admin/users/{user_id}")
        return _parse_admin_user(r.json()["data"])

    def delete(self, user_id: str) -> None:
        """Delete a Terraform Enterprise site user by ID.

        Args:
            user_id: The user ID (e.g. ``"user-xxxxxxxx"``).

        Returns:
            None.

        Raises:
            ValueError: If ``user_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> client.admin.users.delete("user-47qC3LmA47piVan7")
        """
        if not valid_string_id(user_id):
            raise ValueError(ERR_INVALID_NAME)
        self.t.request("DELETE", f"/api/v2/admin/users/{user_id}")

    def suspend(self, user_id: str) -> AdminUser:
        """Suspend a Terraform Enterprise site user by ID.

        Args:
            user_id: The user ID (e.g. ``"user-xxxxxxxx"``).

        Returns:
            The :class:`AdminUser`.

        Raises:
            ValueError: If ``user_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> user = client.admin.users.suspend("user-47qC3LmA47piVan7")
            >>> print(user.is_suspended)
        """
        if not valid_string_id(user_id):
            raise ValueError(ERR_INVALID_NAME)
        r = self.t.request("POST", f"/api/v2/admin/users/{user_id}/actions/suspend")
        return _parse_admin_user(r.json()["data"])

    def unsuspend(self, user_id: str) -> AdminUser:
        """Unsuspend a Terraform Enterprise site user by ID.

        Args:
            user_id: The user ID (e.g. ``"user-xxxxxxxx"``).

        Returns:
            The :class:`AdminUser`.

        Raises:
            ValueError: If ``user_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> user = client.admin.users.unsuspend("user-47qC3LmA47piVan7")
            >>> print(user.is_suspended)
        """
        if not valid_string_id(user_id):
            raise ValueError(ERR_INVALID_NAME)
        r = self.t.request("POST", f"/api/v2/admin/users/{user_id}/actions/unsuspend")
        return _parse_admin_user(r.json()["data"])

    def grant_admin(self, user_id: str) -> AdminUser:
        """Grant site-admin access to a user by ID.

        Args:
            user_id: The user ID (e.g. ``"user-xxxxxxxx"``).

        Returns:
            The :class:`AdminUser`.

        Raises:
            ValueError: If ``user_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> user = client.admin.users.grant_admin("user-47qC3LmA47piVan7")
            >>> print(user.is_admin)
        """
        if not valid_string_id(user_id):
            raise ValueError(ERR_INVALID_NAME)
        r = self.t.request("POST", f"/api/v2/admin/users/{user_id}/actions/grant_admin")
        return _parse_admin_user(r.json()["data"])

    def revoke_admin(self, user_id: str) -> AdminUser:
        """Revoke site-admin access from a user by ID.

        Args:
            user_id: The user ID (e.g. ``"user-xxxxxxxx"``).

        Returns:
            The :class:`AdminUser`.

        Raises:
            ValueError: If ``user_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> user = client.admin.users.revoke_admin("user-47qC3LmA47piVan7")
            >>> print(user.is_admin)
        """
        if not valid_string_id(user_id):
            raise ValueError(ERR_INVALID_NAME)
        r = self.t.request(
            "POST", f"/api/v2/admin/users/{user_id}/actions/revoke_admin"
        )
        return _parse_admin_user(r.json()["data"])

    def disable_two_factor(self, user_id: str) -> AdminUser:
        """Disable two-factor authentication for a user by ID.

        Args:
            user_id: The user ID (e.g. ``"user-xxxxxxxx"``).

        Returns:
            The :class:`AdminUser`.

        Raises:
            ValueError: If ``user_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> user = client.admin.users.disable_two_factor("user-47qC3LmA47piVan7")
            >>> print(user.two_factor_enabled)
        """
        if not valid_string_id(user_id):
            raise ValueError(ERR_INVALID_NAME)
        r = self.t.request(
            "POST", f"/api/v2/admin/users/{user_id}/actions/disable_two_factor"
        )
        return _parse_admin_user(r.json()["data"])
