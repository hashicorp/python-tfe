"""Unit tests for run task webhook request models."""

from pytfe.models import RunTaskRequest, RunTaskRequestCapabilities


def _run_task_request_payload() -> dict:
    return {
        "access_token": "token",
        "configuration_version_download_url": "https://example.com/cv",
        "configuration_version_id": "cv-123",
        "is_speculative": False,
        "organization_name": "example-org",
        "payload_version": 1,
        "plan_json_api_url": "https://example.com/plan-json",
        "run_app_url": "https://example.com/run",
        "run_created_at": "2024-01-01T00:00:00Z",
        "run_created_by": "user-123",
        "run_id": "run-123",
        "run_message": "Queued manually",
        "stage": "post_plan",
        "task_result_callback_url": "https://example.com/callback",
        "task_result_enforcement_level": "mandatory",
        "task_result_id": "taskrs-123",
        "workspace_app_url": "https://example.com/workspace",
        "workspace_id": "ws-123",
        "workspace_name": "example-workspace",
    }


def test_run_task_request_parses_capabilities_from_live_payload():
    payload = _run_task_request_payload()
    payload["capabilities"] = {"outcomes": True}

    request = RunTaskRequest.model_validate(payload)

    assert isinstance(request.capabilities, RunTaskRequestCapabilities)
    assert request.capabilities.outcomes is True
    dumped = request.model_dump(by_alias=True)
    assert dumped["capabilities"] == {"outcomes": True}
    assert "capabilitites" not in dumped
