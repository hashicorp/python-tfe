from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from .user import User

# from .comment import Comment


class RunEvent(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    id: str
    # action: RunEventAction = Field(..., alias="action")
    created_at: datetime = Field(..., alias="created-at")
    description: str = Field(..., alias="description")

    # Relations - Note that `target` is not supported yet
    actor: User = Field(..., alias="actor")
    # comment: Comment | None = Field(None, alias="comment")
