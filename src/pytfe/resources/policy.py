# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from .._jsonapi import attach_jsonapi
from ..errors import (
    InvalidNameError,
    InvalidOrgError,
    InvalidPolicyIDError,
    RequiredEnforceError,
    RequiredNameError,
    RequiredQueryError,
)
from ..models.policy import (
    Policy,
    PolicyCreateOptions,
    PolicyListOptions,
    PolicyUpdateOptions,
)
from ..utils import valid_string, valid_string_id
from ._base import _Service


class Policies(_Service):
    def list(
        self, organization: str, options: PolicyListOptions | None = None
    ) -> Iterator[Policy]:
        """List all policies in the given organization.

        Args:
            organization: The organization name (e.g. ``"my-org"``).
            options: Pagination and filter options, as a :class:`PolicyListOptions`.

        Returns:
            A single-use ``Iterator[Policy]``. Wrap with ``list(...)`` to materialize
            the results or iterate more than once.

        Raises:
            InvalidOrgError: If ``organization`` is not a valid organization name.
            TFEError: If the API request fails.

        Example:
            >>> for policy in client.policies.list("my-org"):
            ...     print(policy.id, policy.name)
        """
        if not valid_string_id(organization):
            raise InvalidOrgError()

        path = f"/api/v2/organizations/{organization}/policies"
        params: dict[str, Any] = {}

        if options:
            if getattr(options, "page_size", None):
                params["page[size]"] = str(options.page_size)

        def _gen() -> Iterator[Policy]:
            for item in self._list(path, params=params):
                attrs = item.get("attributes", {})
                attrs["id"] = item.get("id")
                attrs["organization"] = item.get("relationships", {}).get(
                    "organization", {}
                )
                yield attach_jsonapi(Policy.model_validate(attrs), item)

        return _gen()

    def create(self, organization: str, options: PolicyCreateOptions) -> Policy:
        """Create a new policy in the given organization.

        Args:
            organization: The organization name (e.g. ``"my-org"``).
            options: Policy creation settings, as a :class:`PolicyCreateOptions`.

        Returns:
            The :class:`Policy`.

        Raises:
            InvalidOrgError: If ``organization`` is not a valid organization name.
            RequiredNameError: If ``options.name`` is missing or blank.
            InvalidNameError: If ``options.name`` is not a valid policy name.
            RequiredQueryError: If an OPA policy is missing ``options.query``.
            RequiredEnforceError: If ``options.enforcement_level`` is missing.
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import (
            ...     EnforcementLevel,
            ...     PolicyCreateOptions,
            ...     PolicyKind,
            ... )
            >>> policy = client.policies.create(
            ...     "my-org",
            ...     PolicyCreateOptions(
            ...         name="cost-policy",
            ...         kind=PolicyKind.SENTINEL,
            ...         enforcement_level=EnforcementLevel.ENFORCEMENT_HARD,
            ...     ),
            ... )
        """
        if not valid_string_id(organization):
            raise InvalidOrgError()
        valid = self._valid_create_options(options)
        if valid is not None:
            raise valid
        payload = {
            "data": {
                "attributes": options.model_dump(by_alias=True, exclude_none=True),
                "type": "policies",
            }
        }
        r = self.t.request(
            "POST",
            f"/api/v2/organizations/{organization}/policies",
            json_body=payload,
        )
        jd = r.json()
        d = jd.get("data", {})
        attrs = d.get("attributes", {})
        attrs["id"] = d.get("id")
        return attach_jsonapi(Policy.model_validate(attrs), d)

    def read(self, policy_id: str) -> Policy:
        """Read a specific policy by its ID.

        Args:
            policy_id: The policy ID (e.g. ``"pol-xxxxxxxx"``).

        Returns:
            The :class:`Policy`.

        Raises:
            InvalidPolicyIDError: If ``policy_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> policy = client.policies.read("pol-789")
            >>> print(policy.name)
        """
        if not valid_string_id(policy_id):
            raise InvalidPolicyIDError
        r = self.t.request(
            "GET",
            f"/api/v2/policies/{policy_id}",
        )
        jd = r.json()
        d = jd.get("data", {})
        attrs = d.get("attributes", {})
        attrs["id"] = d.get("id")
        attrs["organization"] = d.get("relationships", {}).get("organization", {})
        return attach_jsonapi(Policy.model_validate(attrs), d)

    def update(self, policy_id: str, options: PolicyUpdateOptions) -> Policy:
        """Update an existing policy by its ID.

        Args:
            policy_id: The policy ID (e.g. ``"pol-xxxxxxxx"``).
            options: Policy update settings, as a :class:`PolicyUpdateOptions`.

        Returns:
            The :class:`Policy`.

        Raises:
            InvalidPolicyIDError: If ``policy_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import EnforcementLevel, PolicyUpdateOptions
            >>> policy = client.policies.update(
            ...     "pol-789",
            ...     PolicyUpdateOptions(
            ...         enforcement_level=EnforcementLevel.ENFORCEMENT_SOFT
            ...     ),
            ... )
        """
        if not valid_string_id(policy_id):
            raise InvalidPolicyIDError
        payload = {
            "data": {
                "type": "policies",
                "attributes": options.model_dump(by_alias=True, exclude_none=True),
            }
        }
        r = self.t.request(
            "PATCH",
            f"/api/v2/policies/{policy_id}",
            json_body=payload,
        )
        jd = r.json()
        d = jd.get("data", {})
        attrs = d.get("attributes", {})
        attrs["id"] = d.get("id")
        attrs["organization"] = d.get("relationships", {}).get("organization", {})
        return attach_jsonapi(Policy.model_validate(attrs), d)

    def delete(self, policy_id: str) -> None:
        """Delete a specific policy by its ID.

        Args:
            policy_id: The policy ID (e.g. ``"pol-xxxxxxxx"``).

        Returns:
            None.

        Raises:
            InvalidPolicyIDError: If ``policy_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> client.policies.delete("pol-789")
        """
        if not valid_string_id(policy_id):
            raise InvalidPolicyIDError
        self.t.request(
            "DELETE",
            f"/api/v2/policies/{policy_id}",
        )
        return None

    def upload(self, policy_id: str, content: bytes) -> None:
        """Upload policy content for a policy.

        Args:
            policy_id: The policy ID (e.g. ``"pol-xxxxxxxx"``).
            content: The raw policy file bytes to upload.

        Returns:
            None.

        Raises:
            InvalidPolicyIDError: If ``policy_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> client.policies.upload("pol-789", b"main = rule { true }")
        """
        if not valid_string_id(policy_id):
            raise InvalidPolicyIDError

        # Send binary content directly (not as JSON)
        self.t.request(
            "PUT",
            f"/api/v2/policies/{policy_id}/upload",
            data=content,
            headers={"Content-Type": "application/octet-stream"},
        )
        return None

    def download(self, policy_id: str) -> bytes:
        """Download policy content for a policy.

        Args:
            policy_id: The policy ID (e.g. ``"pol-xxxxxxxx"``).

        Returns:
            The raw bytes (the SDK follows the storage/redirect URL for you).

        Raises:
            InvalidPolicyIDError: If ``policy_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> content = client.policies.download("pol-789")
            >>> print(content.decode())
        """
        if not valid_string_id(policy_id):
            raise InvalidPolicyIDError
        r = self.t.request(
            "GET",
            f"/api/v2/policies/{policy_id}/download",
        )
        return r.content

    def _valid_create_options(self, options: PolicyCreateOptions) -> None | Exception:
        """Validate the given PolicyCreateOptions."""
        if not valid_string(options.name):
            return RequiredNameError()
        if not valid_string_id(options.name):
            return InvalidNameError()

        if options.kind == "opa" and not valid_string(options.query):
            return RequiredQueryError()

        if not options.enforcement_level:
            return RequiredEnforceError()

        return None
