from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from .run import Run


# PolicyCheck represents a Terraform Enterprise policy check..
class PolicyCheck(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    id: str
    # actions: PolicyActions = Field(..., alias="actions")
    # permissions: PolicyPermissions = Field(..., alias="permissions")
    # result: PolicyResult = Field(..., alias="result")
    # scope: PolicyScope = Field(..., alias="scope")
    # status: PolicyStatus = Field(..., alias="status")
    # status_timestamps: PolicyStatusTimestamps = Field(..., alias="status-timestamps")

    # Relations
    run: Run = Field(..., alias="run")
