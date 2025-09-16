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


class Capacity(BaseModel):
    organization: str
    pending: int
    running: int


class Entitlements(BaseModel):
    id: str
    agents: bool | None = None
    audit_logging: bool | None = None
    cost_estimation: bool | None = None
    global_run_tasks: bool | None = None
    operations: bool | None = None
    private_module_registry: bool | None = None
    private_run_tasks: bool | None = None
    run_tasks: bool | None = None
    sso: bool | None = None
    sentinel: bool | None = None
    state_storage: bool | None = None
    teams: bool | None = None
    vcs_integrations: bool | None = None
    waypoint_actions: bool | None = None
    waypoint_templates_and_addons: bool | None = None


class Run(BaseModel):
    id: str
    status: RunStatus
    # Add other Run fields as needed


class Pagination(BaseModel):
    current_page: int
    total_count: int
    # Add other pagination fields as needed


class RunQueue(BaseModel):
    pagination: Pagination | None = None
    items: list[Run] = Field(default_factory=list)


class ReadRunQueueOptions(BaseModel):
    # List options for pagination
    page_number: int | None = None
    page_size: int | None = None


class DataRetentionPolicy(BaseModel):
    """Deprecated: Use DataRetentionPolicyDeleteOlder instead."""

    id: str
    delete_older_than_n_days: int


class DataRetentionPolicyDeleteOlder(BaseModel):
    id: str
    delete_older_than_n_days: int


class DataRetentionPolicyDontDelete(BaseModel):
    id: str


class DataRetentionPolicyChoice(BaseModel):
    """Polymorphic data retention policy choice."""

    data_retention_policy: DataRetentionPolicy | None = None
    data_retention_policy_delete_older: DataRetentionPolicyDeleteOlder | None = None
    data_retention_policy_dont_delete: DataRetentionPolicyDontDelete | None = None

    def is_populated(self) -> bool:
        """Returns whether one of the choices is populated."""
        return (
            self.data_retention_policy is not None
            or self.data_retention_policy_delete_older is not None
            or self.data_retention_policy_dont_delete is not None
        )

    def convert_to_legacy_struct(self) -> DataRetentionPolicy | None:
        """Convert the DataRetentionPolicyChoice to the legacy DataRetentionPolicy struct."""
        if not self.is_populated():
            return None

        if self.data_retention_policy is not None:
            return self.data_retention_policy
        elif self.data_retention_policy_delete_older is not None:
            return DataRetentionPolicy(
                id=self.data_retention_policy_delete_older.id,
                delete_older_than_n_days=self.data_retention_policy_delete_older.delete_older_than_n_days,
            )
        return None


class DataRetentionPolicySetOptions(BaseModel):
    """Deprecated: Use DataRetentionPolicyDeleteOlderSetOptions instead."""

    delete_older_than_n_days: int


class DataRetentionPolicyDeleteOlderSetOptions(BaseModel):
    delete_older_than_n_days: int


class DataRetentionPolicyDontDeleteSetOptions(BaseModel):
    pass  # No additional fields needed
