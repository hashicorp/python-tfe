# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""Unit tests for the stack_deployment_group module."""

from unittest.mock import Mock

import pytest

from pytfe._http import HTTPTransport
from pytfe.errors import (
    InvalidStackConfigurationIDError,
    InvalidStackDeploymentGroupIDError,
)
from pytfe.models.stack_configuration import StackConfiguration
from pytfe.models.stack_deployment_group import (
    DeploymentGroupStatus,
    StackDeploymentGroup,
    StackDeploymentGroupListOptions,
    StackDeploymentGroupRerunOptions,
)
from pytfe.resources.stack_deployment_group import StackDeploymentGroups


class TestStackDeploymentGroups:
    """Test the StackDeploymentGroups service class."""

    @pytest.fixture
    def mock_transport(self):
        """Create a mock HTTPTransport."""
        return Mock(spec=HTTPTransport)

    @pytest.fixture
    def service(self, mock_transport):
        """Create a StackDeploymentGroups service with mocked transport."""
        return StackDeploymentGroups(mock_transport)

    @pytest.fixture
    def group_api_data(self):
        """Typical API response item for a single stack deployment group."""
        return {
            "id": "sdg-xyz789",
            "type": "stack-deployment-groups",
            "attributes": {
                "name": "dev",
                "status": "deploying",
                "created-at": "2026-07-02T09:40:00.000Z",
                "updated-at": "2026-07-02T09:41:00.000Z",
            },
            "relationships": {
                "stack-configuration": {
                    "data": {"id": "stc-abc123", "type": "stack-configurations"}
                }
            },
        }

    # ── Model tests ──────────────────────────────────────────────────────────

    def test_deployment_group_status_enum_values(self):
        """DeploymentGroupStatus covers all wire values from go-tfe."""
        expected = {"pending", "deploying", "succeeded", "failed", "abandoned"}
        assert {s.value for s in DeploymentGroupStatus} == expected

    def test_deployment_group_parse(self, group_api_data):
        """StackDeploymentGroup parses id, name, and status from attributes."""
        attrs = dict(group_api_data["attributes"])
        attrs["id"] = group_api_data["id"]
        group = StackDeploymentGroup.model_validate(attrs)
        assert group.id == "sdg-xyz789"
        assert group.name == "dev"
        assert group.status == DeploymentGroupStatus.DEPLOYING

    def test_list_options_serialization(self):
        """StackDeploymentGroupListOptions serializes page[size]."""
        opts = StackDeploymentGroupListOptions(page_size=50)
        dumped = opts.model_dump(by_alias=True, exclude_none=True)
        assert dumped["page[size]"] == 50

    def test_rerun_options_serialization(self):
        """StackDeploymentGroupRerunOptions stores deployment names."""
        opts = StackDeploymentGroupRerunOptions(deployments=["dev", "prod"])
        assert opts.deployments == ["dev", "prod"]

    # ── list() tests ─────────────────────────────────────────────────────────

    def test_list_invalid_config_id_raises(self, service):
        """list() with an empty config ID raises InvalidStackConfigurationIDError."""
        with pytest.raises(InvalidStackConfigurationIDError):
            list(service.list(""))

    def test_list_success(self, service, group_api_data):
        """list() yields StackDeploymentGroup objects from paginated results."""
        service._list = Mock(return_value=[group_api_data])

        results = list(service.list("stc-abc123"))

        service._list.assert_called_once_with(
            path="/api/v2/stack-configurations/stc-abc123/stack-deployment-groups",
            params={},
        )
        assert len(results) == 1
        assert isinstance(results[0], StackDeploymentGroup)
        assert results[0].id == "sdg-xyz789"
        assert results[0].name == "dev"

    def test_list_with_page_size(self, service, group_api_data):
        """list() passes page[size] param correctly."""
        service._list = Mock(return_value=[group_api_data])
        opts = StackDeploymentGroupListOptions(page_size=10)
        list(service.list("stc-abc123", options=opts))
        service._list.assert_called_once_with(
            path="/api/v2/stack-configurations/stc-abc123/stack-deployment-groups",
            params={"page[size]": 10},
        )

    def test_list_hydrates_config_relation(self, service, group_api_data):
        """list() hydrates the stack-configuration relation as a typed stub."""
        service._list = Mock(return_value=[group_api_data])
        results = list(service.list("stc-abc123"))
        assert isinstance(results[0].stack_configuration, StackConfiguration)
        assert results[0].stack_configuration.id == "stc-abc123"

    def test_list_empty(self, service):
        """list() returns an empty iterator when the API returns no items."""
        service._list = Mock(return_value=[])
        assert list(service.list("stc-abc123")) == []

    # ── read() tests ─────────────────────────────────────────────────────────

    def test_read_invalid_id_raises(self, service):
        """read() with an empty ID raises InvalidStackDeploymentGroupIDError."""
        with pytest.raises(InvalidStackDeploymentGroupIDError):
            service.read("")

    def test_read_success(self, service, mock_transport, group_api_data):
        """read() fetches a single deployment group by ID."""
        mock_response = Mock()
        mock_response.json.return_value = {"data": group_api_data}
        mock_transport.request.return_value = mock_response

        group = service.read("sdg-xyz789")

        mock_transport.request.assert_called_once_with(
            "GET", path="/api/v2/stack-deployment-groups/sdg-xyz789"
        )
        assert isinstance(group, StackDeploymentGroup)
        assert group.id == "sdg-xyz789"
        assert group.status == DeploymentGroupStatus.DEPLOYING

    # ── read_by_name() tests ──────────────────────────────────────────────────

    def test_read_by_name_invalid_config_id_raises(self, service):
        """read_by_name() with an empty config ID raises InvalidStackConfigurationIDError."""
        with pytest.raises(InvalidStackConfigurationIDError):
            service.read_by_name("", "dev")

    def test_read_by_name_success(self, service, mock_transport, group_api_data):
        """read_by_name() fetches a deployment group by config ID and name."""
        mock_response = Mock()
        mock_response.json.return_value = {"data": group_api_data}
        mock_transport.request.return_value = mock_response

        group = service.read_by_name("stc-abc123", "dev")

        mock_transport.request.assert_called_once_with(
            "GET",
            path="/api/v2/stack-configurations/stc-abc123/stack-deployment-groups/dev",
        )
        assert group.name == "dev"

    # ── approve_all_plans() tests ─────────────────────────────────────────────

    def test_approve_all_plans_invalid_id_raises(self, service):
        """approve_all_plans() with an empty ID raises InvalidStackDeploymentGroupIDError."""
        with pytest.raises(InvalidStackDeploymentGroupIDError):
            service.approve_all_plans("")

    def test_approve_all_plans_calls_correct_endpoint(self, service, mock_transport):
        """approve_all_plans() POSTs to the approve-all-plans action endpoint."""
        mock_transport.request.return_value = Mock()
        service.approve_all_plans("sdg-xyz789")
        mock_transport.request.assert_called_once_with(
            "POST",
            path="/api/v2/stack-deployment-groups/sdg-xyz789/approve-all-plans",
        )

    # ── rerun() tests ─────────────────────────────────────────────────────────

    def test_rerun_invalid_id_raises(self, service):
        """rerun() with an empty ID raises InvalidStackDeploymentGroupIDError."""
        with pytest.raises(InvalidStackDeploymentGroupIDError):
            service.rerun("", StackDeploymentGroupRerunOptions(deployments=["dev"]))

    def test_rerun_empty_deployments_raises(self, service):
        """rerun() raises ValueError when options.deployments is empty."""
        with pytest.raises(ValueError, match="at least one"):
            service.rerun(
                "sdg-xyz789", StackDeploymentGroupRerunOptions(deployments=[])
            )

    def test_rerun_calls_correct_endpoint(self, service, mock_transport):
        """rerun() POSTs to the rerun endpoint with deployment names as a query param."""
        mock_transport.request.return_value = Mock()
        opts = StackDeploymentGroupRerunOptions(deployments=["dev", "prod"])
        service.rerun("sdg-xyz789", opts)
        mock_transport.request.assert_called_once_with(
            "POST",
            path="/api/v2/stack-deployment-groups/sdg-xyz789/rerun",
            params={"deployments": "dev,prod"},
        )
