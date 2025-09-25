from __future__ import annotations

from pydantic import BaseModel, ConfigDict


# TaskStage represents a HCP Terraform or Terraform Enterprise run's stage where run tasks can occur
class TaskStage(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    id: str
    # stage: Stage = Field(..., alias="stage")
    # status: TaskStageStatus = Field(..., alias="status")
    # status_timestamps: TaskStageStatusTimestamps = Field(..., alias="status-timestamps")
    # created_at: datetime = Field(..., alias="created-at")
    # updated_at: datetime = Field(..., alias="updated-at")
    # permissions: Permissions = Field(..., alias="permissions")
    # actions: Actions = Field(..., alias="actions")

    # # Relations
    # run: Run = Field(..., alias="run")
    # task_results: list[TaskResult] = Field(..., alias="task-results")
    # policy_evaluations: list[PolicyEvaluation] = Field(..., alias="policy-evaluations")
