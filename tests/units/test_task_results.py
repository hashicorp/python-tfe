from unittest.mock import Mock

import pytest

from pytfe.models.policy_evaluation import PolicyEvaluation
from pytfe.models.run import Run
from pytfe.models.task_result import TaskResult
from pytfe.models.task_stage import TaskStage
from pytfe.models.workspace import Workspace
from pytfe.resources.task_result import TaskResults


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
        response.json.return_value = {"data": {"id": "tr-123"}}

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
                    "status-timestamps": {"passed-at": "2024-01-01T00:00:00Z"},
                },
            }
        }

        mock_transport.request.return_value = response

        result = service.read("tr-123")

        assert result.status_timestamps is not None

    # ── Relationship mapping tests ─────────────────────────────────────────────

    def test_task_stage_relationship_mapped(self, service, mock_transport):
        response = Mock()
        response.json.return_value = {
            "data": {
                "id": "tr-123",
                "attributes": {"status": "passed"},
                "relationships": {
                    "task-stage": {"data": {"id": "ts-456", "type": "task-stages"}}
                },
            }
        }
        mock_transport.request.return_value = response

        result = service.read("tr-123")

        assert isinstance(result.task_stage, TaskStage)
        assert result.task_stage.id == "ts-456"

    def test_task_stage_relationship_null(self, service, mock_transport):
        response = Mock()
        response.json.return_value = {
            "data": {
                "id": "tr-123",
                "attributes": {"status": "passed"},
                "relationships": {"task-stage": {"data": None}},
            }
        }
        mock_transport.request.return_value = response

        result = service.read("tr-123")

        assert result.task_stage is None

    def test_run_relationship_mapped(self, service, mock_transport):
        response = Mock()
        response.json.return_value = {
            "data": {
                "id": "tr-123",
                "attributes": {"status": "passed"},
                "relationships": {"run": {"data": {"id": "run-789", "type": "runs"}}},
            }
        }
        mock_transport.request.return_value = response

        result = service.read("tr-123")

        assert isinstance(result.run, Run)
        assert result.run.id == "run-789"

    def test_run_relationship_null(self, service, mock_transport):
        response = Mock()
        response.json.return_value = {
            "data": {
                "id": "tr-123",
                "attributes": {"status": "passed"},
                "relationships": {"run": {"data": None}},
            }
        }
        mock_transport.request.return_value = response

        result = service.read("tr-123")

        assert result.run is None

    def test_workspace_relationship_mapped(self, service, mock_transport):
        response = Mock()
        response.json.return_value = {
            "data": {
                "id": "tr-123",
                "attributes": {"status": "passed"},
                "relationships": {
                    "workspace": {"data": {"id": "ws-abc", "type": "workspaces"}}
                },
            }
        }
        mock_transport.request.return_value = response

        result = service.read("tr-123")

        assert isinstance(result.workspace, Workspace)
        assert result.workspace.id == "ws-abc"

    def test_workspace_relationship_null(self, service, mock_transport):
        response = Mock()
        response.json.return_value = {
            "data": {
                "id": "tr-123",
                "attributes": {"status": "passed"},
                "relationships": {"workspace": {"data": None}},
            }
        }
        mock_transport.request.return_value = response

        result = service.read("tr-123")

        assert result.workspace is None

    def test_policy_evaluations_relationship_mapped(self, service, mock_transport):
        response = Mock()
        response.json.return_value = {
            "data": {
                "id": "tr-123",
                "attributes": {"status": "passed"},
                "relationships": {
                    "policy-evaluations": {
                        "data": [
                            {"id": "pe-001", "type": "policy-evaluations"},
                            {"id": "pe-002", "type": "policy-evaluations"},
                        ]
                    }
                },
            }
        }
        mock_transport.request.return_value = response

        result = service.read("tr-123")

        assert isinstance(result.policy_evaluations, list)
        assert len(result.policy_evaluations) == 2
        assert all(isinstance(pe, PolicyEvaluation) for pe in result.policy_evaluations)
        assert result.policy_evaluations[0].id == "pe-001"
        assert result.policy_evaluations[1].id == "pe-002"

    def test_policy_evaluations_relationship_empty(self, service, mock_transport):
        response = Mock()
        response.json.return_value = {
            "data": {
                "id": "tr-123",
                "attributes": {"status": "passed"},
                "relationships": {"policy-evaluations": {"data": []}},
            }
        }
        mock_transport.request.return_value = response

        result = service.read("tr-123")

        assert result.policy_evaluations == []

    def test_no_relationships_key(self, service, mock_transport):
        """When 'relationships' is absent, all relationship fields stay None."""
        response = Mock()
        response.json.return_value = {
            "data": {
                "id": "tr-123",
                "attributes": {"status": "passed"},
            }
        }
        mock_transport.request.return_value = response

        result = service.read("tr-123")

        assert result.task_stage is None
        assert result.run is None
        assert result.workspace is None
        assert result.policy_evaluations == []
