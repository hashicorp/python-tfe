# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class OrganizationUpdateOptions(BaseModel):
    # populate_by_name lets existing callers keep passing snake_case
    # kwargs while we add aliases that produce the correct hyphenated
    # JSON:API wire names on dump. The resource layer now uses
    # ``model_dump(by_alias=True, ...)`` to honour those aliases.
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    name: str | None = None
    email: str | None = None
    assessments_enforced: bool | None = None
    collaborator_auth_policy: str | None = None
    cost_estimation_enabled: bool | None = None
    default_execution_mode: str | None = Field(
        default=None, alias="default-execution-mode"
    )
    # Sent as a flat ``default-agent-pool-id`` attribute on PATCH; not the
    # ``default-agent-pool`` relationship shape that reads return.
    default_agent_pool_id: str | None = Field(
        default=None, alias="default-agent-pool-id"
    )
    # Controls whether the org enforces the per-token TTL policy described
    # by the new client.organization_token_ttl_policies resource.
    max_ttl_enabled: bool | None = Field(default=None, alias="max-ttl-enabled")
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
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    name: str | None = None
    email: str | None = None
    assessments_enforced: bool | None = None
    collaborator_auth_policy: str | None = None
    cost_estimation_enabled: bool | None = None
    default_execution_mode: str | None = Field(
        default=None, alias="default-execution-mode"
    )
    default_agent_pool_id: str | None = Field(
        default=None, alias="default-agent-pool-id"
    )
    max_ttl_enabled: bool | None = Field(default=None, alias="max-ttl-enabled")
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
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    name: str | None = None
    assessments_enforced: bool | None = None
    collaborator_auth_policy: str | None = None
    cost_estimation_enabled: bool | None = None
    created_at: datetime | None = None
    default_execution_mode: str | None = Field(
        default=None, alias="default-execution-mode"
    )
    max_ttl_enabled: bool | None = Field(default=None, alias="max-ttl-enabled")
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
    # ``default_agent_pool`` arrives as a JSON:API relationship at read time
    # (under ``relationships.default-agent-pool.data.id``). The resource
    # layer lifts that into this dict-shaped field; the modelling remains
    # loose because callers normally only need the id string.
    default_agent_pool: dict | None = None
    data_retention_policy: dict | None = None
    data_retention_policy_choice: dict | None = None


# ---------------------------------------------------------------------------
# Organization default settings (provider-parity focused models)
# ---------------------------------------------------------------------------


class OrganizationDefaultSettings(BaseModel):
    """Focused read-model for an organisation's default execution mode +
    default agent pool, mirroring the provider's
    ``tfe_organization_default_settings`` resource. This is a thin
    projection of the underlying ``Organization`` model — both share the
    same upstream endpoint (``GET /api/v2/organizations/{org}``).
    """

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    id: str | None = None
    default_execution_mode: str | None = Field(
        default=None, alias="default-execution-mode"
    )
    # Lifted from ``relationships.default-agent-pool.data.id`` at parse
    # time, not from ``attributes``. ``None`` means the org has no
    # default agent pool configured.
    default_agent_pool_id: str | None = None


class OrganizationDefaultSettingsUpdateOptions(BaseModel):
    """Focused write-model for setting default execution mode + default
    agent pool. Both fields are optional individually; the validator
    below enforces the cross-field constraint that the API itself
    documents.
    """

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    default_execution_mode: str | None = Field(
        default=None, alias="default-execution-mode"
    )
    default_agent_pool_id: str | None = Field(
        default=None, alias="default-agent-pool-id"
    )

    @model_validator(mode="after")
    def _agent_pool_requires_agent_mode(
        self,
    ) -> OrganizationDefaultSettingsUpdateOptions:
        """``default-agent-pool-id`` is only meaningful when
        ``default-execution-mode == "agent"``. The upstream docs say to
        not specify it for ``remote``/``local`` modes. Enforce that
        locally so callers see the mistake at construction time, not as
        an opaque server-side 422.

        We only enforce the constraint when both fields are present in
        the same call — that lets an isolated update like
        ``OrganizationDefaultSettingsUpdateOptions(default_execution_mode="remote")``
        clear the mode without forcing the caller to also explicitly
        null the agent pool.
        """
        if (
            self.default_agent_pool_id is not None
            and self.default_execution_mode is not None
            and self.default_execution_mode != "agent"
        ):
            raise ValueError(
                "default_agent_pool_id is only valid when "
                "default_execution_mode='agent'; got "
                f"default_execution_mode={self.default_execution_mode!r}"
            )
        return self

    def to_payload(self) -> dict[str, Any]:
        """Build the JSON:API ``attributes`` dict, emitting only the
        fields the caller explicitly set. Distinguishes "omit" from
        "explicit None" by inspecting Pydantic's ``model_fields_set`` —
        so callers can pass ``default_agent_pool_id=None`` to clear a
        previously-set agent pool, while merely omitting the kwarg
        leaves the server value untouched.
        """
        attrs: dict[str, Any] = {}
        set_fields = self.model_fields_set
        if "default_execution_mode" in set_fields:
            # Treat None as "leave alone" rather than "send null" here,
            # because the API has no documented null-write behaviour for
            # execution mode.
            if self.default_execution_mode is not None:
                attrs["default-execution-mode"] = self.default_execution_mode
        if "default_agent_pool_id" in set_fields:
            # None becomes wire null, which clears the agent pool.
            attrs["default-agent-pool-id"] = self.default_agent_pool_id
        return attrs


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


# RunQueue represents the current run queue of an organization.
class RunQueue(BaseModel):
    pagination: Pagination | None = None
    items: list[Run] = Field(default_factory=list)


class ReadRunQueueOptions(BaseModel):
    # List options for pagination
    page_number: int | None = None
    page_size: int | None = None
