import pytest

from pytfe.client import TFEClient
from pytfe.errors import InvalidTaskStageIDError
from pytfe.models import Stage as ExportedStage
from pytfe.models.run_task import Stage as RunTaskStage
from pytfe.models.task_stage import (
    Stage,
    TaskStage,
    TaskStageStatus,
)
from pytfe.resources.task_stage import TaskStages

# Basic existence tests


def test_task_stage_service_exists():
    client = TFEClient()
    assert hasattr(client, "task_stages")


def test_task_stage_methods_exist():
    client = TFEClient()

    assert hasattr(client.task_stages, "read")
    assert hasattr(client.task_stages, "list")
    assert hasattr(client.task_stages, "override")


def test_task_stage_uses_canonical_stage_enum():
    assert Stage is RunTaskStage
    assert Stage is ExportedStage


# InvalidTaskStageIDError tests


def test_invalid_task_stage_id_error_is_raised():
    """InvalidTaskStageIDError should be raised for blank IDs."""
    client = TFEClient()

    with pytest.raises(InvalidTaskStageIDError):
        client.task_stages.read("")

    with pytest.raises(InvalidTaskStageIDError):
        client.task_stages.override("")


def test_invalid_task_stage_id_error_message():
    err = InvalidTaskStageIDError()
    assert "task stage" in str(err).lower()


# TaskStage optional fields / stub tests


def test_task_stage_stub_with_only_id():
    """TaskStage should be constructable with only `id` — all other fields optional."""
    ts = TaskStage(id="ts-stub-123")
    assert ts.id == "ts-stub-123"
    assert ts.stage is None
    assert ts.status is None
    assert ts.status_timestamps is None
    assert ts.created_at is None
    assert ts.updated_at is None
    assert ts.permissions is None
    assert ts.actions is None
    assert ts.run is None
    assert ts.task_results is None
    assert ts.policy_evaluations is None


def test_task_stage_partial_payload():
    """TaskStage should parse a payload with only some fields populated."""
    ts = TaskStage.model_validate(
        {"id": "ts-456", "stage": "pre_plan", "status": "pending"}
    )
    assert ts.id == "ts-456"
    assert ts.stage == Stage.PRE_PLAN
    assert ts.status == TaskStageStatus.pending
    assert ts.status_timestamps is None
    assert ts.created_at is None
    assert ts.run is None


def test_task_stage_full_payload():
    """TaskStage should parse a complete attributes payload."""
    ts = TaskStage.model_validate(
        {
            "id": "ts-789",
            "stage": "post_plan",
            "status": "passed",
            "status-timestamps": {"passed-at": "2024-06-01T12:00:00Z"},
            "created-at": "2024-01-01T00:00:00Z",
            "updated-at": "2024-06-01T12:00:00Z",
            "permissions": {"can-override": True},
            "actions": {"is-overridable": False},
        }
    )
    assert ts.stage == Stage.POST_PLAN
    assert ts.status == TaskStageStatus.passed
    assert ts.permissions is not None
    assert ts.permissions.can_override is True
    assert ts.actions is not None
    assert ts.actions.is_overridable is False


# Read method tests


def test_read_raises_error_when_id_missing():
    client = TFEClient()

    with pytest.raises(InvalidTaskStageIDError):
        client.task_stages.read("")


def test_read_calls_request_correctly(mocker):
    mock_transport = mocker.Mock()

    mock_response = mocker.Mock()
    mock_response.json.return_value = {
        "data": {
            "id": "ts-123",
            "attributes": {
                "stage": "pre_plan",
                "status": "pending",
                "status-timestamps": {},
                "created-at": "2024-01-01T00:00:00Z",
                "updated-at": "2024-01-01T00:00:00Z",
            },
        }
    }

    mock_transport.request.return_value = mock_response

    service = TaskStages(mock_transport)

    result = service.read("ts-123")

    assert isinstance(result, TaskStage)

    mock_transport.request.assert_called_once_with(
        "GET",
        "/api/v2/task-stages/ts-123",
    )


def test_read_stub_payload(mocker):
    """read() should succeed when API returns only an id (stub/relationship payload)."""
    mock_transport = mocker.Mock()
    mock_response = mocker.Mock()
    mock_response.json.return_value = {"data": {"id": "ts-stub-001", "attributes": {}}}
    mock_transport.request.return_value = mock_response

    service = TaskStages(mock_transport)
    result = service.read("ts-stub-001")

    assert isinstance(result, TaskStage)
    assert result.id == "ts-stub-001"
    assert result.stage is None


# List method tests


def test_list_with_valid_id_does_not_raise(mocker):
    mock_transport = mocker.Mock()

    service = TaskStages(mock_transport)

    service._list = mocker.Mock(return_value=[])

    result = list(service.list("run-123"))

    assert result == []


def test_list_calls_internal_list(mocker):
    mock_transport = mocker.Mock()

    service = TaskStages(mock_transport)

    service._list = mocker.Mock(
        return_value=[
            {
                "id": "ts-1",
                "attributes": {
                    "stage": "pre_plan",
                    "status": "pending",
                    "status-timestamps": {},
                    "created-at": "2024-01-01T00:00:00Z",
                    "updated-at": "2024-01-01T00:00:00Z",
                },
            }
        ]
    )

    result = list(service.list("run-123"))

    assert len(result) == 1
    assert isinstance(result[0], TaskStage)

    service._list.assert_called_once_with(
        "/api/v2/runs/run-123/task-stages", params=None
    )


# Override method tests


def test_override_raises_error_when_id_missing():
    client = TFEClient()

    with pytest.raises(InvalidTaskStageIDError):
        client.task_stages.override("")


def test_override_calls_request_without_comment(mocker):
    mock_transport = mocker.Mock()

    mock_response = mocker.Mock()
    mock_response.json.return_value = {
        "data": {
            "id": "ts-123",
            "attributes": {
                "stage": "pre_plan",
                "status": "pending",
                "status-timestamps": {},
                "created-at": "2024-01-01T00:00:00Z",
                "updated-at": "2024-01-01T00:00:00Z",
            },
        }
    }

    mock_transport.request.return_value = mock_response

    service = TaskStages(mock_transport)

    result = service.override("ts-123")

    assert isinstance(result, TaskStage)

    mock_transport.request.assert_called_once_with(
        "POST",
        "/api/v2/task-stages/ts-123/actions/override",
        json_body=None,
    )


def test_override_calls_request_with_comment(mocker):
    mock_transport = mocker.Mock()

    mock_response = mocker.Mock()
    mock_response.json.return_value = {
        "data": {
            "id": "ts-123",
            "attributes": {
                "stage": "pre_plan",
                "status": "pending",
                "status-timestamps": {},
                "created-at": "2024-01-01T00:00:00Z",
                "updated-at": "2024-01-01T00:00:00Z",
            },
        }
    }

    mock_transport.request.return_value = mock_response

    service = TaskStages(mock_transport)

    result = service.override("ts-123", comment="approved")

    assert isinstance(result, TaskStage)

    mock_transport.request.assert_called_once_with(
        "POST",
        "/api/v2/task-stages/ts-123/actions/override",
        json_body={"comment": "approved"},
    )


# Relationship parsing tests


def test_parse_task_stage_with_run_relationship(mocker):
    """_parse_task_stage should attach a Run stub from relationships."""
    mock_transport = mocker.Mock()
    service = TaskStages(mock_transport)

    data = {
        "id": "ts-rel-001",
        "attributes": {"stage": "pre_plan", "status": "running"},
        "relationships": {
            "run": {"data": {"id": "run-abc", "type": "runs"}},
            "task-results": {"data": []},
            "policy-evaluations": {"data": []},
        },
    }

    result = service._parse_task_stage(data)

    assert isinstance(result, TaskStage)
    assert result.run is not None
    assert result.run.id == "run-abc"
    assert result.task_results == []
    assert result.policy_evaluations == []


def test_parse_task_stage_with_task_results_relationship(mocker):
    """_parse_task_stage should parse task-results from relationships."""
    mock_transport = mocker.Mock()
    service = TaskStages(mock_transport)

    data = {
        "id": "ts-rel-002",
        "attributes": {},
        "relationships": {
            "task-results": {
                "data": [
                    {"id": "tr-1", "type": "task-results"},
                    {"id": "tr-2", "type": "task-results"},
                ]
            },
            "policy-evaluations": {"data": []},
        },
    }

    result = service._parse_task_stage(data)

    assert result.task_results is not None
    assert len(result.task_results) == 2
    assert result.task_results[0].id == "tr-1"
    assert result.task_results[1].id == "tr-2"


def test_parse_task_stage_with_no_relationships(mocker):
    """_parse_task_stage should handle missing relationships gracefully."""
    mock_transport = mocker.Mock()
    service = TaskStages(mock_transport)

    data = {
        "id": "ts-no-rel",
        "attributes": {},
    }

    result = service._parse_task_stage(data)

    assert isinstance(result, TaskStage)
    assert result.run is None
    assert result.task_results == []
    assert result.policy_evaluations == []
