# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""Unit tests for the comment module."""

from unittest.mock import Mock

import pytest

from pytfe._http import HTTPTransport
from pytfe.errors import (
    InvalidCommentIDError,
    InvalidRunIDError,
    RequiredCommentBodyError,
)
from pytfe.models.comment import Comment, CommentCreateOptions
from pytfe.resources.comment import Comments


class TestComments:
    """Test the Comments service class."""

    @pytest.fixture
    def mock_transport(self):
        """Create a mock HTTPTransport."""
        return Mock(spec=HTTPTransport)

    @pytest.fixture
    def service(self, mock_transport):
        """Create a Comments service with mocked transport."""
        return Comments(mock_transport)

    @pytest.fixture
    def comment_api_data(self):
        """Typical API response for a single comment."""
        return {
            "id": "com-abc123",
            "type": "comments",
            "attributes": {
                "body": "This is a test comment.",
            },
        }

    # ── Model tests ──────────────────────────────────────────────────────────

    def test_create_options_valid(self):
        """CommentCreateOptions accepts a valid body."""
        opts = CommentCreateOptions(body="Hello world")
        assert opts.body == "Hello world"

    def test_create_options_empty_body_raises(self):
        """CommentCreateOptions raises RequiredCommentBodyError when body is empty."""
        with pytest.raises(RequiredCommentBodyError):
            CommentCreateOptions(body="")

    def test_create_options_serializes_with_alias(self):
        """CommentCreateOptions serialises using the API alias."""
        opts = CommentCreateOptions(body="My comment")
        dumped = opts.model_dump(by_alias=True, exclude_none=True)
        assert dumped == {"body": "My comment"}

    def test_comment_model_fields(self):
        """Comment model stores id and body."""
        c = Comment(id="com-123", body="test")
        assert c.id == "com-123"
        assert c.body == "test"

    def test_comment_model_default_body(self):
        """Comment body defaults to empty string."""
        c = Comment(id="com-123")
        assert c.body == ""

    # ── Parser tests ─────────────────────────────────────────────────────────

    def test_comment_from_full_data(self, service, comment_api_data):
        """_comment_from parses id and body from API data."""
        result = service._comment_from(comment_api_data)

        assert isinstance(result, Comment)
        assert result.id == "com-abc123"
        assert result.body == "This is a test comment."

    def test_comment_from_missing_body(self, service):
        """_comment_from handles missing body attribute gracefully."""
        data = {"id": "com-xyz", "attributes": {}}
        result = service._comment_from(data)

        assert result.id == "com-xyz"
        assert result.body == ""

    # ── Resource method tests ─────────────────────────────────────────────────

    def test_list_success(self, service, comment_api_data):
        """list() yields Comment objects from paginated results."""
        service._list = Mock(return_value=[comment_api_data])

        results = list(service.list(run_id="run-abc123"))

        service._list.assert_called_once_with(path="/api/v2/runs/run-abc123/comments")
        assert len(results) == 1
        assert isinstance(results[0], Comment)
        assert results[0].id == "com-abc123"
        assert results[0].body == "This is a test comment."

    def test_list_empty(self, service):
        """list() returns empty iterator when no comments exist."""
        service._list = Mock(return_value=[])

        results = list(service.list(run_id="run-abc123"))
        assert results == []

    def test_list_invalid_run_id(self, service):
        """list() raises InvalidRunIDError for a bad run ID."""
        with pytest.raises(InvalidRunIDError):
            list(service.list(run_id="not valid!"))

    def test_read_success(self, service, mock_transport, comment_api_data):
        """read() GETs the correct path and returns a Comment."""
        mock_response = Mock()
        mock_response.json.return_value = {"data": comment_api_data}
        mock_transport.request.return_value = mock_response

        result = service.read(comment_id="com-abc123")

        mock_transport.request.assert_called_once_with(
            "GET", path="/api/v2/comments/com-abc123"
        )
        assert isinstance(result, Comment)
        assert result.id == "com-abc123"
        assert result.body == "This is a test comment."

    def test_read_invalid_comment_id(self, service):
        """read() raises InvalidCommentIDError for a bad comment ID."""
        with pytest.raises(InvalidCommentIDError):
            service.read(comment_id="not valid!")

    def test_create_success(self, service, mock_transport, comment_api_data):
        """create() POSTs the correct payload and returns a Comment."""
        mock_response = Mock()
        mock_response.json.return_value = {"data": comment_api_data}
        mock_transport.request.return_value = mock_response

        opts = CommentCreateOptions(body="This is a test comment.")
        result = service.create(run_id="run-abc123", options=opts)

        mock_transport.request.assert_called_once_with(
            "POST",
            path="/api/v2/runs/run-abc123/comments",
            json_body={
                "data": {
                    "type": "comments",
                    "attributes": {"body": "This is a test comment."},
                }
            },
        )
        assert isinstance(result, Comment)
        assert result.id == "com-abc123"
        assert result.body == "This is a test comment."

    def test_create_invalid_run_id(self, service):
        """create() raises InvalidRunIDError for a bad run ID."""
        opts = CommentCreateOptions(body="Hello")
        with pytest.raises(InvalidRunIDError):
            service.create(run_id="not valid!", options=opts)
