# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from collections.abc import Iterator

from .._jsonapi import attach_jsonapi
from ..errors import (
    InvalidTaskStageIDError,
)
from ..models.policy_evaluation import (
    PolicyEvaluation,
    PolicyEvaluationListOptions,
)
from ..utils import valid_string_id
from ._base import _Service


class PolicyEvaluations(_Service):
    """
    PolicyEvalutations describes all the policy evaluation related methods that the Terraform Enterprise API supports.
    TFE API docs: https://developer.hashicorp.com/terraform/cloud-docs/api-docs/policy-checks
    """

    def list(
        self, task_stage_id: str, options: PolicyEvaluationListOptions | None = None
    ) -> Iterator[PolicyEvaluation]:
        """List policy evaluations in a task stage.

        **Note: This method is still in BETA and subject to change.** Only available
        for OPA policies.

        Args:
            task_stage_id: The task stage ID (e.g. ``"ts-xxxxxxxx"``).
            options: Optional pagination settings, as a
                :class:`PolicyEvaluationListOptions`.

        Returns:
            A single-use ``Iterator[PolicyEvaluation]``. Wrap with ``list(...)`` to
            materialize the results or iterate more than once.

        Raises:
            InvalidTaskStageIDError: If ``task_stage_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> for evaluation in client.policy_evaluations.list("ts-123"):
            ...     print(evaluation.id, evaluation.status)
        """
        if not valid_string_id(task_stage_id):
            raise InvalidTaskStageIDError()
        params = options.model_dump(by_alias=True) if options else {}
        path = f"api/v2/task-stages/{task_stage_id}/policy-evaluations"
        for item in self._list(path, params=params):
            attrs = item.get("attributes", {})
            attrs["id"] = item.get("id")
            attrs["policy-attachable"] = (
                item.get("relationships", {})
                .get("policy-attachable", {})
                .get("data", {})
            )
            yield attach_jsonapi(PolicyEvaluation.model_validate(attrs), item)
