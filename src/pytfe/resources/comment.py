# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from ..errors import InvalidCommentIDError, InvalidRunIDError
from ..models.comment import Comment, CommentCreateOptions
from ..utils import valid_string_id
from ._base import _Service


class Comments(_Service):
    """Service for managing run comments."""

    def list(self, run_id: str) -> Iterator[Comment]:
        """List all comments for the given run."""
        if not valid_string_id(run_id):
            raise InvalidRunIDError()
        path = f"/api/v2/runs/{run_id}/comments"
        for item in self._list(path=path):
            yield self._comment_from(item)

    def read(self, comment_id: str) -> Comment:
        """Read a comment by its ID."""
        if not valid_string_id(comment_id):
            raise InvalidCommentIDError()
        r = self.t.request("GET", path=f"/api/v2/comments/{comment_id}")
        data = r.json().get("data", {})
        return self._comment_from(data)

    def create(self, run_id: str, options: CommentCreateOptions) -> Comment:
        """Create a new comment on the given run."""
        if not valid_string_id(run_id):
            raise InvalidRunIDError()
        payload = {
            "data": {
                "type": "comments",
                "attributes": options.model_dump(by_alias=True, exclude_none=True),
            }
        }
        r = self.t.request(
            "POST", path=f"/api/v2/runs/{run_id}/comments", json_body=payload
        )
        data = r.json().get("data", {})
        return self._comment_from(data)

    def _comment_from(self, data: dict[str, Any]) -> Comment:
        """Parse a Comment from API response data."""
        attrs = dict(data.get("attributes", {}))
        attrs["id"] = data.get("id")
        return Comment.model_validate(attrs)
