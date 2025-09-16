from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ExecutionMode(str, Enum):
    REMOTE = "remote"
    AGENT = "agent"
    LOCAL = "local"


class RunStatus(str, Enum):
    PLANNING = "planning"
    PLANNED = "planned"
    APPLIED = "applied"
    CANCELED = "canceled"
    ERRORED = "errored"


class Organization(BaseModel):
    id: str
    name: str
    email: str | None = None


class Project(BaseModel):
    """Project represents a Terraform Enterprise project"""

    id: str
    name: str
    description: str = ""
    organization: str
    created_at: str = ""
    updated_at: str = ""
    workspace_count: int = 0
    default_execution_mode: str = "remote"


class ProjectListOptions(BaseModel):
    """Options for listing projects"""

    # Optional: String used to filter results by complete project name
    name: str | None = None
    # Optional: Query string to search projects by names
    query: str | None = None
    # Optional: Include related resources
    include: list[str] | None = None
    # Pagination options
    page_number: int | None = None
    page_size: int | None = None


class ProjectCreateOptions(BaseModel):
    """Options for creating a project"""

    # Required: A name to identify the project
    name: str
    # Optional: A description for the project
    description: str | None = None


class ProjectUpdateOptions(BaseModel):
    """Options for updating a project"""

    # Optional: A name to identify the project
    name: str | None = None
    # Optional: A description for the project
    description: str | None = None


class Workspace(BaseModel):
    id: str
    name: str
    organization: str
    execution_mode: ExecutionMode | None = None
    project_id: str | None = None
    tags: list[str] = Field(default_factory=list)


class TagBinding(BaseModel):
    """Tag binding associates a key-value pair with a resource"""

    id: str | None = None
    key: str
    value: str | None = None


class EffectiveTagBinding(BaseModel):
    """Effective tag binding includes inherited bindings"""

    id: str | None = None
    key: str
    value: str | None = None
    # Links indicate inheritance (e.g., from project to workspace)
    links: dict[str, Any] | None = None


class ProjectAddTagBindingsOptions(BaseModel):
    """Options for adding tag bindings to a project"""

    tag_bindings: list[TagBinding]
