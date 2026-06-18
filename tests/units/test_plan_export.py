# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""Unit tests for the plan exports resource."""

from unittest.mock import Mock

import pytest

from pytfe._http import HTTPTransport
from pytfe.errors import InvalidPlanExportIDError, RequiredPlanError
from pytfe.models.plan_export import (
    PlanExport,
    PlanExportCreateOptions,
    PlanExportDataType,
    PlanExportStatus,
)
from pytfe.resources.plan_export import PlanExports


class TestPlanExports:
    """Test the PlanExports service class."""

    @pytest.fixture
    def mock_transport(self):
        return Mock(spec=HTTPTransport)

    @pytest.fixture
    def service(self, mock_transport):
        return PlanExports(mock_transport)

    @pytest.fixture
    def plan_export_api_data(self):
        return {
            "id": "pe-3yVQZvHzf5j3WRJ1",
            "type": "plan-exports",
            "attributes": {
                "data-type": "sentinel-mock-bundle-v0",
                "status": "finished",
                "status-timestamps": {
                    "queued-at": "2019-03-04T22:29:53+00:00",
                    "finished-at": "2019-03-04T22:29:58+00:00",
                    "expired-at": "2019-03-04T23:29:58+00:00",
                },
            },
            "relationships": {
                "plan": {"data": {"id": "plan-8F5JFydVYAmtTjET", "type": "plans"}}
            },
        }

    # ── Model / options tests ─────────────────────────────────────────────────

    def test_create_options_defaults_data_type(self):
        """data_type defaults to the only supported export format."""
        opts = PlanExportCreateOptions(plan_id="plan-abc123")
        assert opts.plan_id == "plan-abc123"
        assert opts.data_type == PlanExportDataType.SENTINEL_MOCK_BUNDLE_V0

    def test_create_options_invalid_plan_raises(self):
        """An empty plan_id raises RequiredPlanError at construction."""
        with pytest.raises(RequiredPlanError):
            PlanExportCreateOptions(plan_id="")

    # ── Resource method tests ─────────────────────────────────────────────────

    def test_create_success(self, service, mock_transport, plan_export_api_data):
        """create() POSTs the JSON:API payload and returns a PlanExport."""
        mock_response = Mock()
        mock_response.json.return_value = {"data": plan_export_api_data}
        mock_transport.request.return_value = mock_response

        opts = PlanExportCreateOptions(plan_id="plan-8F5JFydVYAmtTjET")
        result = service.create(opts)

        mock_transport.request.assert_called_once_with(
            "POST",
            "/api/v2/plan-exports",
            json_body={
                "data": {
                    "type": "plan-exports",
                    "attributes": {"data-type": "sentinel-mock-bundle-v0"},
                    "relationships": {
                        "plan": {
                            "data": {"type": "plans", "id": "plan-8F5JFydVYAmtTjET"}
                        }
                    },
                }
            },
        )
        assert isinstance(result, PlanExport)
        assert result.id == "pe-3yVQZvHzf5j3WRJ1"
        assert result.data_type == PlanExportDataType.SENTINEL_MOCK_BUNDLE_V0
        assert result.status == PlanExportStatus.FINISHED

    def test_read_success(self, service, mock_transport, plan_export_api_data):
        """read() GETs the correct path and returns a PlanExport."""
        mock_response = Mock()
        mock_response.json.return_value = {"data": plan_export_api_data}
        mock_transport.request.return_value = mock_response

        result = service.read("pe-3yVQZvHzf5j3WRJ1")

        mock_transport.request.assert_called_once_with(
            "GET", "/api/v2/plan-exports/pe-3yVQZvHzf5j3WRJ1"
        )
        assert isinstance(result, PlanExport)
        assert result.id == "pe-3yVQZvHzf5j3WRJ1"
        assert result.status_timestamps is not None
        assert result.status_timestamps.expired_at is not None
        # The plan relationship is captured losslessly via TFEModel.
        assert result.related("plan") == [
            {"id": "plan-8F5JFydVYAmtTjET", "type": "plans"}
        ]

    def test_read_invalid_id(self, service):
        with pytest.raises(InvalidPlanExportIDError):
            service.read("not valid!")

    def test_delete_success(self, service, mock_transport):
        """delete() issues a DELETE to the correct path."""
        mock_transport.request.return_value = Mock()

        service.delete("pe-3yVQZvHzf5j3WRJ1")

        mock_transport.request.assert_called_once_with(
            "DELETE", "/api/v2/plan-exports/pe-3yVQZvHzf5j3WRJ1"
        )

    def test_delete_invalid_id(self, service):
        with pytest.raises(InvalidPlanExportIDError):
            service.delete("")

    def test_download_follows_redirect_without_auth(self, service, mock_transport):
        """download() follows the 302 to the presigned URL without forwarding auth."""
        redirect_resp = Mock()
        redirect_resp.status_code = 302
        redirect_resp.headers = {"Location": "https://blob.example/export.tar.gz?sig=x"}
        blob_resp = Mock()
        blob_resp.status_code = 200
        blob_resp.content = b"tarball-bytes"
        mock_transport.request.side_effect = [redirect_resp, blob_resp]

        result = service.download("pe-3yVQZvHzf5j3WRJ1")

        assert result == b"tarball-bytes"
        assert mock_transport.request.call_count == 2
        first_call, second_call = mock_transport.request.call_args_list
        assert first_call.args == (
            "GET",
            "/api/v2/plan-exports/pe-3yVQZvHzf5j3WRJ1/download",
        )
        assert first_call.kwargs == {"allow_redirects": False}
        assert second_call.args == ("GET", "https://blob.example/export.tar.gz?sig=x")
        assert second_call.kwargs == {"include_auth": False}

    def test_download_inline_content(self, service, mock_transport):
        """download() returns the body directly when there is no redirect."""
        resp = Mock()
        resp.status_code = 200
        resp.content = b"inline-bytes"
        mock_transport.request.return_value = resp

        result = service.download("pe-3yVQZvHzf5j3WRJ1")

        assert result == b"inline-bytes"

    def test_download_invalid_id(self, service):
        with pytest.raises(InvalidPlanExportIDError):
            service.download("")
