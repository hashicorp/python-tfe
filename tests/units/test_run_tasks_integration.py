"""Unit tests for Run Tasks Integration."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from pytfe.client import TFEClient
from pytfe.errors import TFEError
from pytfe.models.run_task_request import RunTaskRequest, RunTaskRequestCapabilities
from pytfe.resources.run_tasks_integration import (
    RunTasksIntegration,
    TaskResultCallbackOptions,
    TaskResultOutcome,
    TaskResultStatus,
    TaskResultTag,
)


class TestRunTaskRequest:
    """Tests for RunTaskRequest model."""

    def test_run_task_request_minimal(self):
        """Test parsing minimal run task request."""
        data = {
            "access_token": "test-token-123",
            "is_speculative": False,
            "organization_name": "my-org",
            "payload_version": 1,
            "run_app_url": "https://app.terraform.io/app/my-org/my-workspace/runs/run-123",
            "run_created_at": "2025-12-22T10:00:00Z",
            "run_created_by": "user@example.com",
            "run_id": "run-123",
            "run_message": "Test run",
            "stage": "post_plan",
            "task_result_callback_url": "https://app.terraform.io/api/v2/task-results/tr-123/callback",
            "task_result_enforcement_level": "mandatory",
            "task_result_id": "tr-123",
            "workspace_app_url": "https://app.terraform.io/app/my-org/my-workspace",
            "workspace_id": "ws-123",
            "workspace_name": "my-workspace",
        }
        
        request = RunTaskRequest(**data)
        
        assert request.access_token == "test-token-123"
        assert request.organization_name == "my-org"
        assert request.run_id == "run-123"
        assert request.stage == "post_plan"
        assert request.task_result_callback_url == "https://app.terraform.io/api/v2/task-results/tr-123/callback"

    def test_run_task_request_complete(self):
        """Test parsing complete run task request with all fields."""
        data = {
            "access_token": "test-token-456",
            "capabilities": {"outcomes": True},
            "configuration_version_download_url": "https://app.terraform.io/api/v2/configuration-versions/cv-123/download",
            "configuration_version_id": "cv-123",
            "is_speculative": True,
            "organization_name": "test-org",
            "payload_version": 1,
            "plan_json_api_url": "https://app.terraform.io/api/v2/plans/plan-123/json-output",
            "run_app_url": "https://app.terraform.io/app/test-org/test-workspace/runs/run-456",
            "run_created_at": "2025-12-22T11:30:00Z",
            "run_created_by": "admin@example.com",
            "run_id": "run-456",
            "run_message": "Test with VCS",
            "stage": "pre_plan",
            "task_result_callback_url": "https://app.terraform.io/api/v2/task-results/tr-456/callback",
            "task_result_enforcement_level": "advisory",
            "task_result_id": "tr-456",
            "vcs_branch": "main",
            "vcs_commit_url": "https://github.com/org/repo/commit/abc123",
            "vcs_pull_request_url": "https://github.com/org/repo/pull/42",
            "vcs_repo_url": "https://github.com/org/repo",
            "workspace_app_url": "https://app.terraform.io/app/test-org/test-workspace",
            "workspace_id": "ws-456",
            "workspace_name": "test-workspace",
            "workspace_working_directory": "terraform/",
        }
        
        request = RunTaskRequest(**data)
        
        assert request.access_token == "test-token-456"
        assert request.capabilities is not None
        assert request.capabilities.outcomes is True
        assert request.configuration_version_id == "cv-123"
        assert request.vcs_branch == "main"
        assert request.vcs_commit_url == "https://github.com/org/repo/commit/abc123"
        assert request.workspace_working_directory == "terraform/"


class TestTaskResultTag:
    """Tests for TaskResultTag."""

    def test_tag_with_level(self):
        """Test tag with level."""
        tag = TaskResultTag(label="High", level="error")
        data = tag.to_dict()
        
        assert data["label"] == "High"
        assert data["level"] == "error"

    def test_tag_without_level(self):
        """Test tag without level."""
        tag = TaskResultTag(label="Passed")
        data = tag.to_dict()
        
        assert data["label"] == "Passed"
        assert "level" not in data


class TestTaskResultOutcome:
    """Tests for TaskResultOutcome."""

    def test_outcome_complete(self):
        """Test complete outcome with all fields."""
        tags = {
            "Status": [TaskResultTag(label="Failed", level="error")],
            "Severity": [TaskResultTag(label="High", level="error")],
        }
        
        outcome = TaskResultOutcome(
            outcome_id="ISSUE-123",
            description="Security issue found",
            body="# Details\n\nSecurity vulnerability detected.",
            url="https://example.com/issues/123",
            tags=tags,
        )
        
        data = outcome.to_dict()
        
        assert data["type"] == "task-result-outcomes"
        assert data["attributes"]["outcome-id"] == "ISSUE-123"
        assert data["attributes"]["description"] == "Security issue found"
        assert data["attributes"]["body"] == "# Details\n\nSecurity vulnerability detected."
        assert data["attributes"]["url"] == "https://example.com/issues/123"
        assert "Status" in data["attributes"]["tags"]

    def test_outcome_minimal(self):
        """Test minimal outcome."""
        outcome = TaskResultOutcome()
        data = outcome.to_dict()
        
        assert data["type"] == "task-result-outcomes"
        assert "attributes" in data


class TestTaskResultCallbackOptions:
    """Tests for TaskResultCallbackOptions."""

    def test_callback_options_passed(self):
        """Test callback options with passed status."""
        options = TaskResultCallbackOptions(
            status=TaskResultStatus.PASSED,
            message="All checks passed",
            url="https://example.com/results/123",
        )
        
        options.validate()
        data = options.to_dict()
        
        assert data["data"]["type"] == "task-results"
        assert data["data"]["attributes"]["status"] == "passed"
        assert data["data"]["attributes"]["message"] == "All checks passed"
        assert data["data"]["attributes"]["url"] == "https://example.com/results/123"

    def test_callback_options_with_outcomes(self):
        """Test callback options with outcomes."""
        outcome = TaskResultOutcome(
            outcome_id="ISSUE-1",
            description="Test issue",
        )
        
        options = TaskResultCallbackOptions(
            status=TaskResultStatus.FAILED,
            message="1 issue found",
            outcomes=[outcome],
        )
        
        data = options.to_dict()
        
        assert "relationships" in data["data"]
        assert "outcomes" in data["data"]["relationships"]
        assert len(data["data"]["relationships"]["outcomes"]["data"]) == 1

    def test_validate_invalid_status(self):
        """Test validation fails with invalid status."""
        options = TaskResultCallbackOptions(status="invalid")
        
        with pytest.raises(TFEError) as exc_info:
            options.validate()
        
        assert "Invalid task result status" in str(exc_info.value)

    def test_validate_valid_statuses(self):
        """Test validation passes with all valid statuses."""
        for status in [TaskResultStatus.PASSED, TaskResultStatus.FAILED, TaskResultStatus.RUNNING]:
            options = TaskResultCallbackOptions(status=status)
            options.validate()  # Should not raise


class TestRunTasksIntegration:
    """Tests for RunTasksIntegration service."""

    def test_callback_success(self):
        """Test successful callback."""
        mock_transport = MagicMock()
        integration = RunTasksIntegration(mock_transport)
        
        options = TaskResultCallbackOptions(
            status=TaskResultStatus.PASSED,
            message="All tests passed",
        )
        
        integration.callback(
            callback_url="https://app.terraform.io/api/v2/task-results/tr-123/callback",
            access_token="test-token-123",
            options=options,
        )
        
        # Verify request was made
        mock_transport.request.assert_called_once()
        call_args = mock_transport.request.call_args
        
        assert call_args[0][0] == "PATCH"
        assert call_args[0][1] == "https://app.terraform.io/api/v2/task-results/tr-123/callback"
        assert "Authorization" in call_args[1]["headers"]
        assert call_args[1]["headers"]["Authorization"] == "Bearer test-token-123"

    def test_callback_empty_url(self):
        """Test callback fails with empty URL."""
        mock_transport = MagicMock()
        integration = RunTasksIntegration(mock_transport)
        
        options = TaskResultCallbackOptions(status=TaskResultStatus.PASSED)
        
        with pytest.raises(TFEError) as exc_info:
            integration.callback(
                callback_url="",
                access_token="test-token",
                options=options,
            )
        
        assert "callback_url cannot be empty" in str(exc_info.value)

    def test_callback_empty_token(self):
        """Test callback fails with empty token."""
        mock_transport = MagicMock()
        integration = RunTasksIntegration(mock_transport)
        
        options = TaskResultCallbackOptions(status=TaskResultStatus.PASSED)
        
        with pytest.raises(TFEError) as exc_info:
            integration.callback(
                callback_url="https://example.com/callback",
                access_token="",
                options=options,
            )
        
        assert "access_token cannot be empty" in str(exc_info.value)

    def test_callback_invalid_status(self):
        """Test callback fails with invalid status."""
        mock_transport = MagicMock()
        integration = RunTasksIntegration(mock_transport)
        
        options = TaskResultCallbackOptions(status="invalid-status")
        
        with pytest.raises(TFEError) as exc_info:
            integration.callback(
                callback_url="https://example.com/callback",
                access_token="test-token",
                options=options,
            )
        
        assert "Invalid task result status" in str(exc_info.value)

    def test_callback_with_outcomes(self):
        """Test callback with detailed outcomes."""
        mock_transport = MagicMock()
        integration = RunTasksIntegration(mock_transport)
        
        outcome = TaskResultOutcome(
            outcome_id="CHECK-1",
            description="Policy violation",
            body="## Issue\n\nPolicy check failed.",
            url="https://example.com/check-1",
            tags={
                "Severity": [TaskResultTag(label="High", level="error")],
            },
        )
        
        options = TaskResultCallbackOptions(
            status=TaskResultStatus.FAILED,
            message="Policy check failed",
            url="https://example.com/results",
            outcomes=[outcome],
        )
        
        integration.callback(
            callback_url="https://app.terraform.io/api/v2/task-results/tr-123/callback",
            access_token="test-token-123",
            options=options,
        )
        
        call_args = mock_transport.request.call_args
        body = call_args[1]["json_body"]
        
        assert "relationships" in body["data"]
        assert "outcomes" in body["data"]["relationships"]
