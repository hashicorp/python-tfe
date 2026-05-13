# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""Unit tests for the stack_configuration module."""

from unittest.mock import Mock

import pytest

from pytfe._http import HTTPTransport
from pytfe.models.configuration_version import IngressAttributes
from pytfe.models.stack import Stack
from pytfe.models.stack_configuration import (
    StackComponent,
    StackConfiguration,
    StackConfigurationCreateOptions,
    StackConfigurationIncludeOps,
    StackConfigurationListOptions,
    StackConfigurationReadOptions,
    StackConfigurationSource,
    StackConfigurationStatus,
)
from pytfe.resources.stack_configuration import StackConfigurations


class TestStackConfigurations:
    """Test the StackConfigurations service class."""

    @pytest.fixture
    def mock_transport(self):
        """Create a mock HTTPTransport."""
        return Mock(spec=HTTPTransport)

    @pytest.fixture
    def service(self, mock_transport):
        """Create a StackConfigurations service with mocked transport."""
        return StackConfigurations(mock_transport)

    @pytest.fixture
    def stack_configuration_api_data(self):
        """Typical API response for a single stack configuration."""
        return {
            "id": "stc-abc123",
            "type": "stack-configurations",
            "attributes": {
                "status": "completed",
                "sequence-number": 3,
                "speculative": False,
                "destroy-all": False,
                "preparing-event-stream-url": "https://example.com/stream",
                "created-at": "2026-05-07T11:32:17.031000+00:00",
                "updated-at": "2026-05-07T11:32:50.500000+00:00",
                "components": [
                    {
                        "name": "simple_default",
                        "correlator": "simple_default",
                        "expanded": True,
                        "removed": False,
                    }
                ],
            },
            "relationships": {
                "stack": {"data": {"id": "st-xyz789", "type": "stacks"}},
                "ingress-attributes": {
                    "data": {"id": "ia-111", "type": "ingress-attributes"}
                },
            },
        }

    # ── Model tests ──────────────────────────────────────────────────────────

    def test_stack_component_defaults(self):
        """StackComponent can be constructed with defaults."""
        comp = StackComponent()
        assert comp.name == ""
        assert comp.correlator == ""
        assert comp.expanded is None
        assert comp.removed is None

    def test_stack_component_full(self):
        """StackComponent parses all fields."""
        comp = StackComponent.model_validate(
            {
                "name": "my_stack",
                "correlator": "corr-1",
                "expanded": True,
                "removed": False,
            }
        )
        assert comp.name == "my_stack"
        assert comp.correlator == "corr-1"
        assert comp.expanded is True
        assert comp.removed is False

    def test_stack_configuration_status_enum(self):
        """StackConfigurationStatus values are correct."""
        assert StackConfigurationStatus.PENDING == "pending"
        assert StackConfigurationStatus.QUEUED == "queued"
        assert StackConfigurationStatus.PREPARING == "preparing"
        assert StackConfigurationStatus.COMPLETED == "completed"
        assert StackConfigurationStatus.FAILED == "failed"

    def test_stack_configuration_source_enum(self):
        """StackConfigurationSource values are correct."""
        assert StackConfigurationSource.MANUAL == "manual"
        assert StackConfigurationSource.FETCH == "fetch"
        assert StackConfigurationSource.REUSE == "reuse"

    def test_stack_configuration_include_enum(self):
        """StackConfigurationIncludeOps values are correct."""
        assert StackConfigurationIncludeOps.INGRESS_ATTRIBUTES == "ingress_attributes"
        assert StackConfigurationIncludeOps.STACK_DIAGNOSTICS == "stack_diagnostics"

    def test_create_options_defaults(self):
        """StackConfigurationCreateOptions has sane defaults."""
        opts = StackConfigurationCreateOptions()
        assert opts.speculative_enabled is False
        assert opts.destroy_all is False
        assert opts.selected_deployments is None

    def test_create_options_serializes_with_aliases(self):
        """StackConfigurationCreateOptions serialises with API aliases."""
        opts = StackConfigurationCreateOptions(
            speculative_enabled=True,
            destroy_all=True,
            selected_deployments=["dep-a", "dep-b"],
        )
        dumped = opts.model_dump(by_alias=True, exclude_none=True)
        assert dumped["speculative"] is True
        assert dumped["destroy-all"] is True
        assert dumped["selected-deployments"] == ["dep-a", "dep-b"]

    def test_list_options_serialization(self):
        """StackConfigurationListOptions serialises page[size] alias."""
        opts = StackConfigurationListOptions(
            page_size=50,
            include=[StackConfigurationIncludeOps.INGRESS_ATTRIBUTES],
        )
        assert opts.page_size == 50
        assert opts.include == [StackConfigurationIncludeOps.INGRESS_ATTRIBUTES]

    def test_read_options(self):
        """StackConfigurationReadOptions stores include list."""
        opts = StackConfigurationReadOptions(
            include=[
                StackConfigurationIncludeOps.INGRESS_ATTRIBUTES,
                StackConfigurationIncludeOps.STACK_DIAGNOSTICS,
            ]
        )
        assert len(opts.include) == 2

    # ── Parser tests ─────────────────────────────────────────────────────────

    def test_stack_configuration_from_full_data(
        self, service, stack_configuration_api_data
    ):
        """_stack_configuration_from parses all attributes and relations."""
        result = service._stack_configuration_from(stack_configuration_api_data)

        assert isinstance(result, StackConfiguration)
        assert result.id == "stc-abc123"
        assert result.status == StackConfigurationStatus.COMPLETED
        assert result.sequence_number == 3
        assert result.speculative is False
        assert result.preparing_event_stream_url == "https://example.com/stream"
        assert result.created_at is not None
        assert result.updated_at is not None

        # Components
        assert len(result.components) == 1
        assert result.components[0].name == "simple_default"
        assert result.components[0].expanded is True

        # Relations
        assert isinstance(result.stack, Stack)
        assert result.stack.id == "st-xyz789"
        assert isinstance(result.ingress_attributes, IngressAttributes)

    def test_stack_configuration_from_no_relationships(self, service):
        """_stack_configuration_from handles missing relationship data gracefully."""
        data = {
            "id": "stc-min",
            "attributes": {
                "status": "pending",
                "sequence-number": 1,
            },
            "relationships": {},
        }
        result = service._stack_configuration_from(data)

        assert result.id == "stc-min"
        assert result.status == StackConfigurationStatus.PENDING
        assert result.stack is None
        assert result.ingress_attributes is None

    def test_stack_configuration_from_null_relationship_data(self, service):
        """_stack_configuration_from handles null data inside relationship."""
        data = {
            "id": "stc-null",
            "attributes": {"status": "queued"},
            "relationships": {
                "stack": {"data": None},
                "ingress-attributes": {"data": None},
            },
        }
        result = service._stack_configuration_from(data)

        assert result.id == "stc-null"
        assert result.stack is None
        assert result.ingress_attributes is None

    def test_stack_configuration_from_empty_components(self, service):
        """_stack_configuration_from handles empty components list."""
        data = {
            "id": "stc-empty",
            "attributes": {"status": "completed", "components": []},
            "relationships": {},
        }
        result = service._stack_configuration_from(data)
        assert result.components == []

    # ── Resource method tests ─────────────────────────────────────────────────

    def test_create_success(
        self, service, mock_transport, stack_configuration_api_data
    ):
        """create() POSTs the correct payload and returns a StackConfiguration."""
        mock_response = Mock()
        mock_response.json.return_value = {"data": stack_configuration_api_data}
        mock_transport.request.return_value = mock_response

        opts = StackConfigurationCreateOptions(speculative_enabled=True)
        result = service.create(stack_id="st-xyz789", options=opts)

        mock_transport.request.assert_called_once_with(
            "POST",
            path="/api/v2/stacks/st-xyz789/stack-configurations",
            json_body={
                "data": {
                    "type": "stack-configurations",
                    "attributes": {"speculative": True, "destroy-all": False},
                }
            },
            params={},
        )
        assert isinstance(result, StackConfiguration)
        assert result.id == "stc-abc123"

    def test_create_with_fetch_source(
        self, service, mock_transport, stack_configuration_api_data
    ):
        """create() passes source param when not MANUAL."""
        mock_response = Mock()
        mock_response.json.return_value = {"data": stack_configuration_api_data}
        mock_transport.request.return_value = mock_response

        service.create(stack_id="st-xyz789", source=StackConfigurationSource.FETCH)

        _, kwargs = mock_transport.request.call_args
        assert kwargs["params"] == {"source": "fetch"}

    def test_create_no_options(
        self, service, mock_transport, stack_configuration_api_data
    ):
        """create() sends empty attributes when no options provided."""
        mock_response = Mock()
        mock_response.json.return_value = {"data": stack_configuration_api_data}
        mock_transport.request.return_value = mock_response

        service.create(stack_id="st-xyz789")

        _, kwargs = mock_transport.request.call_args
        assert kwargs["json_body"]["data"]["attributes"] == {}

    def test_list_success(self, service, stack_configuration_api_data):
        """list() yields StackConfiguration objects from paginated results."""
        service._list = Mock(return_value=[stack_configuration_api_data])

        opts = StackConfigurationListOptions(page_size=20)
        results = list(service.list(stack_id="st-xyz789", options=opts))

        service._list.assert_called_once_with(
            path="/api/v2/stacks/st-xyz789/stack-configurations",
            params={"page[size]": 20},
        )
        assert len(results) == 1
        assert isinstance(results[0], StackConfiguration)
        assert results[0].id == "stc-abc123"

    def test_list_with_include(self, service, stack_configuration_api_data):
        """list() passes include param as comma-separated string."""
        service._list = Mock(return_value=[stack_configuration_api_data])

        opts = StackConfigurationListOptions(
            include=[StackConfigurationIncludeOps.INGRESS_ATTRIBUTES]
        )
        list(service.list(stack_id="st-xyz789", options=opts))

        _, kwargs = service._list.call_args
        assert kwargs["params"]["include"] == "ingress_attributes"

    def test_list_empty(self, service):
        """list() returns empty iterator when no items returned."""
        service._list = Mock(return_value=[])

        results = list(service.list(stack_id="st-xyz789"))
        assert results == []

    def test_list_no_options(self, service, stack_configuration_api_data):
        """list() works correctly when no options are given."""
        service._list = Mock(return_value=[stack_configuration_api_data])

        results = list(service.list(stack_id="st-xyz789"))

        service._list.assert_called_once_with(
            path="/api/v2/stacks/st-xyz789/stack-configurations",
            params={},
        )
        assert len(results) == 1

    def test_read_success(self, service, mock_transport, stack_configuration_api_data):
        """read() GETs the correct path and returns a StackConfiguration."""
        mock_response = Mock()
        mock_response.json.return_value = {"data": stack_configuration_api_data}
        mock_transport.request.return_value = mock_response

        result = service.read(stack_configuration_id="stc-abc123")

        mock_transport.request.assert_called_once_with(
            "GET",
            path="/api/v2/stack-configurations/stc-abc123",
            params={},
        )
        assert isinstance(result, StackConfiguration)
        assert result.id == "stc-abc123"
        assert result.status == StackConfigurationStatus.COMPLETED

    def test_read_with_include(
        self, service, mock_transport, stack_configuration_api_data
    ):
        """read() appends include query param."""
        mock_response = Mock()
        mock_response.json.return_value = {"data": stack_configuration_api_data}
        mock_transport.request.return_value = mock_response

        opts = StackConfigurationReadOptions(
            include=[
                StackConfigurationIncludeOps.INGRESS_ATTRIBUTES,
                StackConfigurationIncludeOps.STACK_DIAGNOSTICS,
            ]
        )
        service.read(stack_configuration_id="stc-abc123", options=opts)

        _, kwargs = mock_transport.request.call_args
        assert kwargs["params"]["include"] == "ingress_attributes,stack_diagnostics"
