# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""Unit tests for the IP allowlist (CIDR range list) resources."""

from unittest.mock import Mock

import pytest

from pytfe._http import HTTPTransport
from pytfe.errors import (
    InvalidAgentPoolIDError,
    InvalidCIDRRangeIDError,
    InvalidCIDRRangeListIDError,
    InvalidOrgError,
    RequiredCIDRBlockError,
    RequiredNameError,
)
from pytfe.models.cidr_range_list import (
    CIDRRange,
    CIDRRangeCreateOptions,
    CIDRRangeList,
    CIDRRangeListCreateOptions,
    CIDRRangeListUpdateOptions,
    CIDRRangeUpdateOptions,
    EnforcementScope,
)
from pytfe.resources.cidr_range_list import CIDRRangeLists, CIDRRanges


class TestCIDRRangeLists:
    """Test the CIDRRangeLists (IP allowlist) service class."""

    @pytest.fixture
    def mock_transport(self):
        return Mock(spec=HTTPTransport)

    @pytest.fixture
    def service(self, mock_transport):
        return CIDRRangeLists(mock_transport)

    @pytest.fixture
    def list_api_data(self):
        return {
            "id": "crl-xKw8dxQPqVQRZmCe",
            "type": "cidr-range-lists",
            "attributes": {
                "name": "Office Network",
                "description": "IP ranges for office locations",
                "enforcement-scope": "selected_agent_pools",
            },
            "relationships": {
                "cidr-ranges": {
                    "data": [{"id": "cidr-6huHpM7asDp7TaiP", "type": "cidr-ranges"}]
                }
            },
        }

    # ── Model / options ───────────────────────────────────────────────────────

    def test_create_options_requires_name(self):
        with pytest.raises(RequiredNameError):
            CIDRRangeListCreateOptions(name="")

    def test_create_options_enforcement_scope_serializes_underscored(self):
        opts = CIDRRangeListCreateOptions(
            name="Office Network",
            enforcement_scope=EnforcementScope.ALL_AGENT_POOLS,
        )
        dumped = opts.model_dump(by_alias=True, exclude_none=True, mode="json")
        assert dumped == {
            "name": "Office Network",
            "enforcement-scope": "all_agent_pools",
        }

    # ── List / create / read / update / delete ────────────────────────────────

    def test_list_success(self, service, list_api_data):
        service._list = Mock(return_value=[list_api_data])

        results = list(service.list("my-org"))

        service._list.assert_called_once_with(
            "/api/v2/organizations/my-org/cidr-range-lists", params={}
        )
        assert len(results) == 1
        assert isinstance(results[0], CIDRRangeList)
        assert results[0].id == "crl-xKw8dxQPqVQRZmCe"
        assert results[0].enforcement_scope == EnforcementScope.SELECTED_AGENT_POOLS
        assert results[0].cidr_ranges[0].id == "cidr-6huHpM7asDp7TaiP"

    def test_list_invalid_org(self, service):
        with pytest.raises(InvalidOrgError):
            list(service.list("not valid!"))

    def test_create_success(self, service, mock_transport, list_api_data):
        mock_response = Mock()
        mock_response.json.return_value = {"data": list_api_data}
        mock_transport.request.return_value = mock_response

        opts = CIDRRangeListCreateOptions(
            name="Office Network",
            description="IP ranges for office locations",
            enforcement_scope=EnforcementScope.SELECTED_AGENT_POOLS,
        )
        result = service.create("my-org", opts)

        mock_transport.request.assert_called_once_with(
            "POST",
            "/api/v2/organizations/my-org/cidr-range-lists",
            json_body={
                "data": {
                    "type": "cidr-range-lists",
                    "attributes": {
                        "name": "Office Network",
                        "description": "IP ranges for office locations",
                        "enforcement-scope": "selected_agent_pools",
                    },
                }
            },
        )
        assert isinstance(result, CIDRRangeList)
        assert result.id == "crl-xKw8dxQPqVQRZmCe"

    def test_create_invalid_org(self, service):
        with pytest.raises(InvalidOrgError):
            service.create("not valid!", CIDRRangeListCreateOptions(name="x"))

    def test_read_success(self, service, mock_transport, list_api_data):
        mock_response = Mock()
        mock_response.json.return_value = {"data": list_api_data}
        mock_transport.request.return_value = mock_response

        result = service.read("crl-xKw8dxQPqVQRZmCe")

        mock_transport.request.assert_called_once_with(
            "GET", "/api/v2/cidr-range-lists/crl-xKw8dxQPqVQRZmCe"
        )
        assert result.name == "Office Network"

    def test_read_invalid_id(self, service):
        with pytest.raises(InvalidCIDRRangeListIDError):
            service.read("not valid!")

    def test_update_with_scope_single_request(
        self, service, mock_transport, list_api_data
    ):
        """When enforcement_scope is provided, update issues a single PATCH."""
        mock_response = Mock()
        mock_response.json.return_value = {"data": list_api_data}
        mock_transport.request.return_value = mock_response

        opts = CIDRRangeListUpdateOptions(
            name="Updated Office Network",
            enforcement_scope=EnforcementScope.ALL_AGENT_POOLS,
        )
        service.update("crl-xKw8dxQPqVQRZmCe", opts)

        mock_transport.request.assert_called_once_with(
            "PATCH",
            "/api/v2/cidr-range-lists/crl-xKw8dxQPqVQRZmCe",
            json_body={
                "data": {
                    "type": "cidr-range-lists",
                    "attributes": {
                        "name": "Updated Office Network",
                        "enforcement-scope": "all_agent_pools",
                    },
                }
            },
        )

    def test_update_without_scope_preserves_current(
        self, service, mock_transport, list_api_data
    ):
        """When enforcement_scope is omitted, update reads the current scope and
        carries it forward (the API rejects a PATCH without enforcement-scope)."""
        read_resp = Mock()
        read_resp.json.return_value = {"data": list_api_data}  # selected_agent_pools
        patch_resp = Mock()
        patch_resp.json.return_value = {"data": list_api_data}
        mock_transport.request.side_effect = [read_resp, patch_resp]

        service.update(
            "crl-xKw8dxQPqVQRZmCe", CIDRRangeListUpdateOptions(name="Renamed")
        )

        assert mock_transport.request.call_count == 2
        get_call, patch_call = mock_transport.request.call_args_list
        assert get_call.args == (
            "GET",
            "/api/v2/cidr-range-lists/crl-xKw8dxQPqVQRZmCe",
        )
        assert patch_call.args[0] == "PATCH"
        assert patch_call.kwargs["json_body"] == {
            "data": {
                "type": "cidr-range-lists",
                "attributes": {
                    "name": "Renamed",
                    "enforcement-scope": "selected_agent_pools",
                },
            }
        }

    def test_update_invalid_id(self, service):
        with pytest.raises(InvalidCIDRRangeListIDError):
            service.update("", CIDRRangeListUpdateOptions(name="x"))

    def test_delete_success(self, service, mock_transport):
        mock_transport.request.return_value = Mock()

        service.delete("crl-xKw8dxQPqVQRZmCe")

        mock_transport.request.assert_called_once_with(
            "DELETE", "/api/v2/cidr-range-lists/crl-xKw8dxQPqVQRZmCe"
        )

    def test_delete_invalid_id(self, service):
        with pytest.raises(InvalidCIDRRangeListIDError):
            service.delete("")

    # ── CIDR range relationships ──────────────────────────────────────────────

    def test_list_cidr_ranges_success(self, service):
        range_data = {
            "id": "cidr-6huHpM7asDp7TaiP",
            "type": "cidr-ranges",
            "attributes": {"range": "192.168.1.0/24"},
        }
        service._list = Mock(return_value=[range_data])

        results = list(service.list_cidr_ranges("crl-xKw8dxQPqVQRZmCe"))

        service._list.assert_called_once_with(
            "/api/v2/cidr-range-lists/crl-xKw8dxQPqVQRZmCe/relationships/cidr-ranges"
        )
        assert results[0].cidr_block == "192.168.1.0/24"

    def test_list_cidr_ranges_invalid_id(self, service):
        with pytest.raises(InvalidCIDRRangeListIDError):
            list(service.list_cidr_ranges(""))

    def test_add_cidr_range_success(self, service, mock_transport):
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {
                "id": "cidr-6huHpM7asDp7TaiP",
                "type": "cidr-ranges",
                "attributes": {"range": "192.168.1.0/24"},
            }
        }
        mock_transport.request.return_value = mock_response

        result = service.add_cidr_range(
            "crl-xKw8dxQPqVQRZmCe", CIDRRangeCreateOptions(cidr_block="192.168.1.0/24")
        )

        mock_transport.request.assert_called_once_with(
            "POST",
            "/api/v2/cidr-range-lists/crl-xKw8dxQPqVQRZmCe/relationships/cidr-ranges",
            json_body={
                "data": {
                    "type": "cidr-ranges",
                    "attributes": {"range": "192.168.1.0/24"},
                }
            },
        )
        assert isinstance(result, CIDRRange)
        assert result.cidr_block == "192.168.1.0/24"

    def test_add_cidr_range_requires_block(self):
        with pytest.raises(RequiredCIDRBlockError):
            CIDRRangeCreateOptions(cidr_block="")

    def test_add_agent_pools_success(self, service, mock_transport):
        mock_transport.request.return_value = Mock()

        service.add_agent_pools("crl-xKw8dxQPqVQRZmCe", ["apool-abc", "apool-def"])

        mock_transport.request.assert_called_once_with(
            "POST",
            "/api/v2/cidr-range-lists/crl-xKw8dxQPqVQRZmCe/relationships/agent-pools",
            json_body={
                "data": [
                    {"type": "agent-pools", "id": "apool-abc"},
                    {"type": "agent-pools", "id": "apool-def"},
                ]
            },
        )

    def test_remove_agent_pools_success(self, service, mock_transport):
        mock_transport.request.return_value = Mock()

        service.remove_agent_pools("crl-xKw8dxQPqVQRZmCe", ["apool-abc"])

        mock_transport.request.assert_called_once_with(
            "DELETE",
            "/api/v2/cidr-range-lists/crl-xKw8dxQPqVQRZmCe/relationships/agent-pools",
            json_body={"data": [{"type": "agent-pools", "id": "apool-abc"}]},
        )

    def test_add_agent_pools_empty_raises(self, service):
        with pytest.raises(InvalidAgentPoolIDError):
            service.add_agent_pools("crl-xKw8dxQPqVQRZmCe", [])

    def test_add_agent_pools_invalid_id_raises(self, service):
        with pytest.raises(InvalidAgentPoolIDError):
            service.add_agent_pools("crl-xKw8dxQPqVQRZmCe", ["not valid!"])

    def test_add_agent_pools_invalid_list_id(self, service):
        with pytest.raises(InvalidCIDRRangeListIDError):
            service.add_agent_pools("", ["apool-abc"])


class TestCIDRRanges:
    """Test the CIDRRanges service class."""

    @pytest.fixture
    def mock_transport(self):
        return Mock(spec=HTTPTransport)

    @pytest.fixture
    def service(self, mock_transport):
        return CIDRRanges(mock_transport)

    @pytest.fixture
    def range_api_data(self):
        return {
            "id": "cidr-6huHpM7asDp7TaiP",
            "type": "cidr-ranges",
            "attributes": {"range": "192.168.1.0/24"},
        }

    def test_read_success(self, service, mock_transport, range_api_data):
        mock_response = Mock()
        mock_response.json.return_value = {"data": range_api_data}
        mock_transport.request.return_value = mock_response

        result = service.read("cidr-6huHpM7asDp7TaiP")

        mock_transport.request.assert_called_once_with(
            "GET", "/api/v2/cidr-ranges/cidr-6huHpM7asDp7TaiP"
        )
        assert isinstance(result, CIDRRange)
        assert result.cidr_block == "192.168.1.0/24"

    def test_read_invalid_id(self, service):
        with pytest.raises(InvalidCIDRRangeIDError):
            service.read("not valid!")

    def test_update_success(self, service, mock_transport, range_api_data):
        mock_response = Mock()
        mock_response.json.return_value = {"data": range_api_data}
        mock_transport.request.return_value = mock_response

        service.update(
            "cidr-6huHpM7asDp7TaiP", CIDRRangeUpdateOptions(cidr_block="192.168.2.0/24")
        )

        mock_transport.request.assert_called_once_with(
            "PATCH",
            "/api/v2/cidr-ranges/cidr-6huHpM7asDp7TaiP",
            json_body={
                "data": {
                    "type": "cidr-ranges",
                    "attributes": {"range": "192.168.2.0/24"},
                }
            },
        )

    def test_update_invalid_id(self, service):
        with pytest.raises(InvalidCIDRRangeIDError):
            service.update("", CIDRRangeUpdateOptions(cidr_block="10.0.0.0/8"))

    def test_delete_success(self, service, mock_transport):
        mock_transport.request.return_value = Mock()

        service.delete("cidr-6huHpM7asDp7TaiP")

        mock_transport.request.assert_called_once_with(
            "DELETE", "/api/v2/cidr-ranges/cidr-6huHpM7asDp7TaiP"
        )

    def test_delete_invalid_id(self, service):
        with pytest.raises(InvalidCIDRRangeIDError):
            service.delete("")
