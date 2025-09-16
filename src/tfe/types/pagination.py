from __future__ import annotations

from pydantic import BaseModel

__all__ = [
    "Pagination",
]


class Pagination(BaseModel):
    current_page: int
    total_count: int
    # Add other pagination fields as needed