from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


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


class RegistryProvider(BaseModel):
    """Registry provider model."""

    id: str
    name: str
    namespace: str
    created_at: datetime = Field(alias="created-at")
    updated_at: datetime = Field(alias="updated-at")
    registry_name: RegistryName = Field(alias="registry-name")
    permissions: RegistryProviderPermissions

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


class RegistryProviderCreateOptions(BaseModel):
    """Options for creating a registry provider."""

    name: str
    namespace: str
    registry_name: RegistryName = Field(alias="registry-name")

    model_config = {"populate_by_name": True}


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
