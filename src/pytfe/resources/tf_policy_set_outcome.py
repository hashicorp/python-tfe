# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from typing import Any

from .._jsonapi import attach_jsonapi
from ..errors import InvalidTfPolicySetOutcomeIDError
from ..models.tf_policy_set_outcome import TfPolicySetOutcome
from ..utils import valid_string_id
from ._base import _Service


class TfPolicySetOutcomes(_Service):
    """tf-policy set outcome methods for the HCP Terraform / TFE API."""

    def read(self, tf_policy_set_outcome_id: str) -> TfPolicySetOutcome:
        """Read a tf-policy set outcome by ID.

        Args:
            tf_policy_set_outcome_id: The set outcome ID (e.g. ``"tfpsout-xxxxxxxx"``).

        Returns:
            The :class:`TfPolicySetOutcome`.

        Raises:
            InvalidTfPolicySetOutcomeIDError: If ``tf_policy_set_outcome_id`` is not a
                valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> outcome = client.tf_policy_set_outcomes.read("tfpsout-abc123")
            >>> for o in outcome.outcomes:
            ...     print(o.policy_name, o.enforcement_level, o.status)
        """
        if not valid_string_id(tf_policy_set_outcome_id):
            raise InvalidTfPolicySetOutcomeIDError()
        path = f"/api/v2/tf-policy-set-outcomes/{tf_policy_set_outcome_id}"
        r = self.t.request("GET", path)
        data = r.json().get("data", {})
        return _tf_policy_set_outcome_from(data)


def _tf_policy_set_outcome_from(data: dict[str, Any]) -> TfPolicySetOutcome:
    attrs = dict(data.get("attributes") or {})
    attrs["id"] = data.get("id")
    model = TfPolicySetOutcome.model_validate(attrs)
    return attach_jsonapi(model, data)
