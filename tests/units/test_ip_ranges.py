# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""Unit tests for the IP ranges resource."""

from datetime import datetime, timezone
from unittest.mock import Mock

import pytest

from pytfe._http import HTTPTransport
from pytfe.models.ip_range import IPRange
from pytfe.resources.ip_ranges import IPRanges


class TestIPRanges:
    """Test the IPRanges service class."""

    @pytest.fixture
    def mock_transport(self):
        return Mock(spec=HTTPTransport)

    @pytest.fixture
    def service(self, mock_transport):
        return IPRanges(mock_transport)

    @pytest.fixture
    def ip_ranges_payload(self):
        return {
            "api": ["75.2.98.97/32", "99.83.150.238/32"],
            "notifications": ["10.0.0.1/32"],
            "sentinel": ["192.168.0.1/32"],
            "vcs": ["172.16.0.1/32"],
        }

    def test_read_success(self, service, mock_transport, ip_ranges_payload):
        """read() GETs /api/meta/ip-ranges and parses the bare JSON body."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = ip_ranges_payload
        mock_transport.request.return_value = mock_response

        result = service.read()

        mock_transport.request.assert_called_once_with(
            "GET",
            "/api/meta/ip-ranges",
            headers={"Accept": "application/json, */*"},
            allow_redirects=False,
        )
        assert isinstance(result, IPRange)
        assert result.api == ["75.2.98.97/32", "99.83.150.238/32"]
        assert result.notifications == ["10.0.0.1/32"]
        assert result.sentinel == ["192.168.0.1/32"]
        assert result.vcs == ["172.16.0.1/32"]

    def test_read_not_modified_returns_none(self, service, mock_transport):
        """A 304 Not Modified response maps to None."""
        mock_response = Mock()
        mock_response.status_code = 304
        mock_transport.request.return_value = mock_response

        result = service.read(
            modified_since=datetime(2020, 5, 26, 15, 10, 5, tzinfo=timezone.utc)
        )

        assert result is None

    def test_read_sends_if_modified_since_header(
        self, service, mock_transport, ip_ranges_payload
    ):
        """A modified_since datetime is sent as an RFC1123 If-Modified-Since header."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = ip_ranges_payload
        mock_transport.request.return_value = mock_response

        service.read(
            modified_since=datetime(2020, 5, 26, 15, 10, 5, tzinfo=timezone.utc)
        )

        _, kwargs = mock_transport.request.call_args
        assert kwargs["headers"]["If-Modified-Since"] == "Tue, 26 May 2020 15:10:05 GMT"

    def test_read_naive_datetime_is_treated_as_utc(
        self, service, mock_transport, ip_ranges_payload
    ):
        """A naive datetime is assumed to be UTC when building the header."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = ip_ranges_payload
        mock_transport.request.return_value = mock_response

        service.read(modified_since=datetime(2020, 5, 26, 15, 10, 5))

        _, kwargs = mock_transport.request.call_args
        assert kwargs["headers"]["If-Modified-Since"] == "Tue, 26 May 2020 15:10:05 GMT"
