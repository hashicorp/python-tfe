# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import builtins
from collections.abc import Iterator
from typing import Any

from .._jsonapi import attach_jsonapi, parse_relationships
from ..errors import InvalidRunIDError, InvalidTaskStageIDError
from ..models.policy_evaluation import PolicyEvaluation
from ..models.run import Run
from ..models.task_result import TaskResult
from ..models.task_stage import TaskStage, TaskStageListOptions, TaskStageReadOptions
from ..utils import _safe_str, valid_string_id
from ._base import _Service


class TaskStages(_Service):
    """TaskStages provides access to task stage endpoints."""

    def _parse_task_stage(
        self,
        data: dict[str, Any],
        included: builtins.list[dict[str, Any]] | None = None,
    ) -> TaskStage:
        attributes = data.get("attributes", {})
        attributes["id"] = _safe_str(data.get("id"))
        attributes.update(
            parse_relationships(
                data.get("relationships"),
                {
                    "run": Run,
                    "task-results": TaskResult,
                    "policy-evaluations": PolicyEvaluation,
                },
                included=included,
            )
        )
        # Preserve the historical contract: parsed task stages expose empty
        # lists (not None) for these collections when the relations are absent.
        attributes.setdefault("task_results", [])
        attributes.setdefault("policy_evaluations", [])
        return attach_jsonapi(TaskStage.model_validate(attributes), data, included)

    # Read
    def read(
        self, task_stage_id: str, options: TaskStageReadOptions | None = None
    ) -> TaskStage:
        """Read a task stage by ID.

        Args:
            task_stage_id: The task stage ID (e.g. ``"ts-xxxxxxxx"``).
            options: Optional include settings, as a :class:`TaskStageReadOptions`.

        Returns:
            The :class:`TaskStage`.

        Raises:
            InvalidTaskStageIDError: If ``task_stage_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> stage = client.task_stages.read("ts-123")
            >>> print(stage.status)
        """
        if not valid_string_id(task_stage_id):
            raise InvalidTaskStageIDError()

        params: dict[str, str] = {}
        if options and options.include:
            params["include"] = ",".join([opt.value for opt in options.include])

        response = self.t.request(
            "GET",
            f"/api/v2/task-stages/{task_stage_id}",
            params=params,
        )

        payload = response.json()

        return self._parse_task_stage(payload.get("data", {}), payload.get("included"))

    # List
    def list(
        self, run_id: str, options: TaskStageListOptions | None = None
    ) -> Iterator[TaskStage]:
        """List task stages for a run.

        Args:
            run_id: The run ID (e.g. ``"run-xxxxxxxx"``).
            options: Optional pagination settings, as a :class:`TaskStageListOptions`.

        Returns:
            A single-use ``Iterator[TaskStage]``. Wrap with ``list(...)`` to
            materialize the results or iterate more than once.

        Raises:
            InvalidRunIDError: If ``run_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> for stage in client.task_stages.list("run-CZcmD7eagjhyX0vN"):
            ...     print(stage.id, stage.stage)
        """
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
        """Override a task stage for a run.

        **Note: This function is still in BETA and subject to change.**

        Args:
            task_stage_id: The task stage ID (e.g. ``"ts-xxxxxxxx"``).
            comment: Optional override comment.

        Returns:
            The :class:`TaskStage`.

        Raises:
            InvalidTaskStageIDError: If ``task_stage_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> stage = client.task_stages.override("ts-123", comment="Approved")
            >>> print(stage.status)
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
