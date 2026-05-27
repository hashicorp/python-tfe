# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from .organization import Organization
from .registry_module import RegistryModule
from .variable import CategoryType
from .workspace import ExecutionMode, Workspace


class NoCodeModuleIncludeOpt(str, Enum):
    """Include options for no-code module read."""

    VARIABLE_OPTIONS = "variable_options"


class NoCodeVariableOption(BaseModel):
    """An allowed-values constraint on a single variable in a no-code module.

    Returned as part of a no-code module's ``variable-options`` relationship.
    The same shape is used both when reading a module (with ``include`` set)
    and when constructing create/update options.
    """

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    id: str | None = None
    variable_name: str | None = Field(default=None, alias="variable-name")
    variable_type: str | None = Field(default=None, alias="variable-type")
    options: list[str] = Field(default_factory=list)


class NoCodeModule(BaseModel):
    """Represents a no-code module — a registry module that has been enabled
    for the no-code provisioning workflow.
    """

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    id: str | None = None
    enabled: bool | None = None
    version_pin: str | None = Field(default=None, alias="version-pin")

    # Relationships
    organization: Organization | None = None
    registry_module: RegistryModule | None = Field(
        default=None, alias="registry-module"
    )
    variable_options: list[NoCodeVariableOption] = Field(
        default_factory=list, alias="variable-options"
    )


class NoCodeModuleCreateOptions(BaseModel):
    """Options for enabling no-code provisioning on a registry module."""

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    registry_module_id: str = Field(
        ..., description="ID of the registry module to enable"
    )
    enabled: bool | None = None
    version_pin: str | None = Field(default=None, alias="version-pin")
    variable_options: list[NoCodeVariableOption] = Field(
        default_factory=list, alias="variable-options"
    )


class NoCodeModuleUpdateOptions(BaseModel):
    """Options for updating no-code provisioning settings.

    ``variable_options`` entries with an ``id`` set update existing options;
    entries without an ``id`` add new options.
    """

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    registry_module_id: str | None = None
    enabled: bool | None = None
    version_pin: str | None = Field(default=None, alias="version-pin")
    variable_options: list[NoCodeVariableOption] | None = Field(
        default=None, alias="variable-options"
    )


class NoCodeModuleReadOptions(BaseModel):
    """Options for reading a no-code module with optional includes."""

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    include: list[NoCodeModuleIncludeOpt] | None = None


class NoCodeWorkspaceVariable(BaseModel):
    """A workspace variable supplied inline during no-code workspace creation
    or upgrade. Mirrors the fields accepted under the ``vars`` relationship.
    """

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    key: str
    value: str | None = None
    description: str | None = None
    category: CategoryType | None = None
    hcl: bool | None = None
    sensitive: bool | None = None


class NoCodeWorkspaceCreateOptions(BaseModel):
    """Options for creating a workspace from a no-code module."""

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    name: str = Field(..., description="Workspace name")
    project_id: str = Field(
        ..., description="ID of the project to create the workspace in"
    )
    description: str | None = None
    agent_pool_id: str | None = Field(default=None, alias="agent-pool-id")
    auto_apply: bool | None = None
    execution_mode: ExecutionMode | None = Field(default=None, alias="execution-mode")
    source_name: str | None = Field(default=None, alias="source-name")
    source_url: str | None = Field(default=None, alias="source-url")
    terraform_version: str | None = Field(default=None, alias="terraform-version")
    vars: list[NoCodeWorkspaceVariable] = Field(default_factory=list)


class NoCodeWorkspaceUpgradeOptions(BaseModel):
    """Options for initiating a no-code workspace upgrade."""

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    vars: list[NoCodeWorkspaceVariable] = Field(default_factory=list)


class WorkspaceUpgrade(BaseModel):
    """The result of initiating or polling a no-code workspace upgrade."""

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    id: str | None = None
    status: str | None = None
    plan_url: str | None = Field(default=None, alias="plan-url")
    message: str | None = None

    # Relationships
    workspace: Workspace | None = None


class RegistryModuleVariable(BaseModel):
    """A variable declared by a specific version of a registry module.

    Returned by ``client.no_code_modules.read_variables`` for use in driving
    UIs that build no-code workspace creation forms.
    """

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    id: str | None = None
    name: str | None = None
    type: str | None = None
    description: str | None = None
    default: str | None = None
    required: bool | None = None
    sensitive: bool | None = None
    options: list[str] = Field(default_factory=list)


__all__ = [
    "NoCodeModule",
    "NoCodeModuleCreateOptions",
    "NoCodeModuleIncludeOpt",
    "NoCodeModuleReadOptions",
    "NoCodeModuleUpdateOptions",
    "NoCodeVariableOption",
    "NoCodeWorkspaceCreateOptions",
    "NoCodeWorkspaceUpgradeOptions",
    "NoCodeWorkspaceVariable",
    "RegistryModuleVariable",
    "WorkspaceUpgrade",
]
