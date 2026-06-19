# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from typing import Any

from pytfe.models.task_result import TaskResult
from pytfe.models.task_stage import TaskStage
from pytfe.utils import valid_string_id

from .._jsonapi import attach_jsonapi
from ._base import _Service


class TaskResults(_Service):
    def read(self, task_result_id: str) -> TaskResult:
        """Read a task result by its ID.

        Args:
            task_result_id: The task result ID (e.g. ``"taskrs-abc123"``).

        Returns:
            The :class:`TaskResult`.

        Raises:
            ValueError: If ``task_result_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> result = client.task_results.read("taskrs-abc123")
            >>> print(result.status)
        """
        if not valid_string_id(task_result_id):
            raise ValueError("Invalid task_result_id")

        path = f"/api/v2/task-results/{task_result_id}"

        response = self.t.request("GET", path)
        data = response.json().get("data", {})

        return self._parse_task_result(data)

    def _parse_task_result(self, data: dict[str, Any]) -> TaskResult:
        attributes = data.get("attributes", {})
        attributes["id"] = data.get("id")

        relationships = data.get("relationships", {})

        # Map task-stage relationship into the TaskStage model.
        task_stage_data = relationships.get("task-stage", {}).get("data")
        if task_stage_data:
            attributes["task-stage"] = TaskStage.model_construct(
                id=task_stage_data["id"]
            )

        return attach_jsonapi(TaskResult.model_validate(attributes), data)
