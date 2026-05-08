import pytest

from pytfe.client import TFEClient
from pytfe.models.task_stage import TaskStage
from pytfe.resources.task_stage import TaskStages

# ---------------------------
# Basic existence tests
# ---------------------------


def test_task_stage_service_exists():
    client = TFEClient()
    assert hasattr(client, "task_stages")


def test_task_stage_methods_exist():
    client = TFEClient()

    assert hasattr(client.task_stages, "read")
    assert hasattr(client.task_stages, "list")
    assert hasattr(client.task_stages, "override")


# ---------------------------
# Read method tests
# ---------------------------


def test_read_raises_error_when_id_missing():
    client = TFEClient()

    with pytest.raises(ValueError):
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


# ---------------------------
# List method tests
# ---------------------------


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

    service._list.assert_called_once_with("/api/v2/runs/run-123/task-stages")


# ---------------------------
# Override method tests
# ---------------------------


def test_override_raises_error_when_id_missing():
    client = TFEClient()

    with pytest.raises(ValueError):
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
