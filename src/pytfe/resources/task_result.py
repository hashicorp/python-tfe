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


def _transform_task_result_relationships(
    relationships: dict[str, Any],
) -> dict[str, Any]:
    """Transform task result relationships into typed SDK models."""
    result: dict[str, Any] = {
        "policy-evaluations": [],
    }

    if not relationships:
        return result

    if data := relationships.get("task-stage", {}).get("data"):
        result["task-stage"] = TaskStage.model_validate(data)

    if data := relationships.get("run", {}).get("data"):
        result["run"] = Run.model_validate(data)

    if data := relationships.get("workspace", {}).get("data"):
        result["workspace"] = Workspace.model_validate(data)

    policy_evaluations = relationships.get("policy-evaluations", {}).get("data")
    if isinstance(policy_evaluations, list):
        result["policy-evaluations"] = [
            PolicyEvaluation.model_validate(item)
            for item in policy_evaluations
            if isinstance(item, dict) and item.get("id")
        ]

    return result


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
        attributes = data.get("attributes", {})
        attributes["id"] = data.get("id")

        relationships = _transform_task_result_relationships(
            data.get("relationships", {}) or {}
        )

        attributes.update(relationships)

        return TaskResult.model_validate(attributes)
