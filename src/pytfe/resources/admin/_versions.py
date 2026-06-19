# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from ...errors import ERR_INVALID_VERSION
from ...models.admin_version import (
    OpaVersion,
    OpaVersionCreateOptions,
    OpaVersionUpdateOptions,
    SentinelVersion,
    SentinelVersionCreateOptions,
    SentinelVersionUpdateOptions,
    TerraformVersion,
    TerraformVersionCreateOptions,
    TerraformVersionUpdateOptions,
)
from ...utils import valid_string_id
from .._base import _Service

_TF_VERSION_TYPE = "terraform-versions"
_OPA_VERSION_TYPE = "opa-versions"
_SENTINEL_VERSION_TYPE = "sentinel-versions"


def _parse_terraform_version(data: dict[str, Any]) -> TerraformVersion:
    attrs = data.get("attributes") or {}
    return TerraformVersion.model_validate({"id": data.get("id"), **attrs})


def _parse_opa_version(data: dict[str, Any]) -> OpaVersion:
    attrs = data.get("attributes") or {}
    return OpaVersion.model_validate({"id": data.get("id"), **attrs})


def _parse_sentinel_version(data: dict[str, Any]) -> SentinelVersion:
    attrs = data.get("attributes") or {}
    return SentinelVersion.model_validate({"id": data.get("id"), **attrs})


class _AdminTerraformVersions(_Service):
    def list(self) -> Iterator[TerraformVersion]:
        """List all admin-managed Terraform versions.

        Returns:
            A single-use ``Iterator[TerraformVersion]``. Wrap with ``list(...)`` to
            materialize the results or iterate more than once.

        Raises:
            TFEError: If the API request fails.

        Example:
            >>> for version in client.admin.terraform_versions.list():
            ...     print(version.id, version.version)
        """
        for item in self._list("/api/v2/admin/terraform-versions"):
            yield _parse_terraform_version(item)

    def read(self, version_id: str) -> TerraformVersion:
        """Read an admin-managed Terraform version by its ID.

        Args:
            version_id: The version ID (e.g. ``"tv-1"``).

        Returns:
            The :class:`TerraformVersion`.

        Raises:
            ValueError: If ``version_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> version = client.admin.terraform_versions.read("tv-1")
            >>> print(version.version)
        """
        if not valid_string_id(version_id):
            raise ValueError(ERR_INVALID_VERSION)
        r = self.t.request("GET", f"/api/v2/admin/terraform-versions/{version_id}")
        return _parse_terraform_version(r.json()["data"])

    def create(self, options: TerraformVersionCreateOptions) -> TerraformVersion:
        """Create an admin-managed Terraform version.

        Args:
            options: The version package metadata, as a
                :class:`TerraformVersionCreateOptions`.

        Returns:
            The created :class:`TerraformVersion`.

        Raises:
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import TerraformVersionCreateOptions
            >>> options = TerraformVersionCreateOptions(
            ...     version="1.9.0", url="https://example.com/tf.zip", sha="abc123"
            ... )
            >>> version = client.admin.terraform_versions.create(
            ...     options
            ... )
        """
        attrs = options.model_dump(by_alias=True, exclude_none=True, mode="json")
        body = {"data": {"type": _TF_VERSION_TYPE, "attributes": attrs}}
        r = self.t.request("POST", "/api/v2/admin/terraform-versions", json_body=body)
        return _parse_terraform_version(r.json()["data"])

    def update(
        self, version_id: str, options: TerraformVersionUpdateOptions
    ) -> TerraformVersion:
        """Update an admin-managed Terraform version.

        Args:
            version_id: The version ID (e.g. ``"tv-1"``).
            options: The version fields to change, as a
                :class:`TerraformVersionUpdateOptions`.

        Returns:
            The updated :class:`TerraformVersion`.

        Raises:
            ValueError: If ``version_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import TerraformVersionUpdateOptions
            >>> version = client.admin.terraform_versions.update(
            ...     "tv-1", TerraformVersionUpdateOptions(enabled=True)
            ... )
        """
        if not valid_string_id(version_id):
            raise ValueError(ERR_INVALID_VERSION)
        attrs = options.model_dump(by_alias=True, exclude_none=True, mode="json")
        body = {"data": {"type": _TF_VERSION_TYPE, "attributes": attrs}}
        r = self.t.request(
            "PATCH", f"/api/v2/admin/terraform-versions/{version_id}", json_body=body
        )
        return _parse_terraform_version(r.json()["data"])

    def delete(self, version_id: str) -> None:
        """Delete an admin-managed Terraform version.

        Args:
            version_id: The version ID (e.g. ``"tv-1"``).

        Returns:
            None.

        Raises:
            ValueError: If ``version_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> client.admin.terraform_versions.delete("tv-1")
        """
        if not valid_string_id(version_id):
            raise ValueError(ERR_INVALID_VERSION)
        self.t.request("DELETE", f"/api/v2/admin/terraform-versions/{version_id}")


class _AdminOpaVersions(_Service):
    def list(self) -> Iterator[OpaVersion]:
        """List all admin-managed OPA versions.

        Returns:
            A single-use ``Iterator[OpaVersion]``. Wrap with ``list(...)`` to
            materialize the results or iterate more than once.

        Raises:
            TFEError: If the API request fails.

        Example:
            >>> for version in client.admin.opa_versions.list():
            ...     print(version.id, version.version)
        """
        for item in self._list("/api/v2/admin/opa-versions"):
            yield _parse_opa_version(item)

    def read(self, version_id: str) -> OpaVersion:
        """Read an admin-managed OPA version by its ID.

        Args:
            version_id: The version ID (e.g. ``"ov-1"``).

        Returns:
            The :class:`OpaVersion`.

        Raises:
            ValueError: If ``version_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> version = client.admin.opa_versions.read("ov-1")
            >>> print(version.version)
        """
        if not valid_string_id(version_id):
            raise ValueError(ERR_INVALID_VERSION)
        r = self.t.request("GET", f"/api/v2/admin/opa-versions/{version_id}")
        return _parse_opa_version(r.json()["data"])

    def create(self, options: OpaVersionCreateOptions) -> OpaVersion:
        """Create an admin-managed OPA version.

        Args:
            options: The version package metadata, as a
                :class:`OpaVersionCreateOptions`.

        Returns:
            The created :class:`OpaVersion`.

        Raises:
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import OpaVersionCreateOptions
            >>> options = OpaVersionCreateOptions(
            ...     version="0.60.0", url="https://example.com/opa.zip", sha="abc123"
            ... )
            >>> version = client.admin.opa_versions.create(
            ...     options
            ... )
        """
        attrs = options.model_dump(by_alias=True, exclude_none=True, mode="json")
        body = {"data": {"type": _OPA_VERSION_TYPE, "attributes": attrs}}
        r = self.t.request("POST", "/api/v2/admin/opa-versions", json_body=body)
        return _parse_opa_version(r.json()["data"])

    def update(self, version_id: str, options: OpaVersionUpdateOptions) -> OpaVersion:
        """Update an admin-managed OPA version.

        Args:
            version_id: The version ID (e.g. ``"ov-1"``).
            options: The version fields to change, as a
                :class:`OpaVersionUpdateOptions`.

        Returns:
            The updated :class:`OpaVersion`.

        Raises:
            ValueError: If ``version_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import OpaVersionUpdateOptions
            >>> version = client.admin.opa_versions.update(
            ...     "ov-1", OpaVersionUpdateOptions(enabled=True)
            ... )
        """
        if not valid_string_id(version_id):
            raise ValueError(ERR_INVALID_VERSION)
        attrs = options.model_dump(by_alias=True, exclude_none=True, mode="json")
        body = {"data": {"type": _OPA_VERSION_TYPE, "attributes": attrs}}
        r = self.t.request(
            "PATCH", f"/api/v2/admin/opa-versions/{version_id}", json_body=body
        )
        return _parse_opa_version(r.json()["data"])

    def delete(self, version_id: str) -> None:
        """Delete an admin-managed OPA version.

        Args:
            version_id: The version ID (e.g. ``"ov-1"``).

        Returns:
            None.

        Raises:
            ValueError: If ``version_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> client.admin.opa_versions.delete("ov-1")
        """
        if not valid_string_id(version_id):
            raise ValueError(ERR_INVALID_VERSION)
        self.t.request("DELETE", f"/api/v2/admin/opa-versions/{version_id}")


class _AdminSentinelVersions(_Service):
    def list(self) -> Iterator[SentinelVersion]:
        """List all admin-managed Sentinel versions.

        Returns:
            A single-use ``Iterator[SentinelVersion]``. Wrap with ``list(...)`` to
            materialize the results or iterate more than once.

        Raises:
            TFEError: If the API request fails.

        Example:
            >>> for version in client.admin.sentinel_versions.list():
            ...     print(version.id, version.version)
        """
        for item in self._list("/api/v2/admin/sentinel-versions"):
            yield _parse_sentinel_version(item)

    def read(self, version_id: str) -> SentinelVersion:
        """Read an admin-managed Sentinel version by its ID.

        Args:
            version_id: The version ID (e.g. ``"sv-1"``).

        Returns:
            The :class:`SentinelVersion`.

        Raises:
            ValueError: If ``version_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> version = client.admin.sentinel_versions.read("sv-1")
            >>> print(version.version)
        """
        if not valid_string_id(version_id):
            raise ValueError(ERR_INVALID_VERSION)
        r = self.t.request("GET", f"/api/v2/admin/sentinel-versions/{version_id}")
        return _parse_sentinel_version(r.json()["data"])

    def create(self, options: SentinelVersionCreateOptions) -> SentinelVersion:
        """Create an admin-managed Sentinel version.

        Args:
            options: The version package metadata, as a
                :class:`SentinelVersionCreateOptions`.

        Returns:
            The created :class:`SentinelVersion`.

        Raises:
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import SentinelVersionCreateOptions
            >>> options = SentinelVersionCreateOptions(
            ...     version="0.26.0", url="https://example.com/s.zip", sha="abc123"
            ... )
            >>> version = client.admin.sentinel_versions.create(
            ...     options
            ... )
        """
        attrs = options.model_dump(by_alias=True, exclude_none=True, mode="json")
        body = {"data": {"type": _SENTINEL_VERSION_TYPE, "attributes": attrs}}
        r = self.t.request("POST", "/api/v2/admin/sentinel-versions", json_body=body)
        return _parse_sentinel_version(r.json()["data"])

    def update(
        self, version_id: str, options: SentinelVersionUpdateOptions
    ) -> SentinelVersion:
        """Update an admin-managed Sentinel version.

        Args:
            version_id: The version ID (e.g. ``"sv-1"``).
            options: The version fields to change, as a
                :class:`SentinelVersionUpdateOptions`.

        Returns:
            The updated :class:`SentinelVersion`.

        Raises:
            ValueError: If ``version_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import SentinelVersionUpdateOptions
            >>> version = client.admin.sentinel_versions.update(
            ...     "sv-1", SentinelVersionUpdateOptions(enabled=True)
            ... )
        """
        if not valid_string_id(version_id):
            raise ValueError(ERR_INVALID_VERSION)
        attrs = options.model_dump(by_alias=True, exclude_none=True, mode="json")
        body = {"data": {"type": _SENTINEL_VERSION_TYPE, "attributes": attrs}}
        r = self.t.request(
            "PATCH", f"/api/v2/admin/sentinel-versions/{version_id}", json_body=body
        )
        return _parse_sentinel_version(r.json()["data"])

    def delete(self, version_id: str) -> None:
        """Delete an admin-managed Sentinel version.

        Args:
            version_id: The version ID (e.g. ``"sv-1"``).

        Returns:
            None.

        Raises:
            ValueError: If ``version_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> client.admin.sentinel_versions.delete("sv-1")
        """
        if not valid_string_id(version_id):
            raise ValueError(ERR_INVALID_VERSION)
        self.t.request("DELETE", f"/api/v2/admin/sentinel-versions/{version_id}")
