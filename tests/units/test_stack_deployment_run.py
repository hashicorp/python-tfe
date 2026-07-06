# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""Unit tests for the stack_deployment_run module."""

from unittest.mock import Mock

import pytest

from pytfe._http import HTTPTransport
from pytfe.errors import (
    InvalidStackDeploymentGroupIDError,
    InvalidStackDeploymentRunIDError,
)
from pytfe.models.stack_deployment_group import StackDeploymentGroup
from pytfe.models.stack_deployment_run import (
    DeploymentRunStatus,
    StackDeploymentRun,
    StackDeploymentRunIncludeOpt,
    StackDeploymentRunListOptions,
    StackDeploymentRunReadOptions,
)
from pytfe.resources.stack_deployment_run import StackDeploymentRuns


class TestStackDeploymentRuns:
    """Test the StackDeploymentRuns service class."""

    @pytest.fixture
    def mock_transport(self):
        """Create a mock HTTPTransport."""
        return Mock(spec=HTTPTransport)

    @pytest.fixture
    def service(self, mock_transport):
        """Create a StackDeploymentRuns service with mocked transport."""
        return StackDeploymentRuns(mock_transport)

    @pytest.fixture
    def run_api_data(self):
        """Typical API response item for a single stack deployment run."""
        return {
            "id": "sdr-abc123",
            "type": "stack-deployment-runs",
            "attributes": {
                "status": "pre-deploying-pending-operator",
                "created-at": "2026-07-02T09:40:37.000Z",
                "updated-at": "2026-07-02T09:40:38.000Z",
            },
            "relationships": {
                "stack-deployment-group": {
                    "data": {"id": "sdg-xyz789", "type": "stack-deployment-groups"}
                }
            },
        }

    # ── Model tests ──────────────────────────────────────────────────────────

    def test_deployment_run_status_enum_values(self):
        """DeploymentRunStatus covers all wire values from go-tfe."""
        expected = {
            "pending",
            "pre-deploying",
            "pre-deploying-pending-operator",
            "acquiring-lock",
            "deploying",
            "deploying-pending-operator",
            "succeeded",
            "failed",
            "abandoned",
        }
        assert {s.value for s in DeploymentRunStatus} == expected

    def test_deployment_run_include_opt_values(self):
        """StackDeploymentRunIncludeOpt covers all valid include values from the API docs."""
        expected = {
            "stack_deployment_group",
            "stack_approval",
            "destroy_stack_configuration",
            "blocked_by_deployment_group",
            "latest_deployment_run_for_deployment",
        }
        assert {o.value for o in StackDeploymentRunIncludeOpt} == expected

    def test_deployment_run_parse(self, run_api_data):
        """StackDeploymentRun parses id and status from attributes."""
        attrs = dict(run_api_data["attributes"])
        attrs["id"] = run_api_data["id"]
        run = StackDeploymentRun.model_validate(attrs)
        assert run.id == "sdr-abc123"
        assert run.status == DeploymentRunStatus.PRE_DEPLOYING_PENDING_OPERATOR

    def test_list_options_serialization(self):
        """StackDeploymentRunListOptions serializes page[size] and include."""
        opts = StackDeploymentRunListOptions(
            page_size=25,
            include=[StackDeploymentRunIncludeOpt.STACK_DEPLOYMENT_GROUP],
        )
        dumped = opts.model_dump(by_alias=True, exclude_none=True)
        assert dumped["page[size]"] == 25

    # ── list() tests ─────────────────────────────────────────────────────────

    def test_list_invalid_group_id_raises(self, service):
        """list() with an empty group ID raises InvalidStackDeploymentGroupIDError."""
        with pytest.raises(InvalidStackDeploymentGroupIDError):
            list(service.list(""))

    def test_list_success(self, service, run_api_data):
        """list() yields StackDeploymentRun objects from paginated results."""
        service._list = Mock(return_value=[run_api_data])

        results = list(service.list("sdg-xyz789"))

        service._list.assert_called_once_with(
            path="/api/v2/stack-deployment-groups/sdg-xyz789/stack-deployment-runs",
            params={},
        )
        assert len(results) == 1
        assert isinstance(results[0], StackDeploymentRun)
        assert results[0].id == "sdr-abc123"

    def test_list_with_page_size_and_include(self, service, run_api_data):
        """list() passes page[size] and include params correctly."""
        service._list = Mock(return_value=[run_api_data])
        opts = StackDeploymentRunListOptions(
            page_size=10,
            include=[StackDeploymentRunIncludeOpt.STACK_DEPLOYMENT_GROUP],
        )
        list(service.list("sdg-xyz789", options=opts))
        service._list.assert_called_once_with(
            path="/api/v2/stack-deployment-groups/sdg-xyz789/stack-deployment-runs",
            params={"page[size]": 10, "include": "stack_deployment_group"},
        )

    def test_list_hydrates_group_relation(self, service, run_api_data):
        """list() hydrates the stack-deployment-group relation as a typed stub."""
        service._list = Mock(return_value=[run_api_data])
        results = list(service.list("sdg-xyz789"))
        assert isinstance(results[0].stack_deployment_group, StackDeploymentGroup)
        assert results[0].stack_deployment_group.id == "sdg-xyz789"

    def test_list_empty(self, service):
        """list() returns an empty iterator when the API returns no items."""
        service._list = Mock(return_value=[])
        assert list(service.list("sdg-xyz789")) == []

    # ── read() tests ─────────────────────────────────────────────────────────

    def test_read_invalid_id_raises(self, service):
        """read() with an empty ID raises InvalidStackDeploymentRunIDError."""
        with pytest.raises(InvalidStackDeploymentRunIDError):
            service.read("")

    def test_read_success(self, service, mock_transport, run_api_data):
        """read() fetches a single deployment run by ID."""
        mock_response = Mock()
        mock_response.json.return_value = {"data": run_api_data}
        mock_transport.request.return_value = mock_response

        run = service.read("sdr-abc123")

        mock_transport.request.assert_called_once_with(
            "GET", path="/api/v2/stack-deployment-runs/sdr-abc123", params={}
        )
        assert isinstance(run, StackDeploymentRun)
        assert run.id == "sdr-abc123"
        assert run.status == DeploymentRunStatus.PRE_DEPLOYING_PENDING_OPERATOR

    def test_read_with_include(self, service, mock_transport, run_api_data):
        """read() passes include= as a comma-separated query param."""
        mock_response = Mock()
        mock_response.json.return_value = {"data": run_api_data}
        mock_transport.request.return_value = mock_response

        opts = StackDeploymentRunReadOptions(
            include=[StackDeploymentRunIncludeOpt.STACK_DEPLOYMENT_GROUP]
        )
        service.read("sdr-abc123", options=opts)

        mock_transport.request.assert_called_once_with(
            "GET",
            path="/api/v2/stack-deployment-runs/sdr-abc123",
            params={"include": "stack_deployment_group"},
        )

    # ── approve_all_plans() tests ─────────────────────────────────────────────

    def test_approve_all_plans_invalid_id_raises(self, service):
        """approve_all_plans() with an empty ID raises InvalidStackDeploymentRunIDError."""
        with pytest.raises(InvalidStackDeploymentRunIDError):
            service.approve_all_plans("")

    def test_approve_all_plans_calls_correct_endpoint(self, service, mock_transport):
        """approve_all_plans() POSTs to the approve-all-plans action endpoint."""
        mock_transport.request.return_value = Mock()
        service.approve_all_plans("sdr-abc123")
        mock_transport.request.assert_called_once_with(
            "POST",
            path="/api/v2/stack-deployment-runs/sdr-abc123/approve-all-plans",
        )

    # ── cancel() tests ────────────────────────────────────────────────────────

    def test_cancel_invalid_id_raises(self, service):
        """cancel() with an empty ID raises InvalidStackDeploymentRunIDError."""
        with pytest.raises(InvalidStackDeploymentRunIDError):
            service.cancel("")

    def test_cancel_calls_correct_endpoint(self, service, mock_transport):
        """cancel() POSTs to the cancel action endpoint."""
        mock_transport.request.return_value = Mock()
        service.cancel("sdr-abc123")
        mock_transport.request.assert_called_once_with(
            "POST",
            path="/api/v2/stack-deployment-runs/sdr-abc123/cancel",
        )
