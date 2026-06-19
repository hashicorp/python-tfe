# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from ..errors import (
    InvalidOrgError,
    InvalidSSHKeyIDError,
)
from ..models.ssh_key import (
    SSHKey,
    SSHKeyCreateOptions,
    SSHKeyListOptions,
    SSHKeyUpdateOptions,
)
from ..utils import valid_string_id
from ._base import _Service


class SSHKeys(_Service):
    """SSH Keys API for Terraform Enterprise."""

    def list(
        self, organization: str, options: SSHKeyListOptions | None = None
    ) -> Iterator[SSHKey]:
        """List SSH keys for the given organization.

        Args:
            organization: The organization name (e.g. ``"my-org"``).
            options: Optional pagination controls, as a :class:`SSHKeyListOptions`.

        Returns:
            A single-use ``Iterator[SSHKey]``. Wrap with ``list(...)`` to
            materialize the results or iterate more than once.

        Raises:
            InvalidOrgError: If ``organization`` is not a valid organization name.
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import SSHKeyListOptions
            >>> for key in client.ssh_keys.list(
            ...     "my-org", SSHKeyListOptions(page_size=20)
            ... ):
            ...     print(key.id, key.name)
        """
        if not valid_string_id(organization):
            raise InvalidOrgError()

        params = options.model_dump(by_alias=True, exclude_none=True) if options else {}
        path = f"/api/v2/organizations/{organization}/ssh-keys"
        for item in self._list(path, params=params):
            attrs = item.get("attributes", {})
            attrs["id"] = item.get("id")
            yield SSHKey.model_validate(attrs)

    def create(self, organization: str, options: SSHKeyCreateOptions) -> SSHKey:
        """Create a new SSH key for the given organization.

        Args:
            organization: The organization name (e.g. ``"my-org"``).
            options: SSH key name and private key text, as a
                :class:`SSHKeyCreateOptions`.

        Returns:
            The :class:`SSHKey`.

        Raises:
            InvalidOrgError: If ``organization`` is not a valid organization name.
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import SSHKeyCreateOptions
            >>> key = client.ssh_keys.create(
            ...     "my-org",
            ...     SSHKeyCreateOptions(name="deploy-key", value=private_key_pem),
            ... )
        """
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
        """Read an SSH key by its ID.

        Args:
            ssh_key_id: The SSH key ID (e.g. ``"sshkey-xxxxxxxx"``).

        Returns:
            The :class:`SSHKey`.

        Raises:
            InvalidSSHKeyIDError: If ``ssh_key_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> key = client.ssh_keys.read("sshkey-123")
            >>> print(key.name)
        """
        if not valid_string_id(ssh_key_id):
            raise InvalidSSHKeyIDError()

        r = self.t.request("GET", f"/api/v2/ssh-keys/{ssh_key_id}")

        jd = r.json()
        data = jd.get("data", {})

        return self._parse_ssh_key(data)

    def update(self, ssh_key_id: str, options: SSHKeyUpdateOptions) -> SSHKey:
        """Update an SSH key.

        Args:
            ssh_key_id: The SSH key ID (e.g. ``"sshkey-xxxxxxxx"``).
            options: SSH key fields to update, as a :class:`SSHKeyUpdateOptions`.

        Returns:
            The :class:`SSHKey`.

        Raises:
            InvalidSSHKeyIDError: If ``ssh_key_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import SSHKeyUpdateOptions
            >>> key = client.ssh_keys.update(
            ...     "sshkey-123", SSHKeyUpdateOptions(name="deploy-key-v2")
            ... )
        """
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
        """Delete an SSH key.

        Args:
            ssh_key_id: The SSH key ID (e.g. ``"sshkey-xxxxxxxx"``).

        Returns:
            None.

        Raises:
            InvalidSSHKeyIDError: If ``ssh_key_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> client.ssh_keys.delete("sshkey-123")
        """
        if not valid_string_id(ssh_key_id):
            raise InvalidSSHKeyIDError()

        self.t.request("DELETE", f"/api/v2/ssh-keys/{ssh_key_id}")
        # DELETE returns 204 No Content on success

    def _parse_ssh_key(self, data: dict[str, Any]) -> SSHKey:
        """Parse SSH key data from API response."""
        attrs = data.get("attributes", {})
        attrs["id"] = data.get("id")
        return SSHKey.model_validate(attrs)
