"""Test cases for Apply resources."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from pytfe.errors import InvalidApplyIDError
from pytfe.models.apply import Apply
from pytfe.resources.apply import Applies


class TestApplies(unittest.TestCase):
    def setUp(self):
        self.mock_transport = MagicMock()
        self.applies = Applies(self.mock_transport)

    def test_applies_service_init(self):
        """Test that the applies service initializes correctly."""
        assert self.applies.t == self.mock_transport

    def test_read_apply_validation_errors(self):
        """Test apply read with invalid IDs."""
        with self.assertRaises(InvalidApplyIDError):
            self.applies.read("")

        with self.assertRaises(InvalidApplyIDError):
            self.applies.read("! / nope")  # Contains spaces and slashes

    def test_read_apply_success(self):
        """Test successful apply read."""
        # Mock the transport response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": {
                "id": "apply-123",
                "attributes": {
                    "status": "finished",
                    "resource-additions": 2,
                    "resource-changes": 1,
                    "resource-destructions": 0,
                    "resource-imports": 0,
                    "created-at": "2023-01-01T00:00:00Z",
                    "log-read-url": "https://app.terraform.io/api/v2/applies/apply-123/logs",
                    "status-timestamps": {},
                },
            }
        }
        self.mock_transport.request.return_value = mock_response

        # Call the method
        result = self.applies.read("apply-123")

        # Verify the request was made correctly
        self.mock_transport.request.assert_called_once_with(
            "GET", "/api/v2/applies/apply-123"
        )

        # Verify the result
        assert isinstance(result, Apply)
        assert result.id == "apply-123"
        assert result.status == "finished"
        assert result.resource_additions == 2
        assert result.resource_changes == 1
        assert result.resource_destructions == 0
        assert result.resource_imports == 0

    @patch("pytfe.resources.apply.Applies.read")
    def test_logs_success(self, mock_read):
        """Test successful logs retrieval."""
        # Mock the apply object
        mock_apply = MagicMock()
        mock_apply.log_read_url = (
            "https://app.terraform.io/api/v2/applies/apply-123/logs"
        )
        mock_read.return_value = mock_apply

        # Call the method
        result = self.applies.logs("apply-123")

        # Verify it returns empty string (placeholder implementation)
        assert result == ""

    @patch("pytfe.resources.apply.Applies.read")
    def test_logs_no_url_error(self, mock_read):
        """Test logs method when apply has no log URL."""
        # Mock apply with no log URL
        mock_apply = MagicMock()
        mock_apply.log_read_url = None
        mock_read.return_value = mock_apply

        # Call the method and expect error
        with self.assertRaises(ValueError) as cm:
            self.applies.logs("apply-123")

        assert "Apply apply-123 does not have a log URL" in str(cm.exception)
