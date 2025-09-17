from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class StateVersionOutput(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    id: str
    name: str
    sensitive: bool
    type: str
    value: Any
    detailed_type: Any | None = Field(None, alias="detailed-type")


class StateVersionOutputsListOptions(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    page_number: int | None = Field(None, alias="page[number]")
    page_size: int | None = Field(None, alias="page[size]")


class StateVersionOutputsList(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    items: list[StateVersionOutput] = Field(default_factory=list)
    current_page: int | None = None
    total_pages: int | None = None
    total_count: int | None = None
