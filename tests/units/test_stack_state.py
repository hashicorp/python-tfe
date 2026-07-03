# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""Unit tests for the stack_states module."""

from unittest.mock import Mock

import pytest

from pytfe._http import HTTPTransport
from pytfe.errors import InvalidStackIDError, InvalidStackStateIDError
from pytfe.models.stack import Stack
from pytfe.models.stack_deployment_run import StackDeploymentRun
from pytfe.models.stack_state import (
    StackState,
    StackStateComponent,
    StackStateListOptions,
)
from pytfe.resources.stack_states import StackStates


class TestStackStates:
    """Test the StackStates service class."""

    @pytest.fixture
    def mock_transport(self):
        """Create a mock HTTPTransport."""
        return Mock(spec=HTTPTransport)

    @pytest.fixture
    def service(self, mock_transport):
        """Create a StackStates service with mocked transport."""
        return StackStates(mock_transport)

    @pytest.fixture
    def state_api_data(self):
        """Typical API response item for a single stack state."""
        return {
            "id": "ss-abc123",
            "type": "stack-states",
            "attributes": {
                "generation": 3,
                "status": "current",
                "deployment": "dev",
                "components": [
                    {
                        "address": "component.ns",
                        "component-address": "component.ns",
                        "instance-correlator": "abc123==",
                        "component-correlator": "xyz789==",
                        "resource-instance-count": 1,
                    }
                ],
                "is-current": True,
                "resource-instance-count": 7,
            },
            "relationships": {
                "stack": {"data": {"id": "st-xyz789", "type": "stacks"}},
                "stack-deployment-run": {
                    "data": {"id": "sdr-run001", "type": "stack-deployment-runs"}
                },
            },
        }

    # ── Model tests ──────────────────────────────────────────────────────────

    def test_stack_state_parse(self, state_api_data):
        """StackState parses all attributes correctly."""
        attrs = dict(state_api_data["attributes"])
        attrs["id"] = state_api_data["id"]
        state = StackState.model_validate(attrs)
        assert state.id == "ss-abc123"
        assert state.generation == 3
        assert state.status == "current"
        assert state.deployment == "dev"
        assert state.is_current is True
        assert state.resource_instance_count == 7

    def test_stack_state_component_parse(self):
        """StackStateComponent parses the wire fields from a stack-state response."""
        raw = {
            "address": "component.ns",
            "component-address": "component.ns",
            "instance-correlator": "abc123==",
            "component-correlator": "xyz789==",
            "resource-instance-count": 1,
        }
        comp = StackStateComponent.model_validate(raw)
        assert comp.address == "component.ns"
        assert comp.component_address == "component.ns"
        assert comp.instance_correlator == "abc123=="
        assert comp.component_correlator == "xyz789=="
        assert comp.resource_instance_count == 1

    def test_stack_state_list_options_serialization(self):
        """StackStateListOptions serializes page[size] correctly."""
        opts = StackStateListOptions(page_size=20)
        dumped = opts.model_dump(by_alias=True, exclude_none=True)
        assert dumped["page[size]"] == 20

    # ── list() tests ─────────────────────────────────────────────────────────

    def test_list_invalid_stack_id_raises(self, service):
        """list() with an empty stack ID raises InvalidStackIDError."""
        with pytest.raises(InvalidStackIDError):
            list(service.list(""))

    def test_list_success(self, service, state_api_data):
        """list() yields StackState objects from paginated results."""
        service._list = Mock(return_value=[state_api_data])

        results = list(service.list("st-xyz789"))

        service._list.assert_called_once_with(
            path="/api/v2/stacks/st-xyz789/stack-states",
            params={},
        )
        assert len(results) == 1
        assert isinstance(results[0], StackState)
        assert results[0].id == "ss-abc123"

    def test_list_with_page_size(self, service, state_api_data):
        """list() passes page[size] param correctly."""
        service._list = Mock(return_value=[state_api_data])
        opts = StackStateListOptions(page_size=10)
        list(service.list("st-xyz789", options=opts))
        service._list.assert_called_once_with(
            path="/api/v2/stacks/st-xyz789/stack-states",
            params={"page[size]": 10},
        )

    def test_list_hydrates_stack_relation(self, service, state_api_data):
        """list() hydrates the stack relation as a typed stub."""
        service._list = Mock(return_value=[state_api_data])
        results = list(service.list("st-xyz789"))
        assert isinstance(results[0].stack, Stack)
        assert results[0].stack.id == "st-xyz789"

    def test_list_hydrates_run_relation(self, service, state_api_data):
        """list() hydrates the stack-deployment-run relation as a typed stub."""
        service._list = Mock(return_value=[state_api_data])
        results = list(service.list("st-xyz789"))
        assert isinstance(results[0].stack_deployment_run, StackDeploymentRun)
        assert results[0].stack_deployment_run.id == "sdr-run001"

    def test_list_empty(self, service):
        """list() returns an empty iterator when the API returns no items."""
        service._list = Mock(return_value=[])
        assert list(service.list("st-xyz789")) == []

    # ── read() tests ─────────────────────────────────────────────────────────

    def test_read_invalid_id_raises(self, service):
        """read() with an empty ID raises InvalidStackStateIDError."""
        with pytest.raises(InvalidStackStateIDError):
            service.read("")

    def test_read_success(self, service, mock_transport, state_api_data):
        """read() fetches a single stack state by ID."""
        mock_response = Mock()
        mock_response.json.return_value = {"data": state_api_data}
        mock_transport.request.return_value = mock_response

        state = service.read("ss-abc123")

        mock_transport.request.assert_called_once_with(
            "GET", path="/api/v2/stack-states/ss-abc123"
        )
        assert isinstance(state, StackState)
        assert state.id == "ss-abc123"
        assert state.generation == 3
        assert state.is_current is True

    def test_read_hydrates_relations(self, service, mock_transport, state_api_data):
        """read() hydrates both stack and run relations."""
        mock_response = Mock()
        mock_response.json.return_value = {"data": state_api_data}
        mock_transport.request.return_value = mock_response

        state = service.read("ss-abc123")
        assert isinstance(state.stack, Stack)
        assert state.stack.id == "st-xyz789"
        assert isinstance(state.stack_deployment_run, StackDeploymentRun)
        assert state.stack_deployment_run.id == "sdr-run001"

    # ── download_description() tests ─────────────────────────────────────────

    def test_download_description_invalid_id_raises(self, service):
        """download_description() with an empty ID raises InvalidStackStateIDError."""
        with pytest.raises(InvalidStackStateIDError):
            service.download_description("")

    def test_download_description_returns_bytes(self, service, mock_transport):
        """download_description() returns the raw response bytes."""
        raw = b"# Stack state description\nresources: 7"
        mock_response = Mock()
        mock_response.content = raw
        mock_transport.request.return_value = mock_response

        result = service.download_description("ss-abc123")

        mock_transport.request.assert_called_once_with(
            "GET", path="/api/v2/stack-states/ss-abc123/description"
        )
        assert result == raw
