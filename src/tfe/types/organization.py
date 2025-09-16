from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

__all__ = [
    "OrganizationUpdateOptions",
    "OrganizationCreateOptions",
    "Organization",
]


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
