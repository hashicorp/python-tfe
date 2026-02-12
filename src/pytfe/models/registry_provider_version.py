from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ..errors import (
    InvalidKeyIDError,
    InvalidVersionError,
    RequiredPrivateRegistryError,
)
from ..utils import valid_string_id
from .registry_provider import (
    RegistryName,
    RegistryProviderID,
)


class RegistryProviderVersionPermissions(BaseModel):
    """Registry provider version permissions."""

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    can_delete: bool = Field(alias="can-delete")
    can_upload_asset: bool = Field(alias="can-upload-asset")


class RegistryProviderVersion(BaseModel):
    """Registry provider version model."""

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    id: str
    version: str
    created_at: datetime = Field(alias="created-at")
    updated_at: datetime = Field(alias="updated-at")
    key_id: str = Field(alias="key-id")
    protocols: list[str]
    permissions: RegistryProviderVersionPermissions
    shasums_uploaded: bool = Field(alias="shasums-uploaded")
    shasums_sig_uploaded: bool = Field(alias="shasums-sig-uploaded")

    # Relations
    registry_provider: dict[str, Any] | None = Field(
        alias="registry-provider", default=None
    )
    registry_provider_platforms: list[dict[str, Any]] | None = Field(
        alias="platforms", default=None
    )

    # Links
    links: dict[str, Any] | None = None

    def shasums_upload_url(self) -> str:
        """ShasumsUploadURL returns the upload URL to upload shasums if one is available"""
        if self.links is None:
            raise ValueError(
                "The registry provider version does not contain a shasums upload link"
            )
        upload_url = str(self.links.get("shasums-upload"))
        if not upload_url:
            raise ValueError(
                "The registry provider version does not contain a shasums upload link"
            )

        if upload_url == "":
            raise ValueError(
                "The registry provider version shasums upload URL is empty"
            )

        return upload_url

    def shasums_sig_upload_url(self) -> str:
        """ShasumsSigUploadURL returns the URL to upload a shasums sig"""
        if self.links is None:
            raise ValueError(
                "The registry provider version does not contain a shasums sig upload link"
            )
        upload_url = str(self.links.get("shasums-sig-upload"))
        if not upload_url:
            raise ValueError(
                "The registry provider version does not contain a shasums sig upload link"
            )

        if upload_url == "":
            raise ValueError(
                "The registry provider version shasums sig upload URL is empty"
            )

        return upload_url

    def shasums_download_url(self) -> str:
        """ShasumsDownloadURL returns the URL to download the shasums for the registry version"""
        if self.links is None:
            raise ValueError(
                "The registry provider version does not contain a shasums download link"
            )
        download_url = str(self.links.get("shasums-download"))
        if not download_url:
            raise ValueError(
                "The registry provider version does not contain a shasums download link"
            )

        if download_url == "":
            raise ValueError(
                "The registry provider version shasums download URL is empty"
            )

        return download_url

    def shasums_sig_download_url(self) -> str:
        """ShasumsSigDownloadURL returns the URL to download the shasums sig for the registry version"""
        if self.links is None:
            raise ValueError(
                "The registry provider version does not contain a shasums sig download link"
            )
        download_url = str(self.links.get("shasums-sig-download"))
        if not download_url:
            raise ValueError(
                "The registry provider version does not contain a shasums sig download link"
            )

        if download_url == "":
            raise ValueError(
                "The registry provider version shasums sig download URL is empty"
            )

        return download_url


class RegistryProviderVersionID(RegistryProviderID):
    """Registry provider version identifier.

    This extends RegistryProviderID with a version field to uniquely
    identify a specific version of a provider.
    """

    version: str

    @model_validator(mode="after")
    def valid(self) -> RegistryProviderVersionID:
        if not valid_string_id(self.version):
            raise InvalidVersionError()
        if self.registry_name != RegistryName.PRIVATE:
            raise RequiredPrivateRegistryError()
        return self


class RegistryProviderVersionCreateOptions(BaseModel):
    """Options for creating a registry provider version."""

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    version: str
    key_id: str = Field(alias="key-id")
    protocols: list[str]

    # validation method for version and key_id
    @model_validator(mode="after")
    def valid(self) -> RegistryProviderVersionCreateOptions:
        if not valid_string_id(self.version):
            raise InvalidVersionError()
        if not valid_string_id(self.key_id):
            raise InvalidKeyIDError()
        return self


class RegistryProviderVersionListOptions(BaseModel):
    """Options for listing registry provider versions."""

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    page_size: int | None = Field(alias="page[size]", default=None)
