from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from .apply import Apply
from .comment import Comment
from .configuration_version import ConfigurationVersion
from .cost_estimate import CostEstimate
from .plan import Plan
from .policy_check import PolicyCheck
from .run_event import RunEvent
from .task_stage import TaskStage
from .user import User
from .workspace import Workspace


class RunSource(str, Enum):
    """RunSource represents a source type of a run."""

    Run_Source_API = "tfe-api"
    Run_Source_Configuration_Version = "tfe-configuration-version"
    Run_Source_UI = "tfe-ui"


class RunStatus(str, Enum):
    """RunStatus represents a run state."""

    Run_Applied = "applied"
    Run_Applying = "applying"
    Run_Apply_Queued = "apply_queued"
    Run_Canceled = "canceled"
    Run_Confirmed = "confirmed"
    Run_Cost_Estimated = "cost_estimated"
    Run_Cost_Estimating = "cost_estimating"
    Run_Discarded = "discarded"
    Run_Errored = "errored"
    Run_Fetching = "fetching"
    Run_Fetching_Completed = "fetching_completed"
    Run_Pending = "pending"
    Run_Planned = "planned"
    Run_Planned_And_Finished = "planned_and_finished"
    Run_Planned_And_Saved = "planned_and_saved"
    Run_Planning = "planning"
    Run_Plan_Queued = "plan_queued"
    Run_Policy_Checked = "policy_checked"
    Run_Policy_Checking = "policy_checking"
    Run_Policy_Override = "policy_override"
    Run_Policy_Soft_Failed = "policy_soft_failed"
    Run_Post_Plan_Awaiting_Decision = "post_plan_awaiting_decision"
    Run_Post_Plan_Completed = "post_plan_completed"
    Run_Post_Plan_Running = "post_plan_running"
    Run_Pre_Apply_Running = "pre_apply_running"
    Run_Pre_Apply_Completed = "pre_apply_completed"
    Run_Pre_Plan_Completed = "pre_plan_completed"
    Run_Pre_Plan_Running = "pre_plan_running"
    Run_Queuing = "queuing"
    Run_Queuing_Apply = "queuing_apply"


class RunIncludeOpt(str, Enum):
    RUN_WORKSPACE = "workspace"
    RUN_CREATED_BY = "created-by"
    RUN_PLAN = "plan"
    RUN_CONFIG_VER = "configuration-version"
    RUN_COST_ESTIMATE = "cost-estimate"
    RUN_APPLY = "apply"
    RUN_TASK_STAGES = "task-stages"
    RUN_CONFIG_VER_INGRESS = "configuration-version.ingress_attributes"


class RunOperation(str, Enum):
    """RunOperation represents an operation type of run."""

    Run_Operation_Plan_Apply = "plan_and_apply"
    Run_Operation_Plan_Only = "plan_only"
    Run_Operation_Refresh_Only = "refresh_only"
    Run_Operation_Destroy = "destroy"
    Run_Operation_Empty_Apply = "empty_apply"
    Run_Operation_Save_Plan = "save_plan"


class Run(BaseModel):
    """Run represents a Terraform Enterprise run."""

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    id: str
    actions: RunActions | None = Field(None, alias="actions")
    auto_apply: bool | None = Field(None, alias="auto-apply")
    allow_config_generation: bool | None = Field(None, alias="allow-config-generation")
    allow_empty_apply: bool | None = Field(None, alias="allow-empty-apply")
    canceled_at: datetime | None = Field(None, alias="canceled-at")
    created_at: datetime | None = Field(None, alias="created-at")
    force_cancel_available_at: datetime | None = Field(
        None, alias="force-cancel-available-at"
    )
    has_changes: bool | None = Field(None, alias="has-changes")
    is_destroy: bool | None = Field(None, alias="is-destroy")
    message: str | None = Field(None, alias="message")
    permissions: RunPermissions | None = Field(None, alias="permissions")
    policy_paths: list[str] | None = Field(None, alias="policy-paths")
    position_in_queue: int | None = Field(None, alias="position-in-queue")
    plan_only: bool | None = Field(None, alias="plan-only")
    refresh: bool | None = Field(None, alias="refresh")
    refresh_only: bool | None = Field(None, alias="refresh-only")
    replace_addrs: list[str] | None = Field(None, alias="replace-addrs")
    save_plan: bool | None = Field(None, alias="save-plan")
    source: RunSource | None = Field(None, alias="source")
    status: RunStatus | None = Field(None, alias="status")
    status_timestamps: RunStatusTimestamps | None = Field(
        None, alias="status-timestamps"
    )
    target_addrs: list[str] | None = Field(None, alias="target-addrs")
    terraform_version: str | None = Field(None, alias="terraform-version")
    trigger_reason: str | None = Field(None, alias="trigger-reason")
    variables: list[RunVariableAttr] | None = Field(None, alias="variables")

    # Relations
    apply: Apply | None = Field(None, alias="apply")
    configuration_version: ConfigurationVersion | None = Field(
        None, alias="configuration-version"
    )
    cost_estimate: CostEstimate | None = Field(None, alias="cost-estimate")
    created_by: User | None = Field(None, alias="created-by")
    confirmed_by: User | None = Field(None, alias="confirmed-by")
    plan: Plan | None = Field(None, alias="plan")
    policy_checks: list[PolicyCheck] | None = Field(None, alias="policy-checks")
    run_events: list[RunEvent] | None = Field(None, alias="run-events")
    task_stages: list[TaskStage] | None = Field(None, alias="task-stages")
    workspace: Workspace | None = Field(None, alias="workspace")
    comments: list[Comment] | None = Field(None, alias="comments")


class RunActions(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    is_cancelable: bool = Field(..., alias="is-cancelable")
    is_confirmable: bool = Field(..., alias="is-confirmable")
    is_discardable: bool = Field(..., alias="is-discardable")
    is_force_cancelable: bool = Field(..., alias="is-force-cancelable")


class RunPermissions(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    can_apply: bool = Field(..., alias="can-apply")
    can_cancel: bool = Field(..., alias="can-cancel")
    can_discard: bool = Field(..., alias="can-discard")
    can_force_cancel: bool = Field(..., alias="can-force-cancel")
    can_force_execute: bool = Field(..., alias="can-force-execute")


class RunStatusTimestamps(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    applied_at: datetime | None = Field(None, alias="applied-at")
    applying_at: datetime | None = Field(None, alias="applying-at")
    apply_queued_at: datetime | None = Field(None, alias="apply-queued-at")
    canceled_at: datetime | None = Field(None, alias="canceled-at")
    confirmed_at: datetime | None = Field(None, alias="confirmed-at")
    cost_estimated_at: datetime | None = Field(None, alias="cost-estimated-at")
    cost_estimating_at: datetime | None = Field(None, alias="cost-estimating-at")
    discarded_at: datetime | None = Field(None, alias="discarded-at")
    errored_at: datetime | None = Field(None, alias="errored-at")
    fetched_at: datetime | None = Field(None, alias="fetched-at")
    fetching_at: datetime | None = Field(None, alias="fetching-at")
    force_canceled_at: datetime | None = Field(None, alias="force-canceled-at")
    planned_and_finished_at: datetime | None = Field(
        None, alias="planned-and-finished-at"
    )
    planned_and_saved_at: datetime | None = Field(None, alias="planned-and-saved-at")
    planned_at: datetime | None = Field(None, alias="planned-at")
    planning_at: datetime | None = Field(None, alias="planning-at")
    plan_queueable_at: datetime | None = Field(None, alias="plan-queueable-at")
    plan_queued_at: datetime | None = Field(None, alias="plan-queued-at")
    policy_checked_at: datetime | None = Field(None, alias="policy-checked-at")
    policy_soft_failed_at: datetime | None = Field(None, alias="policy-soft-failed-at")
    post_plan_completed_at: datetime | None = Field(
        None, alias="post-plan-completed-at"
    )
    post_plan_running_at: datetime | None = Field(None, alias="post-plan-running-at")
    pre_plan_completed_at: datetime | None = Field(None, alias="pre-plan-completed-at")
    pre_plan_running_at: datetime | None = Field(None, alias="pre-plan-running-at")
    queuing_at: datetime | None = Field(None, alias="queuing-at")


class RunVariable(BaseModel):
    """RunVariable for create operations."""

    key: str
    value: str


class RunVariableAttr(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    key: str = Field(..., alias="key")
    value: str = Field(..., alias="value")


class RunList(BaseModel):
    """RunList represents a list of runs."""

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    items: list[Run] = Field(default_factory=list)
    current_page: int | None = None
    prev_page: int | None = None
    next_page: int | None = None
    total_pages: int | None = None
    total_count: int | None = None


class RunListOptions(BaseModel):
    page_number: int | None = Field(default=1, alias="page[number]")
    page_size: int | None = Field(default=20, alias="page[size]")

    user: str | None = Field(default=None, alias="search[user]")
    commit: str | None = Field(default=None, alias="search[commit]")
    search: str | None = Field(default=None, alias="search[basic]")
    status: str | None = Field(default=None, alias="filter[status]")
    source: str | None = Field(default=None, alias="filter[source]")
    operation: str | None = Field(default=None, alias="filter[operation]")

    include: list[RunIncludeOpt] | None = Field(default_factory=list, alias="include")


class OrganizationRunList(BaseModel):
    """
    OrganizationRunList represents a list of runs across an organization.
    It differs from the RunList in that it does not include a TotalCount of records in the pagination details
    """

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    items: list[Run] = Field(default_factory=list)
    current_page: int | None = None
    prev_page: int | None = None
    next_page: int | None = None


class RunListForOrganizationOptions(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    page_number: int | None = Field(default=1, alias="page[number]")
    page_size: int | None = Field(default=20, alias="page[size]")

    user: str | None = Field(default=None, alias="search[user]")
    commit: str | None = Field(default=None, alias="search[commit]")
    basic: str | None = Field(default=None, alias="search[basic]")
    status: str | None = Field(default=None, alias="filter[status]")
    source: str | None = Field(default=None, alias="filter[source]")
    operation: str | None = Field(default=None, alias="filter[operation]")
    agent_pool_names: str | None = Field(default=None, alias="filter[agent_pool_names]")
    status_group: str | None = Field(default=None, alias="filter[status_group]")
    timeframe: str | None = Field(default=None, alias="filter[timeframe]")
    workspace_names: str | None = Field(default=None, alias="filter[workspace_names]")

    include: list[RunIncludeOpt] | None = Field(default_factory=list, alias="include")


class RunCreateOptions(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    type: str = Field(default="runs")
    allow_config_generation: bool | None = Field(None, alias="allow-config-generation")
    allow_empty_apply: bool | None = Field(None, alias="allow-empty-apply")
    terraform_version: str | None = Field(None, alias="terraform-version")
    plan_only: bool | None = Field(None, alias="plan-only")
    is_destroy: bool | None = Field(None, alias="is-destroy")
    refresh: bool | None = Field(None, alias="refresh")
    refresh_only: bool | None = Field(None, alias="refresh-only")
    save_plan: bool | None = Field(None, alias="save-plan")
    message: str | None = Field(None, alias="message")
    configuration_version: ConfigurationVersion | None = Field(
        None, alias="configuration-version"
    )
    workspace: Workspace | None = Field(None, alias="workspace")
    target_addrs: list[str] | None = Field(None, alias="target-addrs")
    replace_addrs: list[str] | None = Field(None, alias="replace-addrs")
    policy_paths: list[str] | None = Field(None, alias="policy-paths")
    auto_apply: bool | None = Field(None, alias="auto-apply")
    variables: list[RunVariable] | None = Field(None, alias="variables")


class RunReadOptions(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    include: list[RunIncludeOpt] | None = Field(default_factory=list, alias="include")


class RunApplyOptions(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    comment: str | None = Field(None, alias="comment")


class RunCancelOptions(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    comment: str | None = Field(None, alias="comment")


class RunForceCancelOptions(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    comment: str | None = Field(None, alias="comment")


class RunDiscardOptions(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    comment: str | None = Field(None, alias="comment")
