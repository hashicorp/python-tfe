import pytest
from unittest.mock import Mock

from pytfe.resources.task_result import TaskResults
from pytfe.models.task_result import TaskResult


class TestTaskResults:
    @pytest.fixture
    def mock_transport(self):
        return Mock()

    @pytest.fixture
    def service(self, mock_transport):
        return TaskResults(mock_transport)

    def test_read_success(self, service, mock_transport):
        response = Mock()
        response.json.return_value = {
            "data": {
                "id": "tr-123",
                "attributes": {
                    "status": "passed",
                    "message": "ok",
                    "status-timestamps": {},
                    "url": "url",
                    "created-at": "2024-01-01T00:00:00Z",
                    "updated-at": "2024-01-01T00:00:00Z",
                    "task-id": "t1",
                    "task-name": "name",
                    "task-url": "url",
                    "workspace-task-id": "wt1",
                    "workspace-task-enforcement-level": "advisory",
                    "agent-pool-id": None,
                },
            }
        }
        mock_transport.request.return_value = response

        result = service.read("tr-123")

        assert isinstance(result, TaskResult)
        assert result.id == "tr-123"
        assert result.status == "passed"

    def test_invalid_id(self, service):
        with pytest.raises(ValueError):
            service.read("")

    def test_missing_data(self, service, mock_transport):
        response = Mock()
        response.json.return_value = {}

        mock_transport.request.return_value = response

        with pytest.raises(ValueError):
            service.read("tr-123")

    def test_missing_attributes(self, service, mock_transport):
        response = Mock()
        response.json.return_value = {
            "data": {"id": "tr-123"}
        }

        mock_transport.request.return_value = response

        result = service.read("tr-123")

        assert result.id == "tr-123"

    def test_optional_fields(self, service, mock_transport):
        response = Mock()
        response.json.return_value = {
            "data": {
                "id": "tr-123",
                "attributes": {
                    "status": "passed",
                    "message": None,
                },
            }
        }

        mock_transport.request.return_value = response

        result = service.read("tr-123")

        assert result.message is None

    def test_status_enum(self, service, mock_transport):
        response = Mock()
        response.json.return_value = {
            "data": {
                "id": "tr-123",
                "attributes": {
                    "status": "failed",
                    "message": "fail",
                },
            }
        }

        mock_transport.request.return_value = response

        result = service.read("tr-123")

        assert result.status == "failed"

    def test_timestamps_parsing(self, service, mock_transport):
        response = Mock()
        response.json.return_value = {
            "data": {
                "id": "tr-123",
                "attributes": {
                    "status": "passed",
                    "message": "ok",
                    "status-timestamps": {
                        "passed-at": "2024-01-01T00:00:00Z"
                    },
                },
            }
        }

        mock_transport.request.return_value = response

        result = service.read("tr-123")

        assert result.status_timestamps is not None