from __future__ import annotations

from pydantic import BaseModel, Field

from .common import TagBinding


class Project(BaseModel):
    id: str = Field(
        json_schema_extra={"jsonapi_type": "primary", "jsonapi_name": "projects"}
    )
    name: str | None = None
    description: str = ""
    organization: str | None = None
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


class ProjectAddTagBindingsOptions(BaseModel):
    """Options for adding tag bindings to a project"""

    tag_bindings: list[TagBinding] = Field(default_factory=list)
