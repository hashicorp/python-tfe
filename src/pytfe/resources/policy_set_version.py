# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from .._jsonapi import attach_jsonapi
from ..errors import (
    InvalidPolicySetIDError,
)
from ..models.policy_set_version import (
    PolicySetVersion,
)
from ..utils import pack_contents, valid_string_id
from ._base import _Service


class PolicySetVersions(_Service):
    """
    PolicySetVersions describes all the Policy Set Version related methods that the Terraform Enterprise API supports.
    TFE API docs: https://developer.hashicorp.com/terraform/cloud-docs/api-docs/policy-sets#create-a-policy-set-version
    """

    def create(self, policy_set_id: str) -> PolicySetVersion:
        """Create a new policy set version.

        Args:
            policy_set_id: The policy set ID (e.g. ``"polset-xxxxxxxx"``).

        Returns:
            The :class:`PolicySetVersion`.

        Raises:
            InvalidPolicySetIDError: If ``policy_set_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> version = client.policy_set_versions.create("polset-123")
            >>> print(version.id)
        """
        if not valid_string_id(policy_set_id):
            raise InvalidPolicySetIDError()
        r = self.t.request(
            "POST",
            f"/api/v2/policy-sets/{policy_set_id}/versions",
        )
        jd = r.json()
        attrs = jd.get("data", {}).get("attributes", {})
        attrs["id"] = jd.get("data", {}).get("id")
        attrs["links"] = jd.get("data", {}).get("links", {})
        attrs["policy-set"] = (
            jd.get("data", {})
            .get("relationships", {})
            .get("policy-set", {})
            .get("data", {})
        )
        return attach_jsonapi(
            PolicySetVersion.model_validate(attrs), jd.get("data", {})
        )

    def read(self, policy_set_version_id: str) -> PolicySetVersion:
        """Read a policy set version by its ID.

        Args:
            policy_set_version_id: The policy set version ID
                (e.g. ``"polsetver-xxxxxxxx"``).

        Returns:
            The :class:`PolicySetVersion`.

        Raises:
            InvalidPolicySetIDError: If ``policy_set_version_id`` is not a valid
                resource ID.
            TFEError: If the API request fails.

        Example:
            >>> version = client.policy_set_versions.read("polsetver-1")
            >>> print(version.status)
        """
        if not valid_string_id(policy_set_version_id):
            raise InvalidPolicySetIDError()
        r = self.t.request(
            "GET",
            f"/api/v2/policy-set-versions/{policy_set_version_id}",
        )
        jd = r.json()
        attrs = jd.get("data", {}).get("attributes", {})
        attrs["id"] = jd.get("data", {}).get("id")
        attrs["links"] = jd.get("data", {}).get("links", {})
        attrs["policy-set"] = (
            jd.get("data", {})
            .get("relationships", {})
            .get("policy-set", {})
            .get("data", {})
        )
        return attach_jsonapi(
            PolicySetVersion.model_validate(attrs), jd.get("data", {})
        )

    def upload(self, policy_set_version: PolicySetVersion, file_path: str) -> None:
        """Upload policy files for a policy set version.

        The SDK packages ``file_path`` with ``hashicorp/go-slug`` compatible
        packing before uploading the archive to the version's upload link.

        Args:
            policy_set_version: The policy set version returned by
                :meth:`create`, as a :class:`PolicySetVersion`.
            file_path: The local directory path containing policy files
                (e.g. ``"./policies"``).

        Returns:
            None.

        Raises:
            ValueError: If ``policy_set_version`` has no upload link or the link is
                empty.
            TFEError: If the API request fails.

        Example:
            >>> version = client.policy_set_versions.create("polset-123")
            >>> client.policy_set_versions.upload(version, "./policies")
        """
        # Extract upload URL from policy set version links
        if not policy_set_version.links or "upload" not in policy_set_version.links:
            raise ValueError("the Policy Set Version does not contain an upload link")

        upload_url = policy_set_version.links["upload"]
        if not upload_url:
            raise ValueError("the Policy Set Version upload URL is empty")

        # Pack the policy files directory into a tar.gz archive
        body = pack_contents(file_path)

        self.t.request(
            "PUT",
            upload_url,
            data=body.getvalue(),
            headers={"Content-Type": "application/octet-stream"},
        )
        return None
