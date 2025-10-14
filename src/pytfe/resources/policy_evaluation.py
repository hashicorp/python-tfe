from __future__ import annotations

from ..errors import (
    InvalidTaskStageIDError,
)
from ..models.policy_evaluation import (
    PolicyEvaluation,
    PolicyEvaluationList,
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
    ) -> PolicyEvaluationList:
        """
        **Note: This method is still in BETA and subject to change.**
            List all policy evaluations in the task stage. Only available for OPA policies.
        """
        if not valid_string_id(task_stage_id):
            raise InvalidTaskStageIDError()
        params = options.model_dump(by_alias=True) if options else {}
        path = f"api/v2/task-stages/{task_stage_id}/policy-evaluations"
        r = self.t.request("GET", path, params=params)
        jd = r.json()
        items = []
        meta = jd.get("meta", {})
        pagination = meta.get("pagination", {})
        for item in jd.get("data", []):
            attrs = item.get("attributes", {})
            attrs["id"] = item.get("id")
            attrs["task-stage"] = (
                item.get("relationships", {})
                .get("policy-attachable", {})
                .get("data", {})
            )
            items.append(PolicyEvaluation.model_validate(attrs))
        return PolicyEvaluationList(
            items=items,
            current_page=pagination.get("current-page"),
            next_page=pagination.get("next-page"),
            prev_page=pagination.get("prev-page"),
            total_count=pagination.get("total-count"),
            total_pages=pagination.get("total-pages"),
        )
