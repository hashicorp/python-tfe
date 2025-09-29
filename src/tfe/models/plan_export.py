from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class PlanExport(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    id: str
