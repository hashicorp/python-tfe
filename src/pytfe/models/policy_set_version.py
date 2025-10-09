from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class PolicySetVersion(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    id: str
    error: str | None = Field(None, alias="error")
