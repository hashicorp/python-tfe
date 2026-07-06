# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""Unit tests for the stack_deployment_group_summaries module."""

from unittest.mock import Mock

import pytest

from pytfe._http import HTTPTransport
from pytfe.errors import InvalidStackConfigurationIDError
from pytfe.models.stack_deployment_group import (
    StackDeploymentGroup,
    StackDeploymentGroupStatusCounts,
    StackDeploymentGroupSummary,
    StackDeploymentGroupSummaryListOptions,
)
from pytfe.resources.stack_deployment_group_summaries import (
    StackDeploymentGroupSummaries,
)


class TestStackDeploymentGroupSummaries:
    """Test the StackDeploymentGroupSummaries service class."""

    @pytest.fixture
    def mock_transport(self):
        """Create a mock HTTPTransport."""
        return Mock(spec=HTTPTransport)

    @pytest.fixture
    def service(self, mock_transport):
        """Create a StackDeploymentGroupSummaries service with mocked transport."""
        return StackDeploymentGroupSummaries(mock_transport)

    @pytest.fixture
    def summary_api_data(self):
        """Typical API response item for a single deployment group summary."""
        return {
            "id": "sdgs-abc123",
            "type": "stack-deployment-group-summaries",
            "attributes": {
                "name": "dev",
                "status": "succeeded",
                "status-counts": {
                    "pending": 0,
                    "pre-deploying": 0,
                    "pending-operator": 0,
                    "acquiring-lock": 0,
                    "deploying": 0,
                    "succeeded": 3,
                    "failed": 0,
                    "abandoned": 0,
                },
            },
            "relationships": {
                "stack-deployment-group": {
                    "data": {"id": "sdg-xyz789", "type": "stack-deployment-groups"}
                }
            },
        }

    # ── Model tests ──────────────────────────────────────────────────────────

    def test_stack_deployment_group_status_counts_parse(self):
        """StackDeploymentGroupStatusCounts parses all count fields."""
        counts_data = {
            "pending": 1,
            "pre-deploying": 2,
            "pending-operator": 3,
            "acquiring-lock": 4,
            "deploying": 5,
            "succeeded": 6,
            "failed": 7,
            "abandoned": 8,
        }
        counts = StackDeploymentGroupStatusCounts.model_validate(counts_data)
        assert counts.pending == 1
        assert counts.pre_deploying == 2
        assert counts.pre_deploying_pending_operator == 3
        assert counts.acquiring_lock == 4
        assert counts.deploying == 5
        assert counts.succeeded == 6
        assert counts.failed == 7
        assert counts.abandoned == 8

    def test_stack_deployment_group_summary_parse(self, summary_api_data):
        """StackDeploymentGroupSummary parses name and status correctly."""
        attrs = dict(summary_api_data["attributes"])
        attrs["id"] = summary_api_data["id"]
        summary = StackDeploymentGroupSummary.model_validate(attrs)
        assert summary.id == "sdgs-abc123"
        assert summary.name == "dev"
        assert summary.status == "succeeded"
        assert isinstance(summary.status_counts, StackDeploymentGroupStatusCounts)
        assert summary.status_counts.succeeded == 3

    def test_summary_list_options_serialization(self):
        """StackDeploymentGroupSummaryListOptions serializes page[size] correctly."""
        opts = StackDeploymentGroupSummaryListOptions(page_size=25)
        dumped = opts.model_dump(by_alias=True, exclude_none=True)
        assert dumped["page[size]"] == 25

    # ── list() tests ─────────────────────────────────────────────────────────

    def test_list_invalid_configuration_id_raises(self, service):
        """list() with an empty config ID raises InvalidStackConfigurationIDError."""
        with pytest.raises(InvalidStackConfigurationIDError):
            list(service.list(""))

    def test_list_success(self, service, summary_api_data):
        """list() yields StackDeploymentGroupSummary objects from paginated results."""
        service._list = Mock(return_value=[summary_api_data])

        results = list(service.list("stc-abc123"))

        service._list.assert_called_once_with(
            path="/api/v2/stack-configurations/stc-abc123/stack-deployment-group-summaries",
            params={},
        )
        assert len(results) == 1
        assert isinstance(results[0], StackDeploymentGroupSummary)
        assert results[0].id == "sdgs-abc123"
        assert results[0].name == "dev"

    def test_list_with_page_size(self, service, summary_api_data):
        """list() passes page[size] param correctly."""
        service._list = Mock(return_value=[summary_api_data])
        opts = StackDeploymentGroupSummaryListOptions(page_size=10)
        list(service.list("stc-abc123", options=opts))
        service._list.assert_called_once_with(
            path="/api/v2/stack-configurations/stc-abc123/stack-deployment-group-summaries",
            params={"page[size]": 10},
        )

    def test_list_hydrates_group_relation(self, service, summary_api_data):
        """list() hydrates the stack-deployment-group relation as a typed stub."""
        service._list = Mock(return_value=[summary_api_data])
        results = list(service.list("stc-abc123"))
        assert isinstance(results[0].stack_deployment_group, StackDeploymentGroup)
        assert results[0].stack_deployment_group.id == "sdg-xyz789"

    def test_list_empty(self, service):
        """list() returns an empty iterator when the API returns no items."""
        service._list = Mock(return_value=[])
        assert list(service.list("stc-abc123")) == []
