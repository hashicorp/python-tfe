# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from ..errors import InvalidRunIDError
from ..models.task_stage import TaskStage
from ..utils import _safe_str, valid_string_id
from ._base import _Service


class TaskStages(_Service):
    """TaskStages provides access to task stage endpoints."""

    # Read
    def read(self, task_stage_id: str) -> TaskStage:
        if not valid_string_id(task_stage_id):
            raise ValueError("Invalid task_stage_id")

        response = self.t.request(
            "GET",
            f"/api/v2/task-stages/{task_stage_id}",
        )

        data = response.json().get("data", {})
        attributes = data.get("attributes", {})
        attributes["id"] = _safe_str(data.get("id"))

        return TaskStage.model_validate(attributes)

    # List
    def list(self, run_id: str) -> Iterator[TaskStage]:
        if not valid_string_id(run_id):
            raise InvalidRunIDError()

        path = f"/api/v2/runs/{run_id}/task-stages"

        for item in self._list(path):
            attributes = item.get("attributes", {})
            attributes["id"] = item.get("id")

            yield TaskStage.model_validate(attributes)

    # Override
    def override(
        self,
        task_stage_id: str,
        comment: str | None = None,
    ) -> TaskStage:
        if not valid_string_id(task_stage_id):
            raise ValueError("Invalid task_stage_id")

        body: dict[str, Any] | None = (
            {"comment": comment} if comment else None
        )

        response = self.t.request(
            "POST",
            f"/api/v2/task-stages/{task_stage_id}/actions/override",
            json_body=body,
        )

        data = response.json().get("data", {})
        attributes = data.get("attributes", {})
        attributes["id"] = _safe_str(data.get("id"))

        return TaskStage.model_validate(attributes)