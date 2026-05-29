# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ToolVersionArchitecture(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)
    url: str | None = None
    sha: str | None = None
    os: str | None = None
    arch: str | None = None


class TerraformVersion(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)
    id: str | None = None
    version: str | None = None
    url: str | None = None
    sha: str | None = None
    official: bool | None = None
    enabled: bool | None = None
    beta: bool | None = None
    deprecated: bool | None = None
    deprecated_reason: str | None = Field(default=None, alias="deprecated-reason")
    usage: int | None = None
    created_at: str | None = Field(default=None, alias="created-at")
    archs: list[ToolVersionArchitecture] | None = None


class TerraformVersionCreateOptions(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)
    version: str
    url: str
    sha: str
    official: bool | None = None
    enabled: bool | None = None
    beta: bool | None = None
    deprecated: bool | None = None
    deprecated_reason: str | None = Field(default=None, alias="deprecated-reason")
    archs: list[ToolVersionArchitecture] | None = None


class TerraformVersionUpdateOptions(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)
    version: str | None = None
    url: str | None = None
    sha: str | None = None
    official: bool | None = None
    enabled: bool | None = None
    beta: bool | None = None
    deprecated: bool | None = None
    deprecated_reason: str | None = Field(default=None, alias="deprecated-reason")
    archs: list[ToolVersionArchitecture] | None = None


class OpaVersion(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)
    id: str | None = None
    version: str | None = None
    url: str | None = None
    sha: str | None = None
    official: bool | None = None
    enabled: bool | None = None
    beta: bool | None = None
    deprecated: bool | None = None
    deprecated_reason: str | None = Field(default=None, alias="deprecated-reason")
    usage: int | None = None
    created_at: str | None = Field(default=None, alias="created-at")
    archs: list[ToolVersionArchitecture] | None = None


class OpaVersionCreateOptions(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)
    version: str
    url: str
    sha: str
    official: bool | None = None
    enabled: bool | None = None
    beta: bool | None = None
    deprecated: bool | None = None
    deprecated_reason: str | None = Field(default=None, alias="deprecated-reason")
    archs: list[ToolVersionArchitecture] | None = None


class OpaVersionUpdateOptions(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)
    version: str | None = None
    url: str | None = None
    sha: str | None = None
    official: bool | None = None
    enabled: bool | None = None
    beta: bool | None = None
    deprecated: bool | None = None
    deprecated_reason: str | None = Field(default=None, alias="deprecated-reason")
    archs: list[ToolVersionArchitecture] | None = None


class SentinelVersion(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)
    id: str | None = None
    version: str | None = None
    url: str | None = None
    sha: str | None = None
    official: bool | None = None
    enabled: bool | None = None
    beta: bool | None = None
    deprecated: bool | None = None
    deprecated_reason: str | None = Field(default=None, alias="deprecated-reason")
    usage: int | None = None
    created_at: str | None = Field(default=None, alias="created-at")
    archs: list[ToolVersionArchitecture] | None = None


class SentinelVersionCreateOptions(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)
    version: str
    url: str
    sha: str
    official: bool | None = None
    enabled: bool | None = None
    beta: bool | None = None
    deprecated: bool | None = None
    deprecated_reason: str | None = Field(default=None, alias="deprecated-reason")
    archs: list[ToolVersionArchitecture] | None = None


class SentinelVersionUpdateOptions(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)
    version: str | None = None
    url: str | None = None
    sha: str | None = None
    official: bool | None = None
    enabled: bool | None = None
    beta: bool | None = None
    deprecated: bool | None = None
    deprecated_reason: str | None = Field(default=None, alias="deprecated-reason")
    archs: list[ToolVersionArchitecture] | None = None
