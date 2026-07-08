# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""Unit tests for the stack_configuration_summaries module."""

from unittest.mock import Mock

import pytest

from pytfe._http import HTTPTransport
from pytfe.errors import InvalidStackIDError
from pytfe.models.stack_configuration import (
    StackConfigurationSummary,
    StackConfigurationSummaryListOptions,
)
from pytfe.resources.stack_configuration_summaries import StackConfigurationSummaries


class TestStackConfigurationSummaries:
    """Test the StackConfigurationSummaries service class."""

    @pytest.fixture
    def mock_transport(self):
        """Create a mock HTTPTransport."""
        return Mock(spec=HTTPTransport)

    @pytest.fixture
    def service(self, mock_transport):
        """Create a StackConfigurationSummaries service with mocked transport."""
        return StackConfigurationSummaries(mock_transport)

    @pytest.fixture
    def summary_api_data(self):
        """Typical API response item for a single stack configuration summary."""
        return {
            "id": "stcs-abc123",
            "type": "stack-configuration-summaries",
            "attributes": {
                "status": "converged",
                "sequence-number": 5,
            },
        }

    # ── Model tests ──────────────────────────────────────────────────────────

    def test_stack_configuration_summary_parse(self, summary_api_data):
        """StackConfigurationSummary parses all attributes correctly."""
        attrs = dict(summary_api_data["attributes"])
        attrs["id"] = summary_api_data["id"]
        summary = StackConfigurationSummary.model_validate(attrs)
        assert summary.id == "stcs-abc123"
        assert summary.status == "converged"
        assert summary.sequence_number == 5

    def test_stack_configuration_summary_list_options_serialization(self):
        """StackConfigurationSummaryListOptions serializes page[size] correctly."""
        opts = StackConfigurationSummaryListOptions(page_size=15)
        dumped = opts.model_dump(by_alias=True, exclude_none=True)
        assert dumped["page[size]"] == 15

    # ── list() tests ─────────────────────────────────────────────────────────

    def test_list_invalid_stack_id_raises(self, service):
        """list() with an empty stack ID raises InvalidStackIDError."""
        with pytest.raises(InvalidStackIDError):
            list(service.list(""))

    def test_list_success(self, service, summary_api_data):
        """list() yields StackConfigurationSummary objects from paginated results."""
        service._list = Mock(return_value=[summary_api_data])

        results = list(service.list("st-xyz789"))

        service._list.assert_called_once_with(
            path="/api/v2/stacks/st-xyz789/stack-configuration-summaries",
            params={},
        )
        assert len(results) == 1
        assert isinstance(results[0], StackConfigurationSummary)
        assert results[0].id == "stcs-abc123"

    def test_list_with_page_size(self, service, summary_api_data):
        """list() passes page[size] param correctly."""
        service._list = Mock(return_value=[summary_api_data])
        opts = StackConfigurationSummaryListOptions(page_size=5)
        list(service.list("st-xyz789", options=opts))
        service._list.assert_called_once_with(
            path="/api/v2/stacks/st-xyz789/stack-configuration-summaries",
            params={"page[size]": 5},
        )

    def test_list_empty(self, service):
        """list() returns an empty iterator when the API returns no items."""
        service._list = Mock(return_value=[])
        assert list(service.list("st-xyz789")) == []
