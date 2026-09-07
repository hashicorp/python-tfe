# Copyright IBM Corp. 2025, 2026

from __future__ import annotations

from ..models.user import User, UserUpdateCurrentOptions
from ..utils import valid_string_id
from ._base import _Service


class Users(_Service):
    def read(self, user_id: str) -> User:
        """Read a user by ID.

        Args:
            user_id: The user ID (e.g. ``"user-xxxxxxxx"``).

        Returns:
            The :class:`User`.

        Raises:
            ValueError: If ``user_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> user = client.users.read("user-47qC3LmA47piVan7")
            >>> print(user.username)
        """
        if not valid_string_id(user_id):
            raise ValueError("invalid user id")

        r = self.t.request("GET", f"/api/v2/users/{user_id}")
        d = r.json()["data"]
        attr = d.get("attributes", {}) or {}
        user_data = dict(attr)
        user_data["id"] = d.get("id")
        return User(**user_data)

    def read_current(self) -> User:
        """Read the currently authenticated user.

        Returns:
            The :class:`User`.

        Raises:
            TFEError: If the API request fails.

        Example:
            >>> user = client.users.read_current()
            >>> print(user.email)
        """
        r = self.t.request("GET", "/api/v2/account/details")
        d = r.json()["data"]
        attr = d.get("attributes", {}) or {}
        user_data = dict(attr)
        user_data["id"] = d.get("id")
        return User(**user_data)

    def update_current(self, options: UserUpdateCurrentOptions) -> User:
        """Update the currently authenticated user.

        Args:
            options: The user account updates, as a
                :class:`UserUpdateCurrentOptions`.

        Returns:
            The :class:`User`.

        Raises:
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import UserUpdateCurrentOptions
            >>> user = client.users.update_current(
            ...     UserUpdateCurrentOptions(username="alice")
            ... )
        """
        body = {
            "data": {
                "type": "users",
                "attributes": options.model_dump(exclude_none=True),
            }
        }
        r = self.t.request("PATCH", "/api/v2/account/update", json_body=body)
        d = r.json()["data"]
        attr = d.get("attributes", {}) or {}
        user_data = dict(attr)
        user_data["id"] = d.get("id")
        return User(**user_data)
