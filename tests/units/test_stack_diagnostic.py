# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""Unit tests for the stack_diagnostics module."""

from unittest.mock import Mock

import pytest

from pytfe._http import HTTPTransport
from pytfe.errors import InvalidStackDiagnosticIDError
from pytfe.models.stack_deployment_step import StackDiagnostic
from pytfe.resources.stack_diagnostics import StackDiagnostics


class TestStackDiagnostics:
    """Test the StackDiagnostics service class."""

    @pytest.fixture
    def mock_transport(self):
        """Create a mock HTTPTransport."""
        return Mock(spec=HTTPTransport)

    @pytest.fixture
    def service(self, mock_transport):
        """Create a StackDiagnostics service with mocked transport."""
        return StackDiagnostics(mock_transport)

    @pytest.fixture
    def diagnostic_api_data(self):
        """Typical API response data for a single stack diagnostic."""
        return {
            "id": "std-abc123",
            "type": "stack-diagnostics",
            "attributes": {
                "severity": "error",
                "summary": "Invalid configuration",
                "detail": "The stack configuration failed validation.",
                "diags": None,
                "acknowledged": False,
                "acknowledged-at": None,
                "created-at": "2026-07-03T10:00:00.000Z",
            },
        }

    # ── Model tests ──────────────────────────────────────────────────────────

    def test_stack_diagnostic_parse(self, diagnostic_api_data):
        """StackDiagnostic parses all attributes correctly."""
        attrs = dict(diagnostic_api_data["attributes"])
        attrs["id"] = diagnostic_api_data["id"]
        diag = StackDiagnostic.model_validate(attrs)
        assert diag.id == "std-abc123"
        assert diag.severity == "error"
        assert diag.summary == "Invalid configuration"
        assert diag.acknowledged is False

    # ── read() tests ─────────────────────────────────────────────────────────

    def test_read_invalid_id_raises(self, service):
        """read() with an empty ID raises InvalidStackDiagnosticIDError."""
        with pytest.raises(InvalidStackDiagnosticIDError):
            service.read("")

    def test_read_success(self, service, mock_transport, diagnostic_api_data):
        """read() fetches a single stack diagnostic by ID."""
        mock_response = Mock()
        mock_response.json.return_value = {"data": diagnostic_api_data}
        mock_transport.request.return_value = mock_response

        diag = service.read("std-abc123")

        mock_transport.request.assert_called_once_with(
            "GET", path="/api/v2/stack-diagnostics/std-abc123"
        )
        assert isinstance(diag, StackDiagnostic)
        assert diag.id == "std-abc123"
        assert diag.severity == "error"
        assert diag.acknowledged is False

    # ── acknowledge() tests ───────────────────────────────────────────────────

    def test_acknowledge_invalid_id_raises(self, service):
        """acknowledge() with an empty ID raises InvalidStackDiagnosticIDError."""
        with pytest.raises(InvalidStackDiagnosticIDError):
            service.acknowledge("")

    def test_acknowledge_calls_correct_endpoint(self, service, mock_transport):
        """acknowledge() POSTs to the acknowledge action endpoint."""
        mock_transport.request.return_value = Mock()
        service.acknowledge("std-abc123")
        mock_transport.request.assert_called_once_with(
            "POST",
            path="/api/v2/stack-diagnostics/std-abc123/acknowledge",
        )

    def test_acknowledge_returns_none(self, service, mock_transport):
        """acknowledge() returns None on success."""
        mock_transport.request.return_value = Mock()
        result = service.acknowledge("std-abc123")
        assert result is None
