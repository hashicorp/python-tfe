# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import builtins
from collections.abc import Iterator
from typing import Any

from .._jsonapi import attach_jsonapi
from ..errors import (
    InvalidRunIDError,
    InvalidTfPolicyEvaluationIDError,
)
from ..models.tf_policy_evaluation import (
    TfPolicyEvaluation,
    TfPolicyEvaluationListOptions,
    TfPolicyEvaluationOverrideOptions,
)
from ..models.tf_policy_set_outcome import (
    TfPolicySetOutcome,
    TfPolicySetOutcomeListOptions,
)
from ..utils import valid_string_id
from ._base import _Service


class TfPolicyEvaluations(_Service):
    """tf-policy evaluation methods for the HCP Terraform / TFE API."""

    def list(
        self,
        run_id: str,
        options: TfPolicyEvaluationListOptions | None = None,
    ) -> Iterator[TfPolicyEvaluation]:
        """List tf-policy evaluations for a run.

        Args:
            run_id: The run ID (e.g. ``"run-xxxxxxxx"``).
            options: Optional pagination and include settings, as a
                :class:`TfPolicyEvaluationListOptions`.

        Returns:
            A single-use ``Iterator[TfPolicyEvaluation]``. Wrap with ``list(...)``
            to materialize or iterate more than once.

        Raises:
            InvalidRunIDError: If ``run_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> for evaluation in client.tf_policy_evaluations.list("run-abc123"):
            ...     print(evaluation.id, evaluation.status)
        """
        if not valid_string_id(run_id):
            raise InvalidRunIDError()
        params = options.model_dump(by_alias=True, exclude_none=True) if options else {}
        path = f"/api/v2/runs/{run_id}/tf-policy-evaluations"
        for item in self._list(path, params=params):
            yield self._tf_policy_evaluation_from(item)

    def read(
        self,
        tf_policy_evaluation_id: str,
        options: TfPolicyEvaluationListOptions | None = None,
    ) -> TfPolicyEvaluation:
        """Read a single tf-policy evaluation by ID.

        Args:
            tf_policy_evaluation_id: The evaluation ID (e.g. ``"tfpeval-xxxxxxxx"``).
            options: Optional include settings (e.g. ``include="tf_policy_set_outcomes"``),
                as a :class:`TfPolicyEvaluationListOptions`.

        Returns:
            The :class:`TfPolicyEvaluation`.

        Raises:
            InvalidTfPolicyEvaluationIDError: If ``tf_policy_evaluation_id`` is not a
                valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> evaluation = client.tf_policy_evaluations.read("tfpeval-abc123")
            >>> print(evaluation.status)
        """
        if not valid_string_id(tf_policy_evaluation_id):
            raise InvalidTfPolicyEvaluationIDError()
        params = options.model_dump(by_alias=True, exclude_none=True) if options else {}
        path = f"/api/v2/tf-policy-evaluations/{tf_policy_evaluation_id}"
        r = self.t.request("GET", path, params=params)
        data = r.json().get("data", {})
        included = r.json().get("included")
        return self._tf_policy_evaluation_from(data, included=included)

    def override(
        self,
        tf_policy_evaluation_id: str,
        options: TfPolicyEvaluationOverrideOptions | None = None,
    ) -> TfPolicyEvaluation:
        """Override a tf-policy evaluation that is in ``awaiting_override`` status.

        The override action transitions the evaluation to ``overridden`` and
        unblocks the run. Only valid when ``actions.is-overridable`` is ``true``.

        Args:
            tf_policy_evaluation_id: The evaluation ID (e.g. ``"tfpeval-xxxxxxxx"``).
            options: Optional override comment, as a
                :class:`TfPolicyEvaluationOverrideOptions`.

        Returns:
            The updated :class:`TfPolicyEvaluation`

        Raises:
            InvalidTfPolicyEvaluationIDError: If ``tf_policy_evaluation_id`` is not a
                valid resource ID.
            TFEError: If the API request fails (including state-transition errors when
                the evaluation is not in ``awaiting_override``).

        Example:
            >>> result = client.tf_policy_evaluations.override(
            ...     "tfpeval-abc123",
            ...     TfPolicyEvaluationOverrideOptions(comment="approved by ops"),
            ... )
            >>> print(result.status)
        """
        if not valid_string_id(tf_policy_evaluation_id):
            raise InvalidTfPolicyEvaluationIDError()
        body = options.model_dump(exclude_none=True) if options else {}
        path = (
            f"/api/v2/tf-policy-evaluations/{tf_policy_evaluation_id}/actions/override"
        )
        r = self.t.request("POST", path, json_body=body)
        data = r.json().get("data", {})
        return self._tf_policy_evaluation_from(data)

    def list_set_outcomes(
        self,
        tf_policy_evaluation_id: str,
        options: TfPolicySetOutcomeListOptions | None = None,
    ) -> Iterator[TfPolicySetOutcome]:
        """List tf-policy set outcomes nested under a tf-policy evaluation.

        Args:
            tf_policy_evaluation_id: The evaluation ID (e.g. ``"tfpeval-xxxxxxxx"``).
            options: Optional pagination and filter settings, as a
                :class:`TfPolicySetOutcomeListOptions`.

        Returns:
            A single-use ``Iterator[TfPolicySetOutcome]``. Wrap with ``list(...)``
            to materialize or iterate more than once.

        Raises:
            InvalidTfPolicyEvaluationIDError: If ``tf_policy_evaluation_id`` is not a
                valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> for outcome in client.tf_policy_evaluations.list_set_outcomes(
            ...     "tfpeval-abc123",
            ...     TfPolicySetOutcomeListOptions(filter_status="failed"),
            ... ):
            ...     print(outcome.id, outcome.policy_set_name)
        """
        if not valid_string_id(tf_policy_evaluation_id):
            raise InvalidTfPolicyEvaluationIDError()
        params: dict[str, Any] = {}
        if options:
            page_params = options.model_dump(
                by_alias=True,
                exclude_none=True,
                include={"page_size", "page_number"},
            )
            params.update(page_params)
            filter_params = _build_filter_params(options)
            params.update(filter_params)
        path = f"/api/v2/tf-policy-evaluations/{tf_policy_evaluation_id}/tf-policy-set-outcomes"
        for item in self._list(path, params=params):
            yield _tf_policy_set_outcome_from(item)

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _tf_policy_evaluation_from(
        self,
        data: dict[str, Any],
        included: builtins.list[dict[str, Any]] | None = None,
    ) -> TfPolicyEvaluation:
        """Convert an API data object to a :class:`TfPolicyEvaluation`."""
        attrs = dict(data.get("attributes") or {})
        attrs["id"] = data.get("id")
        model = TfPolicyEvaluation.model_validate(attrs)
        return attach_jsonapi(model, data, included)


def _tf_policy_set_outcome_from(data: dict[str, Any]) -> TfPolicySetOutcome:
    """Convert an API data object to a :class:`TfPolicySetOutcome`."""
    attrs = dict(data.get("attributes") or {})
    attrs["id"] = data.get("id")
    model = TfPolicySetOutcome.model_validate(attrs)
    return attach_jsonapi(model, data)


def _build_filter_params(options: TfPolicySetOutcomeListOptions) -> dict[str, str]:
    """Build ``filter[...]`` query parameters from list options."""
    result: dict[str, str] = {}
    if options.filter_status is not None:
        result["filter[outcomes][status]"] = options.filter_status
    if options.filter_enforcement_level is not None:
        result["filter[outcomes][enforcement_level]"] = options.filter_enforcement_level
    return result
