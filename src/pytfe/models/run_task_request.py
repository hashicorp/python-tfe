# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class RunTaskRequestCapabilities(BaseModel):
    """Defines the capabilities that the caller supports."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    outcomes: bool = Field(..., description="Whether the caller supports outcomes")


class RunTaskRequest(BaseModel):
    """Payload object that TFC/E sends to the Run Task's URL.

    https://developer.hashicorp.com/terraform/enterprise/api-docs/run-tasks/run-tasks-integration#common-properties
    """

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    access_token: str = Field(
        ..., alias="access_token", description="The access token for the run task"
    )
    capabilities: RunTaskRequestCapabilities = Field(
        default_factory=lambda: RunTaskRequestCapabilities(outcomes=False),
        alias="capabilities",
        description="The capabilities that the caller supports",
    )
    configuration_version_download_url: str | None = Field(
        None,
        alias="configuration_version_download_url",
        description="The URL to download the configuration version",
    )
    configuration_version_id: str | None = Field(
        None,
        alias="configuration_version_id",
        description="The ID of the configuration version",
    )
    is_speculative: bool = Field(
        ..., alias="is_speculative", description="Whether the run is speculative"
    )
    organization_name: str = Field(
        ..., alias="organization_name", description="The name of the organization"
    )
    payload_version: int = Field(
        ..., alias="payload_version", description="The version of the payload format"
    )
    plan_json_api_url: str | None = Field(
        None,
        alias="plan_json_api_url",
        description="URL to the plan JSON API (specific to post_plan, pre_apply or post_apply stage)",
    )
    run_app_url: str = Field(
        ..., alias="run_app_url", description="The URL to the run in the TFC/E UI"
    )
    run_created_at: datetime = Field(
        ..., alias="run_created_at", description="The time the run was created"
    )
    run_created_by: str = Field(
        ..., alias="run_created_by", description="The user who created the run"
    )
    run_id: str = Field(..., alias="run_id", description="The ID of the run")
    run_message: str = Field(
        ..., alias="run_message", description="The message associated with the run"
    )
    stage: str = Field(..., alias="stage", description="The stage of the run task")
    task_result_callback_url: str = Field(
        ...,
        alias="task_result_callback_url",
        description="The URL to call with the task result",
    )
    task_result_enforcement_level: str = Field(
        ...,
        alias="task_result_enforcement_level",
        description="The enforcement level of the task result",
    )
    task_result_id: str = Field(
        ..., alias="task_result_id", description="The ID of the task result"
    )
    vcs_branch: str | None = Field(
        None, alias="vcs_branch", description="The VCS branch associated with the run"
    )
    vcs_commit_url: str | None = Field(
        None,
        alias="vcs_commit_url",
        description="The URL of the VCS commit associated with the run",
    )
    vcs_pull_request_url: str | None = Field(
        None,
        alias="vcs_pull_request_url",
        description="The URL of the VCS pull request associated with the run",
    )
    vcs_repo_url: str | None = Field(
        None,
        alias="vcs_repo_url",
        description="The URL of the VCS repository associated with the run",
    )
    workspace_app_url: str = Field(
        ...,
        alias="workspace_app_url",
        description="The URL to the workspace in the TFC/E UI",
    )
    workspace_id: str = Field(
        ..., alias="workspace_id", description="The ID of the workspace"
    )
    workspace_name: str = Field(
        ..., alias="workspace_name", description="The name of the workspace"
    )
    workspace_working_directory: str | None = Field(
        None,
        alias="workspace_working_directory",
        description="The working directory configured for the workspace",
    )
