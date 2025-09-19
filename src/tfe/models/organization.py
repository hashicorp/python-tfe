from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class OrganizationUpdateOptions(BaseModel):
    name: str | None = None
    email: str | None = None
    assessments_enforced: bool | None = None
    collaborator_auth_policy: str | None = None
    cost_estimation_enabled: bool | None = None
    default_execution_mode: str | None = None
    external_id: str | None = None
    is_unified: bool | None = None
    owners_team_saml_role_id: str | None = None
    permissions: dict | None = None
    saml_enabled: bool | None = None
    session_remember: int | None = None
    session_timeout: int | None = None
    two_factor_conformant: bool | None = None
    send_passing_statuses_for_untriggered_speculative_plans: bool | None = None
    remaining_testable_count: int | None = None
    speculative_plan_management_enabled: bool | None = None
    aggregated_commit_status_enabled: bool | None = None
    allow_force_delete_workspaces: bool | None = None
    default_project: dict | None = None
    default_agent_pool: dict | None = None
    data_retention_policy: dict | None = None
    data_retention_policy_choice: dict | None = None


class OrganizationCreateOptions(BaseModel):
    name: str | None = None
    email: str | None = None
    assessments_enforced: bool | None = None
    collaborator_auth_policy: str | None = None
    cost_estimation_enabled: bool | None = None
    default_execution_mode: str | None = None
    external_id: str | None = None
    is_unified: bool | None = None
    owners_team_saml_role_id: str | None = None
    permissions: dict | None = None
    saml_enabled: bool | None = None
    session_remember: int | None = None
    session_timeout: int | None = None
    two_factor_conformant: bool | None = None
    send_passing_statuses_for_untriggered_speculative_plans: bool | None = None
    remaining_testable_count: int | None = None
    speculative_plan_management_enabled: bool | None = None
    aggregated_commit_status_enabled: bool | None = None
    allow_force_delete_workspaces: bool | None = None
    default_project: dict | None = None
    default_agent_pool: dict | None = None
    data_retention_policy: dict | None = None
    data_retention_policy_choice: dict | None = None


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
    name: str | None = None
    assessments_enforced: bool | None = None
    collaborator_auth_policy: str | None = None
    cost_estimation_enabled: bool | None = None
    created_at: datetime | None = None
    default_execution_mode: str | None = None
    email: str | None = None
    external_id: str | None = None
    id: str | None = None
    is_unified: bool | None = None
    owners_team_saml_role_id: str | None = None
    permissions: dict | None = None
    saml_enabled: bool | None = None
    session_remember: int | None = None
    session_timeout: int | None = None
    trial_expires_at: datetime | None = None
    two_factor_conformant: bool | None = None
    send_passing_statuses_for_untriggered_speculative_plans: bool | None = None
    remaining_testable_count: int | None = None
    speculative_plan_management_enabled: bool | None = None
    aggregated_commit_status_enabled: bool | None = None
    allow_force_delete_workspaces: bool | None = None
    default_project: dict | None = None
    default_agent_pool: dict | None = None
    data_retention_policy: dict | None = None
    data_retention_policy_choice: dict | None = None


class Project(BaseModel):
    id: str
    name: str
    organization: str


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
