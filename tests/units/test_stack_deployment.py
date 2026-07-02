# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""Unit tests for the stack_deployment module."""

from unittest.mock import Mock

import pytest

from pytfe._http import HTTPTransport
from pytfe.errors import InvalidStackIDError
from pytfe.models.stack import Stack
from pytfe.models.stack_deployment import (
    StackDeployment,
    StackDeploymentIncludeOpt,
    StackDeploymentListOptions,
)
from pytfe.resources.stack_deployment import StackDeployments


class TestStackDeployments:
    """Test the StackDeployments service class."""

    @pytest.fixture
    def mock_transport(self):
        """Create a mock HTTPTransport."""
        return Mock(spec=HTTPTransport)

    @pytest.fixture
    def service(self, mock_transport):
        """Create a StackDeployments service with mocked transport."""
        return StackDeployments(mock_transport)

    @pytest.fixture
    def stack_deployment_api_data(self):
        """Typical API response item for a single stack deployment."""
        return {
            "id": "st-MWvJsvy1FCg3bnXY-std-simple",
            "type": "stack-deployments",
            "attributes": {"name": "simple"},
            "relationships": {
                "stack": {
                    "data": {"id": "st-MWvJsvy1FCg3bnXY", "type": "stacks"}
                },
                "latest-deployment-run": {
                    "data": {
                        "id": "sdr-vzub48Y4f7sFBk7J",
                        "type": "stack-deployment-runs",
                    }
                },
            },
        }

    # ── Model tests ──────────────────────────────────────────────────────────

    def test_stack_deployment_parse(self, stack_deployment_api_data):
        """StackDeployment parses id, name, and the stack relation."""
        attrs = dict(stack_deployment_api_data["attributes"])
        attrs["id"] = stack_deployment_api_data["id"]
        deployment = StackDeployment.model_validate(attrs)
        assert deployment.id == "st-MWvJsvy1FCg3bnXY-std-simple"
        assert deployment.name == "simple"

    def test_list_options_serialization(self):
        """StackDeploymentListOptions serializes page[size] and include."""
        opts = StackDeploymentListOptions(
            page_size=50,
            include=[StackDeploymentIncludeOpt.LATEST_DEPLOYMENT_RUN],
        )
        dumped = opts.model_dump(by_alias=True, exclude_none=True)
        assert dumped["page[size]"] == 50

    # ── list() tests ─────────────────────────────────────────────────────────

    def test_list_invalid_stack_id_raises(self, service):
        """list() with an empty stack id raises InvalidStackIDError on iteration."""
        with pytest.raises(InvalidStackIDError):
            list(service.list(""))

    def test_list_success(self, service, stack_deployment_api_data):
        """list() yields StackDeployment objects from paginated results."""
        service._list = Mock(return_value=[stack_deployment_api_data])

        opts = StackDeploymentListOptions(page_size=20)
        results = list(service.list(stack_id="st-MWvJsvy1FCg3bnXY", options=opts))

        service._list.assert_called_once_with(
            path="/api/v2/stacks/st-MWvJsvy1FCg3bnXY/stack-deployments",
            params={"page[size]": 20},
        )
        assert len(results) == 1
        assert isinstance(results[0], StackDeployment)
        assert results[0].id == "st-MWvJsvy1FCg3bnXY-std-simple"
        assert results[0].name == "simple"

    def test_list_hydrates_stack_relation(self, service, stack_deployment_api_data):
        """list() parses the stack relationship into a typed Stack stub."""
        service._list = Mock(return_value=[stack_deployment_api_data])

        results = list(service.list(stack_id="st-MWvJsvy1FCg3bnXY"))

        assert isinstance(results[0].stack, Stack)
        assert results[0].stack.id == "st-MWvJsvy1FCg3bnXY"

    def test_list_latest_run_reachable_raw(self, service, stack_deployment_api_data):
        """The unmodelled latest-deployment-run relation is reachable losslessly."""
        service._list = Mock(return_value=[stack_deployment_api_data])

        results = list(service.list(stack_id="st-MWvJsvy1FCg3bnXY"))

        refs = results[0].related("latest-deployment-run")
        assert refs[0]["id"] == "sdr-vzub48Y4f7sFBk7J"
        # raw escape-hatch data never leaks into model_dump()
        assert "relationships" not in results[0].model_dump()

    def test_list_with_include(self, service, stack_deployment_api_data):
        """list() passes include param as a comma-separated string."""
        service._list = Mock(return_value=[stack_deployment_api_data])

        opts = StackDeploymentListOptions(
            include=[
                StackDeploymentIncludeOpt.LATEST_DEPLOYMENT_RUN,
                StackDeploymentIncludeOpt.LATEST_DEPLOYMENT_RUN_STACK_CONFIGURATION,
            ]
        )
        list(service.list(stack_id="st-MWvJsvy1FCg3bnXY", options=opts))

        _, kwargs = service._list.call_args
        assert (
            kwargs["params"]["include"]
            == "latest_deployment_run,latest_deployment_run.stack_configuration"
        )

    def test_list_empty(self, service):
        """list() returns an empty iterator when no items are returned."""
        service._list = Mock(return_value=[])

        results = list(service.list(stack_id="st-MWvJsvy1FCg3bnXY"))
        assert results == []

    def test_list_no_options(self, service, stack_deployment_api_data):
        """list() works correctly when no options are given."""
        service._list = Mock(return_value=[stack_deployment_api_data])

        results = list(service.list(stack_id="st-MWvJsvy1FCg3bnXY"))

        service._list.assert_called_once_with(
            path="/api/v2/stacks/st-MWvJsvy1FCg3bnXY/stack-deployments",
            params={},
        )
        assert len(results) == 1
