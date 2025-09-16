from __future__ import annotations

from typing import Any, List, Optional

from pydantic import BaseModel, Field, ConfigDict


class StateVersionOutput(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    id: str
    name: str
    sensitive: bool
    type: str
    value: Any
    detailed_type: Optional[Any] = Field(None, alias="detailed-type")


class StateVersionOutputsListOptions(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    page_number: Optional[int] = Field(None, alias="page[number]")
    page_size: Optional[int] = Field(None, alias="page[size]")


class StateVersionOutputsList(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    items: List[StateVersionOutput] = Field(default_factory=list)
    current_page: Optional[int] = None
    total_pages: Optional[int] = None
    total_count: Optional[int] = None
