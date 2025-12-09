from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from ..errors import (
    InvalidPolicyEvaluationIDError,
    InvalidPolicySetOutcomeIDError,
)
from ..models.policy_set_outcome import (
    PolicySetOutcome,
    PolicySetOutcomeListOptions,
)
from ..utils import valid_string_id
from ._base import _Service


class PolicySetOutcomes(_Service):
    """
    PolicySetOutcomes describes all the policy set outcome related methods that the Terraform Enterprise API supports.
    TFE API docs: https://developer.hashicorp.com/terraform/cloud-docs/api-docs/policy-checks
    """

    def list(
        self,
        policy_evaluation_id: str,
        options: PolicySetOutcomeListOptions | None = None,
    ) -> Iterator[PolicySetOutcome]:
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
        for item in self._list(path, params=params):
            yield self._policy_set_outcome_from(item)

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
            raise InvalidPolicySetOutcomeIDError()
        path = f"api/v2/policy-set-outcomes/{policy_set_outcome_id}"
        r = self.t.request("GET", path)
        data = r.json().get("data", {})
        return PolicySetOutcome.model_validate(data)

    def _policy_set_outcome_from(self, d: dict[str, Any]) -> PolicySetOutcome:
        """Convert API response dict to PolicySetParameter model."""
        attrs = d.get("attributes", {})
        attrs["id"] = d.get("id")
        attrs["policy-evaluation"] = (
            d.get("relationships", {}).get("policy-evaluation", {}).get("data", {})
        )
        return PolicySetOutcome.model_validate(attrs)
