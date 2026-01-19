"""Run Task Request models for python-tfe.

This module contains the RunTaskRequest model which represents the payload
that TFC/TFE sends to external run task servers.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class RunTaskRequestCapabilities(BaseModel):
    """Capabilities that the caller supports."""

    outcomes: bool = Field(
        default=False,
        description="Whether the run task server supports outcomes"
    )


class RunTaskRequest(BaseModel):
    """Represents the payload that TFC/TFE sends to a run task's URL.
    
    This is the incoming request that your external run task server receives
    from Terraform Cloud/Enterprise when a run task is triggered.
    
    API Documentation:
        https://developer.hashicorp.com/terraform/enterprise/api-docs/run-tasks/run-tasks-integration#common-properties
    """

    access_token: str = Field(
        description="Token to use for authentication when sending callback"
    )
    capabilities: RunTaskRequestCapabilities | None = Field(
        default=None,
        description="Capabilities that the caller supports"
    )
    configuration_version_download_url: str | None = Field(
        default=None,
        description="URL to download the configuration version"
    )
    configuration_version_id: str | None = Field(
        default=None,
        description="ID of the configuration version"
    )
    is_speculative: bool = Field(
        description="Whether this is a speculative run"
    )
    organization_name: str = Field(
        description="Name of the organization"
    )
    payload_version: int = Field(
        description="Version of the payload format"
    )
    plan_json_api_url: str | None = Field(
        default=None,
        description="URL to access the plan JSON via API (post_plan, pre_apply, post_apply stages)"
    )
    run_app_url: str = Field(
        description="URL to view the run in TFC/TFE UI"
    )
    run_created_at: datetime = Field(
        description="Timestamp when the run was created"
    )
    run_created_by: str = Field(
        description="Username of the user who created the run"
    )
    run_id: str = Field(
        description="ID of the run"
    )
    run_message: str = Field(
        description="Message associated with the run"
    )
    stage: str = Field(
        description="Stage when the run task is executed (pre_plan, post_plan, pre_apply, post_apply)"
    )
    task_result_callback_url: str = Field(
        description="URL to send the task result callback to"
    )
    task_result_enforcement_level: str = Field(
        description="Enforcement level for the task result (advisory, mandatory)"
    )
    task_result_id: str = Field(
        description="ID of the task result"
    )
    vcs_branch: str | None = Field(
        default=None,
        description="VCS branch name"
    )
    vcs_commit_url: str | None = Field(
        default=None,
        description="URL to the VCS commit"
    )
    vcs_pull_request_url: str | None = Field(
        default=None,
        description="URL to the VCS pull request"
    )
    vcs_repo_url: str | None = Field(
        default=None,
        description="URL to the VCS repository"
    )
    workspace_app_url: str = Field(
        description="URL to view the workspace in TFC/TFE UI"
    )
    workspace_id: str = Field(
        description="ID of the workspace"
    )
    workspace_name: str = Field(
        description="Name of the workspace"
    )
    workspace_working_directory: str | None = Field(
        default=None,
        description="Working directory for the workspace"
    )

    model_config = ConfigDict(populate_by_name=True)
