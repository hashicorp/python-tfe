# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""Unit tests for the assessment results resource."""

from unittest.mock import Mock

import pytest

from pytfe._http import HTTPTransport
from pytfe.errors import InvalidAssessmentResultIDError
from pytfe.models.assessment_result import AssessmentResult
from pytfe.resources.assessment_result import AssessmentResults


class TestAssessmentResults:
    @pytest.fixture
    def mock_transport(self):
        return Mock(spec=HTTPTransport)

    @pytest.fixture
    def service(self, mock_transport):
        return AssessmentResults(mock_transport)

    @pytest.fixture
    def api_data(self):
        return {
            "id": "asmtres-UG5rE9L1373hMYMA",
            "type": "assessment-results",
            "attributes": {
                "drifted": True,
                "succeeded": True,
                "error-message": None,
                "created-at": "2022-07-02T22:29:58+00:00",
            },
            "relationships": {
                "workspace": {"data": {"id": "ws-1", "type": "workspaces"}}
            },
        }

    # ── read ──────────────────────────────────────────────────────────────────

    def test_read_success(self, service, mock_transport, api_data):
        mock_response = Mock()
        mock_response.json.return_value = {"data": api_data}
        mock_transport.request.return_value = mock_response

        result = service.read("asmtres-UG5rE9L1373hMYMA")

        mock_transport.request.assert_called_once_with(
            "GET", "/api/v2/assessment-results/asmtres-UG5rE9L1373hMYMA"
        )
        assert isinstance(result, AssessmentResult)
        assert result.id == "asmtres-UG5rE9L1373hMYMA"
        assert result.drifted is True
        assert result.succeeded is True
        assert result.error_message is None
        assert result.related("workspace") == [{"id": "ws-1", "type": "workspaces"}]

    def test_read_invalid_id(self, service):
        with pytest.raises(InvalidAssessmentResultIDError):
            service.read("not valid!")

    # ── json_output / json_schema (blob redirect) ─────────────────────────────

    def test_json_output_follows_redirect(self, service, mock_transport):
        redirect = Mock()
        redirect.status_code = 307
        redirect.headers = {"Location": "https://archivist.example/blob?sig=abc"}
        blob = Mock()
        blob.status_code = 200
        blob.json.return_value = {"format_version": "1.2", "planned_values": {}}
        mock_transport.request.side_effect = [redirect, blob]

        result = service.json_output("asmtres-1")

        assert result == {"format_version": "1.2", "planned_values": {}}
        first, second = mock_transport.request.call_args_list
        assert first.args == (
            "GET",
            "/api/v2/assessment-results/asmtres-1/json-output",
        )
        assert first.kwargs == {"allow_redirects": False}
        assert second.args == ("GET", "https://archivist.example/blob?sig=abc")

    def test_json_output_204_returns_none(self, service, mock_transport):
        resp = Mock()
        resp.status_code = 204
        mock_transport.request.return_value = resp
        assert service.json_output("asmtres-1") is None

    def test_json_output_inline_body(self, service, mock_transport):
        resp = Mock()
        resp.status_code = 200
        resp.json.return_value = {"format_version": "1.1"}
        mock_transport.request.return_value = resp
        assert service.json_output("asmtres-1") == {"format_version": "1.1"}

    def test_json_schema_follows_redirect(self, service, mock_transport):
        redirect = Mock()
        redirect.status_code = 307
        redirect.headers = {"Location": "https://archivist.example/schema"}
        blob = Mock()
        blob.status_code = 200
        blob.json.return_value = {"provider_schemas": {}}
        mock_transport.request.side_effect = [redirect, blob]

        result = service.json_schema("asmtres-1")

        assert result == {"provider_schemas": {}}
        assert mock_transport.request.call_args_list[0].args == (
            "GET",
            "/api/v2/assessment-results/asmtres-1/json-schema",
        )

    def test_json_output_invalid_id(self, service):
        with pytest.raises(InvalidAssessmentResultIDError):
            service.json_output("")

    def test_json_schema_invalid_id(self, service):
        with pytest.raises(InvalidAssessmentResultIDError):
            service.json_schema("")

    # ── log_output ────────────────────────────────────────────────────────────

    def test_log_output_text(self, service, mock_transport):
        resp = Mock()
        resp.status_code = 200
        resp.text = '{"@level":"info"}\n{"@level":"info"}'
        mock_transport.request.return_value = resp

        result = service.log_output("asmtres-1")

        assert result == '{"@level":"info"}\n{"@level":"info"}'
        assert mock_transport.request.call_args.args == (
            "GET",
            "/api/v2/assessment-results/asmtres-1/log-output",
        )

    def test_log_output_204_returns_empty(self, service, mock_transport):
        resp = Mock()
        resp.status_code = 204
        mock_transport.request.return_value = resp
        assert service.log_output("asmtres-1") == ""

    def test_log_output_invalid_id(self, service):
        with pytest.raises(InvalidAssessmentResultIDError):
            service.log_output("")
