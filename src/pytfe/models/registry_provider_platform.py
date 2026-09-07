# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ..errors import (
    InvalidArchError,
    InvalidOSError,
    RequiredArchError,
    RequiredFilenameError,
    RequiredOSError,
    RequiredShasumError,
)
from ..utils import valid_string, valid_string_id
from ._base import TFEModel
from .registry_provider_version import (
    RegistryProviderVersion,
    RegistryProviderVersionID,
)


class RegistryProviderPlatformPermissions(BaseModel):
    """Registry provider platform permissions."""

    model_config = ConfigDict(
        populate_by_name=True, validate_by_name=True, extra="allow"
    )

    can_delete: bool = Field(alias="can-delete")
    can_upload_asset: bool = Field(alias="can-upload-asset")


class RegistryProviderPlatform(TFEModel):
    """Registry provider platform model."""

    model_config = ConfigDict(
        populate_by_name=True, validate_by_name=True, extra="allow"
    )

    id: str
    os: str = Field(alias="os", default="")
    arch: str = Field(alias="arch", default="")
    filename: str = Field(alias="filename", default="")
    shasum: str = Field(alias="shasum", default="")
    provider_binary_uploaded: bool | None = Field(
        alias="provider-binary-uploaded", default=None
    )
    permissions: RegistryProviderPlatformPermissions | None = None

    # Relations
    registry_provider_version: RegistryProviderVersion | None = Field(
        alias="registry-provider-version", default=None
    )

    # Links
    links: dict[str, Any] | None = None

    def provider_binary_upload_url(self) -> str:
        """Return the URL to upload this platform's provider binary.

        Returns:
            The presigned upload URL from the ``provider-binary-upload`` link.

        Raises:
            ValueError: If the platform carries no upload link, which happens
                once the binary has already been uploaded.

        Example:
            >>> platform = client.registry_provider_platforms.create(version_id, opts)
            >>> platform.provider_binary_upload_url()
            'https://archivist.terraform.io/v1/object/...'
        """
        if self.links is None:
            raise ValueError(
                "The registry provider platform does not contain a provider "
                "binary upload link"
            )
        upload_url = str(self.links.get("provider-binary-upload") or "")
        if not upload_url:
            raise ValueError(
                "The registry provider platform does not contain a provider "
                "binary upload link"
            )
        return upload_url

    def provider_binary_download_url(self) -> str:
        """Return the URL to download this platform's provider binary.

        Returns:
            The download URL from the ``provider-binary-download`` link.

        Raises:
            ValueError: If the platform carries no download link, which is the
                case until the binary has been uploaded.

        Example:
            >>> platform = client.registry_provider_platforms.read(platform_id)
            >>> platform.provider_binary_download_url()
            'https://archivist.terraform.io/v1/object/...'
        """
        if self.links is None:
            raise ValueError(
                "The registry provider platform does not contain a provider "
                "binary download link"
            )
        download_url = str(self.links.get("provider-binary-download") or "")
        if not download_url:
            raise ValueError(
                "The registry provider platform does not contain a provider "
                "binary download link"
            )
        return download_url


class RegistryProviderPlatformID(RegistryProviderVersionID):
    """Registry provider platform identifier.

    Extends RegistryProviderVersionID with OS and arch to uniquely
    identify a specific platform of a provider version.
    """

    os: str
    arch: str

    @model_validator(mode="after")
    def valid_platform_id(self) -> RegistryProviderPlatformID:
        if not valid_string_id(self.os):
            raise InvalidOSError()
        if not valid_string_id(self.arch):
            raise InvalidArchError()
        return self


class RegistryProviderPlatformCreateOptions(BaseModel):
    """Options for creating a registry provider platform."""

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    os: str = Field(alias="os")
    arch: str = Field(alias="arch")
    shasum: str = Field(alias="shasum")
    filename: str = Field(alias="filename")

    @model_validator(mode="after")
    def valid(self) -> RegistryProviderPlatformCreateOptions:
        if not valid_string(self.os):
            raise RequiredOSError()
        if not valid_string(self.arch):
            raise RequiredArchError()
        if not valid_string_id(self.shasum):
            raise RequiredShasumError()
        if not valid_string_id(self.filename):
            raise RequiredFilenameError()
        return self


class RegistryProviderPlatformListOptions(BaseModel):
    """Options for listing registry provider platforms."""

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    page_size: int | None = Field(alias="page[size]", default=None)
