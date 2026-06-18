# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, model_validator

from ..errors import (
    InvalidNameError,
    InvalidNamespaceError,
    InvalidOrgError,
    InvalidValues,
)
from ..utils import valid_string_id
from ._base import TFEModel


class RegistryName(Enum):
    """Registry name enumeration."""

    PRIVATE = "private"
    PUBLIC = "public"


class RegistryProviderIncludeOps(Enum):
    """Registry provider include operations."""

    REGISTRY_PROVIDER_VERSIONS = "registry-provider-versions"


class RegistryProviderPermissions(BaseModel):
    """Registry provider permissions."""

    can_delete: bool = Field(alias="can-delete")

    model_config = {"populate_by_name": True}


class RegistryProvider(TFEModel):
    """Registry provider model."""

    id: str
    name: str = Field(alias="name", default="")
    namespace: str = Field(alias="namespace", default="")
    created_at: datetime | None = Field(alias="created-at", default=None)
    updated_at: datetime | None = Field(alias="updated-at", default=None)
    registry_name: RegistryName | None = Field(alias="registry-name", default=None)
    permissions: RegistryProviderPermissions | None = Field(
        alias="permissions", default=None
    )

    # Relations
    organization: dict[str, Any] | None = None
    registry_provider_versions: list[dict[str, Any]] | None = Field(
        alias="registry-provider-versions", default=None
    )

    # Links
    links: dict[str, Any] | None = None

    model_config = {"populate_by_name": True}


class RegistryProviderID(BaseModel):
    """Registry provider identifier."""

    organization_name: str
    registry_name: RegistryName
    namespace: str
    name: str

    @model_validator(mode="after")
    def valid(self) -> RegistryProviderID:
        """Validate the registry provider ID."""
        if not valid_string_id(self.organization_name):
            raise InvalidOrgError()
        if not valid_string_id(self.name):
            raise InvalidNameError()
        if not valid_string_id(self.namespace):
            raise InvalidNamespaceError()
        if not valid_string_id(self.registry_name.value):
            raise InvalidValues("invalid value for registry name")
        return self


class RegistryProviderCreateOptions(BaseModel):
    """Options for creating a registry provider."""

    name: str
    namespace: str
    registry_name: RegistryName = Field(alias="registry-name")

    model_config = {"populate_by_name": True}

    @model_validator(mode="after")
    def valid(self) -> RegistryProviderCreateOptions:
        """Validate the create options."""
        if not valid_string_id(self.name):
            raise InvalidNameError()
        if not valid_string_id(self.namespace):
            raise InvalidNamespaceError()
        return self


class RegistryProviderReadOptions(BaseModel):
    """Options for reading a registry provider."""

    include: list[RegistryProviderIncludeOps] | None = None


class RegistryProviderListOptions(BaseModel):
    """Options for listing registry providers."""

    registry_name: RegistryName | None = Field(
        alias="filter[registry_name]", default=None
    )
    organization_name: str | None = Field(
        alias="filter[organization_name]", default=None
    )
    search: str | None = Field(alias="q", default=None)
    include: list[RegistryProviderIncludeOps] | None = None
    page_number: int | None = Field(alias="page[number]", default=None)
    page_size: int | None = Field(alias="page[size]", default=None)

    model_config = {"populate_by_name": True}


class RegistryProviderList(BaseModel):
    """Registry provider list response."""

    items: list[RegistryProvider]
    pagination: dict[str, Any] | None = None
