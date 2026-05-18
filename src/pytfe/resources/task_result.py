# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from typing import Any

from pytfe.models.task_result import TaskResult
from pytfe.models.task_stage import TaskStage
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
        attributes = data.get("attributes", {})

        attributes["id"] = data.get("id")

        relationships = data.get("relationships", {})

        # Map task-stage relationship into the TaskStage SDK model so callers
        # get a typed object rather than a raw {id, type} dict.
        if "task-stage" in relationships:
            task_stage_data = relationships["task-stage"].get("data")
            if task_stage_data:
                attributes["task_stage"] = TaskStage.model_validate(task_stage_data)
            else:
                attributes["task_stage"] = None

        if "run" in relationships:
            attributes["run"] = relationships["run"].get("data")

        if "workspace" in relationships:
            attributes["workspace"] = relationships["workspace"].get("data")

        if "policy-evaluations" in relationships:
            attributes["policy_evaluations"] = relationships["policy-evaluations"].get(
                "data"
            )

        return TaskResult.model_validate(attributes)
