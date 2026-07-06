# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""Unit tests for the stack_deployment_steps module."""

from unittest.mock import Mock

import pytest

from pytfe._http import HTTPTransport
from pytfe.errors import (
    InvalidStackDeploymentRunIDError,
    InvalidStackDeploymentStepIDError,
)
from pytfe.models.stack_deployment_run import StackDeploymentRun
from pytfe.models.stack_deployment_step import (
    DeploymentStepStatus,
    StackDeploymentStep,
    StackDeploymentStepArtifactType,
    StackDeploymentStepIncludeOpt,
    StackDeploymentStepListOptions,
    StackDeploymentStepReadOptions,
    StackDiagnostic,
    StackDiagnosticListOptions,
)
from pytfe.resources.stack_deployment_steps import StackDeploymentSteps


class TestStackDeploymentSteps:
    """Test the StackDeploymentSteps service class."""

    @pytest.fixture
    def mock_transport(self):
        """Create a mock HTTPTransport."""
        return Mock(spec=HTTPTransport)

    @pytest.fixture
    def service(self, mock_transport):
        """Create a StackDeploymentSteps service with mocked transport."""
        return StackDeploymentSteps(mock_transport)

    @pytest.fixture
    def step_api_data(self):
        """Typical API response item for a single stack deployment step."""
        return {
            "id": "sds-abc123",
            "type": "stack-deployment-steps",
            "attributes": {
                "status": "pending-operator",
                "operation-type": "plan",
                "created-at": "2026-07-02T09:40:37.000Z",
                "updated-at": "2026-07-02T09:40:38.000Z",
            },
            "relationships": {
                "stack-deployment-run": {
                    "data": {"id": "sdr-xyz789", "type": "stack-deployment-runs"}
                }
            },
        }

    @pytest.fixture
    def diag_api_data(self):
        """Typical API response item for a single stack diagnostic."""
        return {
            "id": "std-diag001",
            "type": "stack-diagnostics",
            "attributes": {
                "severity": "warning",
                "summary": "Resource will be re-created",
                "detail": "The resource will be destroyed and then re-created.",
                "diags": None,
                "acknowledged": False,
                "acknowledged-at": None,
                "created-at": "2026-07-02T09:40:37.000Z",
            },
        }

    # ── Model tests ──────────────────────────────────────────────────────────

    def test_deployment_step_status_enum_values(self):
        """DeploymentStepStatus covers all wire values from go-tfe."""
        expected = {
            "blocked",
            "abandoned",
            "queued",
            "running",
            "pending-operator",
            "completed",
            "failed",
        }
        assert {s.value for s in DeploymentStepStatus} == expected

    def test_artifact_type_enum_values(self):
        """StackDeploymentStepArtifactType covers all artifact types from go-tfe."""
        expected = {
            "plan-description",
            "apply-description",
            "plan-debug-log",
            "apply-debug-log",
        }
        assert {a.value for a in StackDeploymentStepArtifactType} == expected

    def test_step_parse(self, step_api_data):
        """StackDeploymentStep parses id, status, and operation_type."""
        attrs = dict(step_api_data["attributes"])
        attrs["id"] = step_api_data["id"]
        step = StackDeploymentStep.model_validate(attrs)
        assert step.id == "sds-abc123"
        assert step.status == DeploymentStepStatus.PENDING_OPERATOR
        assert step.operation_type == "plan"

    def test_list_options_serialization(self):
        """StackDeploymentStepListOptions serializes page[size] and include."""
        opts = StackDeploymentStepListOptions(
            page_size=25,
            include=[StackDeploymentStepIncludeOpt.STACK_APPROVAL],
        )
        dumped = opts.model_dump(by_alias=True, exclude_none=True)
        assert dumped["page[size]"] == 25

    def test_diagnostic_list_options_serialization(self):
        """StackDiagnosticListOptions serializes page[size]."""
        opts = StackDiagnosticListOptions(page_size=10)
        dumped = opts.model_dump(by_alias=True, exclude_none=True)
        assert dumped["page[size]"] == 10

    # ── list() tests ─────────────────────────────────────────────────────────

    def test_list_invalid_run_id_raises(self, service):
        """list() with an empty run ID raises InvalidStackDeploymentRunIDError."""
        with pytest.raises(InvalidStackDeploymentRunIDError):
            list(service.list(""))

    def test_list_success(self, service, step_api_data):
        """list() yields StackDeploymentStep objects from paginated results."""
        service._list = Mock(return_value=[step_api_data])

        results = list(service.list("sdr-xyz789"))

        service._list.assert_called_once_with(
            path="/api/v2/stack-deployment-runs/sdr-xyz789/stack-deployment-steps",
            params={},
        )
        assert len(results) == 1
        assert isinstance(results[0], StackDeploymentStep)
        assert results[0].id == "sds-abc123"

    def test_list_with_page_size_and_include(self, service, step_api_data):
        """list() passes page[size] and include params correctly."""
        service._list = Mock(return_value=[step_api_data])
        opts = StackDeploymentStepListOptions(
            page_size=10,
            include=[StackDeploymentStepIncludeOpt.STACK_APPROVAL],
        )
        list(service.list("sdr-xyz789", options=opts))
        service._list.assert_called_once_with(
            path="/api/v2/stack-deployment-runs/sdr-xyz789/stack-deployment-steps",
            params={"page[size]": 10, "include": "stack_approval"},
        )

    def test_list_hydrates_run_relation(self, service, step_api_data):
        """list() hydrates the stack-deployment-run relation as a typed stub."""
        service._list = Mock(return_value=[step_api_data])
        results = list(service.list("sdr-xyz789"))
        assert isinstance(results[0].stack_deployment_run, StackDeploymentRun)
        assert results[0].stack_deployment_run.id == "sdr-xyz789"

    def test_list_empty(self, service):
        """list() returns an empty iterator when the API returns no items."""
        service._list = Mock(return_value=[])
        assert list(service.list("sdr-xyz789")) == []

    # ── read() tests ─────────────────────────────────────────────────────────

    def test_read_invalid_id_raises(self, service):
        """read() with an empty ID raises InvalidStackDeploymentStepIDError."""
        with pytest.raises(InvalidStackDeploymentStepIDError):
            service.read("")

    def test_read_success(self, service, mock_transport, step_api_data):
        """read() fetches a single deployment step by ID."""
        mock_response = Mock()
        mock_response.json.return_value = {"data": step_api_data}
        mock_transport.request.return_value = mock_response

        step = service.read("sds-abc123")

        mock_transport.request.assert_called_once_with(
            "GET", path="/api/v2/stack-deployment-steps/sds-abc123", params={}
        )
        assert isinstance(step, StackDeploymentStep)
        assert step.id == "sds-abc123"
        assert step.status == DeploymentStepStatus.PENDING_OPERATOR

    def test_read_with_include(self, service, mock_transport, step_api_data):
        """read() passes include= as a comma-separated query param."""
        mock_response = Mock()
        mock_response.json.return_value = {"data": step_api_data}
        mock_transport.request.return_value = mock_response

        opts = StackDeploymentStepReadOptions(
            include=[StackDeploymentStepIncludeOpt.STACK_APPROVAL]
        )
        service.read("sds-abc123", options=opts)

        mock_transport.request.assert_called_once_with(
            "GET",
            path="/api/v2/stack-deployment-steps/sds-abc123",
            params={"include": "stack_approval"},
        )

    # ── advance() tests ───────────────────────────────────────────────────────

    def test_advance_invalid_id_raises(self, service):
        """advance() with an empty ID raises InvalidStackDeploymentStepIDError."""
        with pytest.raises(InvalidStackDeploymentStepIDError):
            service.advance("")

    def test_advance_calls_correct_endpoint(self, service, mock_transport):
        """advance() POSTs to the advance action endpoint."""
        mock_transport.request.return_value = Mock()
        service.advance("sds-abc123")
        mock_transport.request.assert_called_once_with(
            "POST",
            path="/api/v2/stack-deployment-steps/sds-abc123/advance",
        )

    # ── list_diagnostics() tests ──────────────────────────────────────────────

    def test_list_diagnostics_invalid_id_raises(self, service):
        """list_diagnostics() with an empty ID raises InvalidStackDeploymentStepIDError."""
        with pytest.raises(InvalidStackDeploymentStepIDError):
            list(service.list_diagnostics(""))

    def test_list_diagnostics_success(self, service, diag_api_data):
        """list_diagnostics() yields StackDiagnostic objects."""
        service._list = Mock(return_value=[diag_api_data])

        results = list(service.list_diagnostics("sds-abc123"))

        service._list.assert_called_once_with(
            path="/api/v2/stack-deployment-steps/sds-abc123/stack-diagnostics",
            params={},
        )
        assert len(results) == 1
        assert isinstance(results[0], StackDiagnostic)
        assert results[0].id == "std-diag001"
        assert results[0].severity == "warning"

    def test_list_diagnostics_with_page_size(self, service, diag_api_data):
        """list_diagnostics() passes page[size] param."""
        service._list = Mock(return_value=[diag_api_data])
        opts = StackDiagnosticListOptions(page_size=5)
        list(service.list_diagnostics("sds-abc123", options=opts))
        service._list.assert_called_once_with(
            path="/api/v2/stack-deployment-steps/sds-abc123/stack-diagnostics",
            params={"page[size]": 5},
        )

    def test_list_diagnostics_empty(self, service):
        """list_diagnostics() returns an empty iterator when no diagnostics."""
        service._list = Mock(return_value=[])
        assert list(service.list_diagnostics("sds-abc123")) == []

    # ── download_artifact() tests ─────────────────────────────────────────────

    def test_download_artifact_invalid_id_raises(self, service):
        """download_artifact() with an empty ID raises InvalidStackDeploymentStepIDError."""
        with pytest.raises(InvalidStackDeploymentStepIDError):
            service.download_artifact(
                "", StackDeploymentStepArtifactType.PLAN_DESCRIPTION
            )

    def test_download_artifact_returns_bytes(self, service, mock_transport):
        """download_artifact() returns the raw response bytes."""
        mock_response = Mock()
        mock_response.content = b"# Plan output\nchange: 1 to add"
        mock_transport.request.return_value = mock_response

        result = service.download_artifact(
            "sds-abc123", StackDeploymentStepArtifactType.PLAN_DESCRIPTION
        )

        mock_transport.request.assert_called_once_with(
            "GET",
            path="/api/v2/stack-deployment-steps/sds-abc123/artifacts",
            params={"name": "plan-description"},
        )
        assert result == b"# Plan output\nchange: 1 to add"

    def test_download_artifact_apply_description(self, service, mock_transport):
        """download_artifact() uses the correct artifact type name for apply-description."""
        mock_response = Mock()
        mock_response.content = b"apply output"
        mock_transport.request.return_value = mock_response

        service.download_artifact(
            "sds-abc123", StackDeploymentStepArtifactType.APPLY_DESCRIPTION
        )

        mock_transport.request.assert_called_once_with(
            "GET",
            path="/api/v2/stack-deployment-steps/sds-abc123/artifacts",
            params={"name": "apply-description"},
        )
