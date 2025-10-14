from __future__ import annotations

from ..errors import (
    InvalidPolicyEvaluationIDError,
)
from ..models.policy_set_outcome import (
    PolicySetOutcome,
    PolicySetOutcomeList,
    PolicySetOutcomeListOptions,
)
from ..utils import valid_string_id
from ._base import _Service


class PolicySets(_Service):
    """
    PolicySetOutcomes describes all the policy set outcome related methods that the Terraform Enterprise API supports.
    TFE API docs: https://developer.hashicorp.com/terraform/cloud-docs/api-docs/policy-checks
    """

    def list(
        self,
        policy_evaluation_id: str,
        options: PolicySetOutcomeListOptions | None = None,
    ) -> PolicySetOutcomeList:
        """
        **Note: This method is still in BETA and subject to change.**
            List all policy set outcomes in the policy evaluation. Only available for OPA policies.
        """
        if not valid_string_id(policy_evaluation_id):
            raise InvalidPolicyEvaluationIDError()

        additional_query_params = self.build_query_string(options)
        params = options.model_dump(by_alias=True) if options else {}
        if additional_query_params:
            params.update(additional_query_params)
        path = f"api/v2/policy-evaluations/{policy_evaluation_id}/policy-set-outcomes"
        r = self.t.request("GET", path, params=params)
        jd = r.json()
        items = []
        meta = jd.get("meta", {})
        pagination = meta.get("pagination", {})
        for item in jd.get("data", []):
            attrs = item.get("attributes", {})
            attrs["id"] = item.get("id")
            attrs["policy-evaluation"] = (
                item.get("relationships", {})
                .get("policy-evaluation", {})
                .get("data", {})
            )
            items.append(PolicySetOutcome.model_validate(attrs))
        return PolicySetOutcomeList(
            items=items,
            current_page=pagination.get("current-page"),
            next_page=pagination.get("next-page"),
            prev_page=pagination.get("prev-page"),
            total_count=pagination.get("total-count"),
            total_pages=pagination.get("total-pages"),
        )

    def build_query_string(
        self, options: PolicySetOutcomeListOptions | None
    ) -> dict[str, str] | None:
        """build_query_string takes the PolicySetOutcomeListOptions and returns a filters map."""
        result = {}
        if options is None or options.filter is None:
            return None
        for key, value in options.filter.items():
            if value.status is not None:
                result[f"filter[{key}][status]"] = value.status
            if value.enforcement_level is not None:
                result[f"filter[{key}][enforcement-level]"] = value.enforcement_level
        return result

    def read(self, policy_set_outcome_id: str) -> PolicySetOutcome:
        """
        **Note: This method is still in BETA and subject to change.**
        Read a single policy set outcome by ID. Only available for OPA policies."""
        if not valid_string_id(policy_set_outcome_id):
            raise InvalidPolicyEvaluationIDError()
        path = f"api/v2/policy-set-outcomes/{policy_set_outcome_id}"
        r = self.t.request("GET", path)
        jd = r.json()
        item = jd.get("data", {})
        attrs = item.get("attributes", {})
        attrs["id"] = item.get("id")
        attrs["policy-evaluation"] = (
            item.get("relationships", {}).get("policy-evaluation", {}).get("data", {})
        )
        return PolicySetOutcome.model_validate(attrs)
