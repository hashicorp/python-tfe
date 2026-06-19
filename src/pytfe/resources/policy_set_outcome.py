# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from .._jsonapi import attach_jsonapi
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
        """List policy set outcomes in a policy evaluation.

        **Note: This method is still in BETA and subject to change.** Only available
        for OPA policies.

        Args:
            policy_evaluation_id: The policy evaluation ID (e.g.
                ``"poleval-xxxxxxxx"``).
            options: Optional filters and pagination, as a
                :class:`PolicySetOutcomeListOptions`.

        Returns:
            A single-use ``Iterator[PolicySetOutcome]``. Wrap with ``list(...)`` to
            materialize the results or iterate more than once.

        Raises:
            InvalidPolicyEvaluationIDError: If ``policy_evaluation_id`` is not a valid
                resource ID.
            TFEError: If the API request fails.

        Example:
            >>> for outcome in client.policy_set_outcomes.list("poleval-123"):
            ...     print(outcome.id, outcome.policy_set_name)
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
        """Build filter query parameters for listing policy set outcomes.

        Args:
            options: Optional filter settings, as a
                :class:`PolicySetOutcomeListOptions`.

        Returns:
            A ``dict[str, str] | None``. ``None`` is returned when no filters are set.

        Example:
            >>> from pytfe.models import PolicySetOutcomeListOptions
            >>> params = client.policy_set_outcomes.build_query_string(
            ...     PolicySetOutcomeListOptions(page_size=20)
            ... )
        """
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
        """Read a policy set outcome by its ID.

        **Note: This method is still in BETA and subject to change.** Only available
        for OPA policies.

        Args:
            policy_set_outcome_id: The policy set outcome ID (e.g. ``"pso-xxxxxxxx"``).

        Returns:
            The :class:`PolicySetOutcome`.

        Raises:
            InvalidPolicySetOutcomeIDError: If ``policy_set_outcome_id`` is not a valid
                resource ID.
            TFEError: If the API request fails.

        Example:
            >>> outcome = client.policy_set_outcomes.read("pso-123")
            >>> print(outcome.policy_set_name)
        """
        if not valid_string_id(policy_set_outcome_id):
            raise InvalidPolicySetOutcomeIDError()
        path = f"api/v2/policy-set-outcomes/{policy_set_outcome_id}"
        r = self.t.request("GET", path)
        data = r.json().get("data", {})
        return attach_jsonapi(PolicySetOutcome.model_validate(data), data)

    def _policy_set_outcome_from(self, d: dict[str, Any]) -> PolicySetOutcome:
        """Convert API response dict to PolicySetParameter model."""
        attrs = d.get("attributes", {})
        attrs["id"] = d.get("id")
        attrs["policy-evaluation"] = (
            d.get("relationships", {}).get("policy-evaluation", {}).get("data", {})
        )
        return attach_jsonapi(PolicySetOutcome.model_validate(attrs), d)
