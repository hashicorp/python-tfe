from __future__ import annotations

from collections.abc import Iterator

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
        """
        **Note: This method is still in BETA and subject to change.**
        List all policy evaluations in the task stage. Only available for OPA policies.
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
            yield PolicyEvaluation.model_validate(attrs)
