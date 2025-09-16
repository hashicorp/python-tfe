from __future__ import annotations

from pydantic import BaseModel

__all__ = [
    "Capacity",
]


class Capacity(BaseModel):
    organization: str
    pending: int
    running: int