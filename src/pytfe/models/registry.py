# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""Models for the public Terraform Registry module API (registry.terraform.io).

These are **not** JSON:API resources — the registry returns plain snake_case
JSON with offset/limit pagination — so they inherit ``BaseModel`` and are
prefixed ``PublicRegistry*`` to distinguish them from the HCP Terraform
private-registry models (``RegistryModule`` and friends).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class PublicRegistryModuleInput(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    name: str | None = None
    type: str | None = None
    description: str | None = None
    default: str | None = None
    required: bool | None = None


class PublicRegistryModuleOutput(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    name: str | None = None
    description: str | None = None


class PublicRegistryModuleResource(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    name: str | None = None
    type: str | None = None


class PublicRegistryModuleProviderDependency(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    name: str | None = None
    namespace: str | None = None
    source: str | None = None
    version: str | None = None


class PublicRegistryModuleDetail(BaseModel):
    """A module's ``root``, one of its ``submodules``, or an ``examples`` entry."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    path: str | None = None
    name: str | None = None
    readme: str | None = None
    empty: bool | None = None
    inputs: list[PublicRegistryModuleInput] | None = None
    outputs: list[PublicRegistryModuleOutput] | None = None
    dependencies: list[Any] | None = None
    provider_dependencies: list[PublicRegistryModuleProviderDependency] | None = None
    resources: list[PublicRegistryModuleResource] | None = None


class PublicRegistryModule(BaseModel):
    """A module entry from the public Terraform Registry."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    id: str | None = None
    owner: str | None = None
    namespace: str | None = None
    name: str | None = None
    version: str | None = None
    provider: str | None = None
    provider_logo_url: str | None = None
    description: str | None = None
    source: str | None = None
    tag: str | None = None
    published_at: datetime | None = None
    downloads: int | None = None
    verified: bool | None = None
    root: PublicRegistryModuleDetail | None = None
    submodules: list[PublicRegistryModuleDetail] | None = None
    examples: list[PublicRegistryModuleDetail] | None = None
    providers: list[str] | None = None
    versions: list[str] | None = None
    deprecation: dict[str, Any] | None = None


class PublicRegistryPagination(BaseModel):
    """The ``meta`` block of a paginated registry response."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    limit: int | None = None
    current_offset: int | None = None
    next_offset: int | None = None
    next_url: str | None = None


class PublicRegistryModuleVersion(BaseModel):
    """A single version entry from the versions endpoint."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    version: str | None = None
    root: PublicRegistryModuleDetail | None = None
    submodules: list[PublicRegistryModuleDetail] | None = None
    deprecation: dict[str, Any] | None = None


class PublicRegistryModuleVersions(BaseModel):
    """The set of available versions for one module (versions endpoint)."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    source: str | None = None
    versions: list[PublicRegistryModuleVersion] = Field(default_factory=list)


class PublicRegistryModuleDownloadsSummary(BaseModel):
    """Module download metrics summary (``/v2`` endpoint)."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    id: str | None = None
    week: int | None = None
    month: int | None = None
    year: int | None = None
    total: int | None = None


class PublicRegistryModuleListOptions(BaseModel):
    """Query options for listing public registry modules."""

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    provider: str | None = None
    verified: bool | None = None
    offset: int | None = None
    limit: int | None = None


class PublicRegistrySearchOptions(BaseModel):
    """Query options for searching public registry modules."""

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    provider: str | None = None
    namespace: str | None = None
    verified: bool | None = None
    offset: int | None = None
    limit: int | None = None
