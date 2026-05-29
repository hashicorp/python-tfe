# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ..errors import RequiredCommentBodyError
from ..utils import valid_string


class Comment(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True, validate_by_name=True, extra="allow"
    )

    id: str
    body: str = Field(default="", alias="body")


class CommentCreateOptions(BaseModel):
    """Options for creating a comment on a run."""

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    body: str = Field(alias="body")

    @model_validator(mode="after")
    def valid(self) -> CommentCreateOptions:
        if not valid_string(self.body):
            raise RequiredCommentBodyError()
        return self
