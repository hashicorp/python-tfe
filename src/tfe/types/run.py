from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from .pagination import Pagination

__all__ = [
    "RunStatus",
    "Run",
    "RunQueue", 
    "ReadRunQueueOptions",
]


class RunStatus(str, Enum):
    PLANNING = "planning"
    PLANNED = "planned"
    APPLIED = "applied"
    CANCELED = "canceled"
    ERRORED = "errored"


class Run(BaseModel):
    id: str
    status: RunStatus
    # Add other Run fields as needed


class RunQueue(BaseModel):
    pagination: Pagination | None = None
    items: list[Run] = Field(default_factory=list)


class ReadRunQueueOptions(BaseModel):
    # List options for pagination
    page_number: int | None = None
    page_size: int | None = None