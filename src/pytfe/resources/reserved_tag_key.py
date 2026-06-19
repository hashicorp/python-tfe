# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from ..errors import (
    InvalidOrgError,
    ValidationError,
)
from ..models.reserved_tag_key import (
    ReservedTagKey,
    ReservedTagKeyCreateOptions,
    ReservedTagKeyListOptions,
    ReservedTagKeyUpdateOptions,
)
from ..utils import valid_string_id
from ._base import _Service


class ReservedTagKeys(_Service):
    """Reserved Tag Key API for Terraform Enterprise."""

    def list(
        self, organization: str, options: ReservedTagKeyListOptions | None = None
    ) -> Iterator[ReservedTagKey]:
        """List reserved tag keys in an organization.

        Args:
            organization: The organization name (e.g. ``"my-org"``).
            options: Optional pagination controls, as a
                :class:`ReservedTagKeyListOptions`.

        Returns:
            A single-use ``Iterator[ReservedTagKey]``. Wrap with ``list(...)`` to
            materialize the results or iterate more than once.

        Raises:
            InvalidOrgError: If ``organization`` is not a valid organization name.
            TFEError: If the API request fails.

        Example:
            >>> for key in client.reserved_tag_key.list("my-org"):
            ...     print(key.id, key.key)
        """
        if not valid_string_id(organization):
            raise InvalidOrgError()

        params = (
            options.model_dump(by_alias=True, exclude_none=True) if options else None
        )
        path = f"/api/v2/organizations/{organization}/reserved-tag-keys"
        for item in self._list(path, params=params):
            yield self._parse_reserved_tag_key(item)

    def create(
        self, organization: str, options: ReservedTagKeyCreateOptions
    ) -> ReservedTagKey:
        """Create a reserved tag key in an organization.

        Args:
            organization: The organization name (e.g. ``"my-org"``).
            options: Reserved tag key attributes, as a
                :class:`ReservedTagKeyCreateOptions`.

        Returns:
            The created :class:`ReservedTagKey`.

        Raises:
            InvalidOrgError: If ``organization`` is not a valid organization name.
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import ReservedTagKeyCreateOptions
            >>> key = client.reserved_tag_key.create(
            ...     "my-org",
            ...     ReservedTagKeyCreateOptions(key="environment", disable_overrides=True),
            ... )
        """
        if not valid_string_id(organization):
            raise InvalidOrgError()

        attrs = options.model_dump(by_alias=True, exclude_none=True)
        body: dict[str, Any] = {
            "data": {
                "attributes": attrs,
                "type": "reserved-tag-keys",
            }
        }

        r = self.t.request(
            "POST",
            f"/api/v2/organizations/{organization}/reserved-tag-keys",
            json_body=body,
        )

        jd = r.json()
        data = jd.get("data", {})

        return self._parse_reserved_tag_key(data)

    def update(
        self, reserved_tag_key_id: str, options: ReservedTagKeyUpdateOptions
    ) -> ReservedTagKey:
        """Update a reserved tag key by its ID.

        Args:
            reserved_tag_key_id: The reserved tag key ID (e.g. ``"rtk-xxxxxxxx"``).
            options: Reserved tag key attributes to update, as a
                :class:`ReservedTagKeyUpdateOptions`.

        Returns:
            The updated :class:`ReservedTagKey`.

        Raises:
            ValidationError: If ``reserved_tag_key_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import ReservedTagKeyUpdateOptions
            >>> key = client.reserved_tag_key.update(
            ...     "rtk-123", ReservedTagKeyUpdateOptions(disable_overrides=False)
            ... )
        """
        if not valid_string_id(reserved_tag_key_id):
            raise ValidationError("Invalid reserved tag key ID")

        attrs = options.model_dump(by_alias=True, exclude_none=True)
        body: dict[str, Any] = {
            "data": {
                "attributes": attrs,
                "type": "reserved-tag-keys",
            }
        }

        r = self.t.request(
            "PATCH",
            f"/api/v2/reserved-tag-keys/{reserved_tag_key_id}",
            json_body=body,
        )

        jd = r.json()
        data = jd.get("data", {})

        return self._parse_reserved_tag_key(data)

    def delete(self, reserved_tag_key_id: str) -> None:
        """Delete a reserved tag key by its ID.

        Args:
            reserved_tag_key_id: The reserved tag key ID (e.g. ``"rtk-xxxxxxxx"``).

        Returns:
            None.

        Raises:
            ValidationError: If ``reserved_tag_key_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> client.reserved_tag_key.delete("rtk-123")
        """
        if not valid_string_id(reserved_tag_key_id):
            raise ValidationError("Invalid reserved tag key ID")

        self.t.request("DELETE", f"/api/v2/reserved-tag-keys/{reserved_tag_key_id}")
        return None

    def _parse_reserved_tag_key(self, data: dict[str, Any]) -> ReservedTagKey:
        """Parse reserved tag key data from API response."""
        attrs = data.get("attributes", {})
        attrs["id"] = data.get("id")
        return ReservedTagKey.model_validate(attrs)
