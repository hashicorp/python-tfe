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
        """List reserved tag keys for the given organization."""
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
        """Create a new reserved tag key for the given organization."""
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
        """Update a reserved tag key."""
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
        """Delete a reserved tag key."""
        if not valid_string_id(reserved_tag_key_id):
            raise ValidationError("Invalid reserved tag key ID")

        self.t.request("DELETE", f"/api/v2/reserved-tag-keys/{reserved_tag_key_id}")
        return None

    def _parse_reserved_tag_key(self, data: dict[str, Any]) -> ReservedTagKey:
        """Parse reserved tag key data from API response."""
        attrs = data.get("attributes", {})
        attrs["id"] = data.get("id")
        return ReservedTagKey.model_validate(attrs)
