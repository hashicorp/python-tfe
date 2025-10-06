from __future__ import annotations

from typing import Any

from ..errors import (
    InvalidOrgError,
    InvalidSSHKeyIDError,
)
from ..models.ssh_key import (
    SSHKey,
    SSHKeyCreateOptions,
    SSHKeyList,
    SSHKeyListOptions,
    SSHKeyUpdateOptions,
)
from ..utils import valid_string_id
from ._base import _Service


class SSHKeys(_Service):
    """SSH Keys API for Terraform Enterprise."""

    def list(
        self, organization: str, options: SSHKeyListOptions | None = None
    ) -> SSHKeyList:
        """List SSH keys for the given organization."""
        if not valid_string_id(organization):
            raise InvalidOrgError()

        params = (
            options.model_dump(by_alias=True, exclude_none=True) if options else None
        )

        r = self.t.request(
            "GET",
            f"/api/v2/organizations/{organization}/ssh-keys",
            params=params,
        )

        jd = r.json()
        items = []
        meta = jd.get("meta", {})
        pagination = meta.get("pagination", {})

        for d in jd.get("data", []):
            items.append(self._parse_ssh_key(d))

        return SSHKeyList(
            items=items,
            current_page=pagination.get("current-page"),
            total_pages=pagination.get("total-pages"),
            prev_page=pagination.get("prev-page"),
            next_page=pagination.get("next-page"),
            total_count=pagination.get("total-count"),
        )

    def create(self, organization: str, options: SSHKeyCreateOptions) -> SSHKey:
        """Create a new SSH key for the given organization."""
        if not valid_string_id(organization):
            raise InvalidOrgError()

        attrs = options.model_dump(by_alias=True, exclude_none=True)
        body: dict[str, Any] = {
            "data": {
                "attributes": attrs,
                "type": "ssh-keys",
            }
        }

        r = self.t.request(
            "POST",
            f"/api/v2/organizations/{organization}/ssh-keys",
            json_body=body,
        )

        jd = r.json()
        data = jd.get("data", {})

        return self._parse_ssh_key(data)

    def read(self, ssh_key_id: str) -> SSHKey:
        """Read an SSH key by its ID."""
        if not valid_string_id(ssh_key_id):
            raise InvalidSSHKeyIDError()

        r = self.t.request("GET", f"/api/v2/ssh-keys/{ssh_key_id}")

        jd = r.json()
        data = jd.get("data", {})

        return self._parse_ssh_key(data)

    def update(self, ssh_key_id: str, options: SSHKeyUpdateOptions) -> SSHKey:
        """Update an SSH key."""
        if not valid_string_id(ssh_key_id):
            raise InvalidSSHKeyIDError()

        attrs = options.model_dump(by_alias=True, exclude_none=True)
        body: dict[str, Any] = {
            "data": {
                "attributes": attrs,
                "type": "ssh-keys",
            }
        }

        r = self.t.request(
            "PATCH",
            f"/api/v2/ssh-keys/{ssh_key_id}",
            json_body=body,
        )

        jd = r.json()
        data = jd.get("data", {})

        return self._parse_ssh_key(data)

    def delete(self, ssh_key_id: str) -> None:
        """Delete an SSH key."""
        if not valid_string_id(ssh_key_id):
            raise InvalidSSHKeyIDError()

        self.t.request("DELETE", f"/api/v2/ssh-keys/{ssh_key_id}")
        # DELETE returns 204 No Content on success

    def _parse_ssh_key(self, data: dict[str, Any]) -> SSHKey:
        """Parse SSH key data from API response."""
        attrs = data.get("attributes", {})
        attrs["id"] = data.get("id")
        return SSHKey.model_validate(attrs)
