"""Variable set type definitions for the TFE API."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

from ..types import CategoryType

if TYPE_CHECKING:
    from ..types import Organization, Workspace
    from .project import Project


class VariableSetIncludeOpt(str, Enum):
    """Include options for variable set operations."""

    WORKSPACES = "workspaces"
    PROJECTS = "projects"
    VARS = "vars"
    CURRENT_RUN = "current-run"


class Parent(BaseModel):
    """Parent represents the variable set's parent (organizations and projects are supported)."""

    organization: Organization | None = None
    project: Project | None = None


class VariableSet(BaseModel):
    """Represents a Terraform Enterprise variable set."""

    id: str | None = None
    name: str | None = None
    description: str | None = None
    global_: bool | None = Field(default=None, alias="global")
    priority: bool | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    # Relations
    organization: Organization | None = None
    workspaces: list[Workspace] = Field(default_factory=list)
    projects: list[Project] = Field(default_factory=list)
    vars: list[VariableSetVariable] = Field(default_factory=list)
    parent: Parent | None = None


class VariableSetVariable(BaseModel):
    """Represents a variable within a variable set."""

    id: str | None = None
    key: str
    value: str | None = None
    description: str | None = None
    category: CategoryType
    hcl: bool | None = None
    sensitive: bool | None = None
    version_id: str | None = None

    # Relations
    variable_set: VariableSet | None = None


# Variable Set Options


class VariableSetListOptions(BaseModel):
    """Options for listing variable sets."""

    # Pagination options
    page_number: int | None = None
    page_size: int | None = None
    include: list[VariableSetIncludeOpt] | None = None
    query: str | None = None  # Filter by name


class VariableSetCreateOptions(BaseModel):
    """Options for creating a variable set."""

    name: str
    description: str | None = None
    global_: bool = Field(alias="global")
    priority: bool | None = None
    parent: Parent | None = None


class VariableSetReadOptions(BaseModel):
    """Options for reading a variable set."""

    include: list[VariableSetIncludeOpt] | None = None


class VariableSetUpdateOptions(BaseModel):
    """Options for updating a variable set."""

    name: str | None = None
    description: str | None = None
    global_: bool | None = Field(alias="global", default=None)
    priority: bool | None = None


class VariableSetApplyToWorkspacesOptions(BaseModel):
    """Options for applying a variable set to workspaces."""

    workspaces: list[Workspace] = Field(default_factory=list)


class VariableSetRemoveFromWorkspacesOptions(BaseModel):
    """Options for removing a variable set from workspaces."""

    workspaces: list[Workspace] = Field(default_factory=list)


class VariableSetApplyToProjectsOptions(BaseModel):
    """Options for applying a variable set to projects."""

    projects: list[Project] = Field(default_factory=list)


class VariableSetRemoveFromProjectsOptions(BaseModel):
    """Options for removing a variable set from projects."""

    projects: list[Project] = Field(default_factory=list)


class VariableSetUpdateWorkspacesOptions(BaseModel):
    """Options for updating workspaces associated with a variable set."""

    workspaces: list[Workspace] = Field(default_factory=list)


# Variable Set Variable Options


class VariableSetVariableListOptions(BaseModel):
    """Options for listing variables in a variable set."""

    # Pagination options
    page_number: int | None = None
    page_size: int | None = None


class VariableSetVariableCreateOptions(BaseModel):
    """Options for creating a variable in a variable set."""

    key: str
    value: str | None = None
    description: str | None = None
    category: CategoryType
    hcl: bool | None = None
    sensitive: bool | None = None


class VariableSetVariableUpdateOptions(BaseModel):
    """Options for updating a variable in a variable set."""

    key: str | None = None
    value: str | None = None
    description: str | None = None
    hcl: bool | None = None
    sensitive: bool | None = None


# Model rebuild functionality for runtime
def _rebuild_models() -> None:
    """Rebuild models to resolve forward references at runtime."""
    try:
        # Import the main types to ensure they're available
        from ..types import Organization, Workspace  # noqa: F401
        from .project import Project  # noqa: F401

        # Rebuild models that have forward references
        Parent.model_rebuild()
        VariableSet.model_rebuild()
        VariableSetVariable.model_rebuild()
        VariableSetCreateOptions.model_rebuild()
        VariableSetApplyToWorkspacesOptions.model_rebuild()
        VariableSetRemoveFromWorkspacesOptions.model_rebuild()
        VariableSetApplyToProjectsOptions.model_rebuild()
        VariableSetRemoveFromProjectsOptions.model_rebuild()
        VariableSetUpdateWorkspacesOptions.model_rebuild()
    except ImportError:
        # If the main types aren't available yet, models will be rebuilt later
        pass


# Call rebuild when module is imported
_rebuild_models()
