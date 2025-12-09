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

    page_number: int | None = Field(alias="page[number]", default=None)
    page_size: int | None = Field(alias="page[size]", default=None)
