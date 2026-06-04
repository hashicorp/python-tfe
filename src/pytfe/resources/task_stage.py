# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from ..errors import InvalidRunIDError, InvalidTaskStageIDError
from ..models.policy_evaluation import PolicyEvaluation
from ..models.run import Run
from ..models.task_result import TaskResult
from ..models.task_stage import TaskStage, TaskStageListOptions
from ..utils import _safe_str, valid_string_id
from ._base import _Service


class TaskStages(_Service):
    """TaskStages provides access to task stage endpoints."""

    def _parse_task_stage(self, data: dict[str, Any]) -> TaskStage:
        attributes = data.get("attributes", {})

        attributes["id"] = _safe_str(data.get("id"))

        relationships = data.get("relationships", {})

        run_data = relationships.get("run", {}).get("data")
        if run_data:
            attributes["run"] = Run.model_construct(id=run_data["id"])

        task_results_data = relationships.get("task-results", {}).get(
            "data",
            [],
        )

        attributes["task-results"] = [
            TaskResult.model_construct(id=task_result["id"])
            for task_result in task_results_data
        ]

        policy_evaluations_data = relationships.get(
            "policy-evaluations",
            {},
        ).get(
            "data",
            [],
        )

        attributes["policy-evaluations"] = [
            PolicyEvaluation.model_construct(id=policy_evaluation["id"])
            for policy_evaluation in policy_evaluations_data
        ]

        return TaskStage.model_validate(attributes)

    # Read
    def read(self, task_stage_id: str) -> TaskStage:
        if not valid_string_id(task_stage_id):
            raise InvalidTaskStageIDError()

        response = self.t.request(
            "GET",
            f"/api/v2/task-stages/{task_stage_id}",
        )

        data = response.json().get("data", {})

        return self._parse_task_stage(data)

    # List
    def list(
        self, run_id: str, options: TaskStageListOptions | None = None
    ) -> Iterator[TaskStage]:
        if not valid_string_id(run_id):
            raise InvalidRunIDError()

        path = f"/api/v2/runs/{run_id}/task-stages"
        params = options.model_dump(by_alias=True) if options else None

        for item in self._list(path, params=params):
            yield self._parse_task_stage(item)

    # Override
    def override(
        self,
        task_stage_id: str,
        comment: str | None = None,
    ) -> TaskStage:
        """
        **Note: This function is still in BETA and subject to change.**
        Override a task stage for a run.
        """
        if not valid_string_id(task_stage_id):
            raise InvalidTaskStageIDError()

        body: dict[str, Any] | None = {"comment": comment} if comment else None

        response = self.t.request(
            "POST",
            f"/api/v2/task-stages/{task_stage_id}/actions/override",
            json_body=body,
        )

        data = response.json().get("data", {})

        return self._parse_task_stage(data)
