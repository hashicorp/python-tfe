from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from .comment import Comment
from .user import User


class RunEventIncludeOpt(str, Enum):
    RUN_EVENT_ACTOR = "actor"
    RUN_EVENT_COMMENT = "comment"


class RunEvent(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    id: str
    action: str | None = Field(None, alias="action")
    created_at: datetime | None = Field(None, alias="created-at")
    description: str | None = Field(None, alias="description")

    # Relations - Note that `target` is not supported yet
    actor: User | None = Field(None, alias="actor")
    comment: Comment | None = Field(None, alias="comment")


class RunEventList(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    items: list[RunEvent] = Field(default_factory=list)
    current_page: int | None = None
    total_pages: int | None = None
    prev_page: int | None = None
    next_page: int | None = None
    total_count: int | None = None


class RunEventListOptions(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    include: list[RunEventIncludeOpt] | None = Field(None, alias="include")


class RunEventReadOptions(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    include: list[RunEventIncludeOpt] | None = Field(None, alias="include")
