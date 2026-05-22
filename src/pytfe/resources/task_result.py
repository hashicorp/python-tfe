# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from typing import Any

from pytfe.models.policy_evaluation import PolicyEvaluation
from pytfe.models.run import Run
from pytfe.models.task_result import TaskResult
from pytfe.models.task_stage import TaskStage
from pytfe.models.workspace import Workspace
from pytfe.utils import valid_string_id

from ._base import _Service


class TaskResults(_Service):
    def read(self, task_result_id: str) -> TaskResult:
        if not valid_string_id(task_result_id):
            raise ValueError("Invalid task_result_id")

        path = f"/api/v2/task-results/{task_result_id}"

        response = self.t.request("GET", path)
        data = response.json()

        if "data" not in data:
            raise ValueError("Invalid response format")

        return self._parse_task_result(data["data"])

    def _parse_task_result(self, data: dict[str, Any]) -> TaskResult:
        # Ensure forward references in TaskResult are resolved before use.
        TaskResult.model_rebuild(
            raise_errors=False,
            _types_namespace={
                "PolicyEvaluation": PolicyEvaluation,
                "Run": Run,
                "TaskStage": TaskStage,
                "Workspace": Workspace,
            },
        )

        attributes = data.get("attributes", {})
        attributes["id"] = data.get("id")

        relationships = data.get("relationships", {})

        # Map task-stage relationship into the TaskStage SDK model.
        task_stage_data = relationships.get("task-stage", {}).get("data")
        if task_stage_data:
            attributes["task-stage"] = TaskStage.model_validate(task_stage_data)
        else:
            attributes["task-stage"] = None

        # Map run relationship into the Run SDK model.
        run_data = relationships.get("run", {}).get("data")
        if run_data:
            attributes["run"] = Run.model_validate(run_data)
        else:
            attributes["run"] = None

        # Map workspace relationship into the Workspace SDK model.
        workspace_data = relationships.get("workspace", {}).get("data")
        if workspace_data:
            attributes["workspace"] = Workspace.model_validate(workspace_data)
        else:
            attributes["workspace"] = None

        # Map policy-evaluations relationship into a list of PolicyEvaluation models.
        policy_evaluations_data = relationships.get("policy-evaluations", {}).get(
            "data", []
        )
        attributes["policy-evaluations"] = [
            PolicyEvaluation.model_validate(pe) for pe in policy_evaluations_data
        ]

        return TaskResult.model_validate(attributes)
