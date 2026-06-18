# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""Unit tests for the cost estimates resource."""

from unittest.mock import Mock

import pytest

from pytfe._http import HTTPTransport
from pytfe.errors import InvalidCostEstimateIDError
from pytfe.models.cost_estimate import CostEstimate, CostEstimateStatus
from pytfe.resources.cost_estimate import CostEstimates


class TestCostEstimates:
    """Test the CostEstimates service class."""

    @pytest.fixture
    def mock_transport(self):
        return Mock(spec=HTTPTransport)

    @pytest.fixture
    def service(self, mock_transport):
        return CostEstimates(mock_transport)

    @pytest.fixture
    def cost_estimate_attrs(self):
        # Mirrors the documented response: error-message is null and only the
        # timestamps that have occurred are present.
        return {
            "error-message": None,
            "status": "finished",
            "status-timestamps": {
                "queued-at": "2017-11-29T20:02:17+00:00",
                "finished-at": "2017-11-29T20:02:20+00:00",
            },
            "resources-count": 4,
            "matched-resources-count": 3,
            "unmatched-resources-count": 1,
            "prior-monthly-cost": "0.0",
            "proposed-monthly-cost": "25.488",
            "delta-monthly-cost": "25.488",
        }

    # ── Model tests ───────────────────────────────────────────────────────────

    def test_model_parses_partial_timestamps_and_null_error(self, cost_estimate_attrs):
        """CostEstimate tolerates null error-message and partial status-timestamps."""
        ce = CostEstimate.model_validate({"id": "ce-1", **cost_estimate_attrs})
        assert ce.id == "ce-1"
        assert ce.error_message is None
        assert ce.status == CostEstimateStatus.Cost_Estimate_Finished
        assert ce.status_timestamps is not None
        assert ce.status_timestamps.finished_at is not None
        assert ce.status_timestamps.canceled_at is None

    # ── Resource method tests ─────────────────────────────────────────────────

    def test_read_success(self, service, mock_transport, cost_estimate_attrs):
        """read() GETs the correct path and returns a CostEstimate."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {
                "id": "ce-BPvFFrYCqRV6qVBK",
                "type": "cost-estimates",
                "attributes": cost_estimate_attrs,
            }
        }
        mock_transport.request.return_value = mock_response

        result = service.read("ce-BPvFFrYCqRV6qVBK")

        mock_transport.request.assert_called_once_with(
            "GET", "/api/v2/cost-estimates/ce-BPvFFrYCqRV6qVBK"
        )
        assert isinstance(result, CostEstimate)
        assert result.id == "ce-BPvFFrYCqRV6qVBK"
        assert result.proposed_monthly_cost == "25.488"
        assert result.resources_count == 4

    def test_read_accepts_array_envelope(
        self, service, mock_transport, cost_estimate_attrs
    ):
        """read() also handles the array-wrapped envelope shown in the docs."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [
                {
                    "id": "ce-BPvFFrYCqRV6qVBK",
                    "type": "cost-estimates",
                    "attributes": cost_estimate_attrs,
                }
            ]
        }
        mock_transport.request.return_value = mock_response

        result = service.read("ce-BPvFFrYCqRV6qVBK")

        assert isinstance(result, CostEstimate)
        assert result.id == "ce-BPvFFrYCqRV6qVBK"

    def test_read_invalid_id(self, service):
        with pytest.raises(InvalidCostEstimateIDError):
            service.read("not valid!")

    def test_logs_success(self, service, mock_transport):
        """logs() GETs the /output endpoint and returns its text."""
        mock_response = Mock()
        mock_response.text = "cost estimation log output"
        mock_transport.request.return_value = mock_response

        result = service.logs("ce-BPvFFrYCqRV6qVBK")

        mock_transport.request.assert_called_once_with(
            "GET", "/api/v2/cost-estimates/ce-BPvFFrYCqRV6qVBK/output"
        )
        assert result == "cost estimation log output"

    def test_logs_invalid_id(self, service):
        with pytest.raises(InvalidCostEstimateIDError):
            service.logs("")
