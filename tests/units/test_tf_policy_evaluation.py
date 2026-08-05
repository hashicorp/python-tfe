# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""Unit tests for TfPolicyEvaluations resource."""

from unittest.mock import Mock

import pytest

from pytfe._http import HTTPTransport
from pytfe.errors import (
    InvalidRunIDError,
    InvalidTfPolicyEvaluationIDError,
)
from pytfe.models.policy_types import TfPolicyEvaluationStatus, TfPolicyStage
from pytfe.models.tf_policy_evaluation import (
    TfPolicyEvaluation,
    TfPolicyEvaluationListOptions,
    TfPolicyEvaluationOverrideOptions,
)
from pytfe.models.tf_policy_set_outcome import (
    TfPolicySetOutcome,
    TfPolicySetOutcomeListOptions,
)
from pytfe.resources.tf_policy_evaluation import TfPolicyEvaluations

_EVAL_ID = "tfpeval-abc123"
_RUN_ID = "run-abc123"


class TestTfPolicyEvaluations:
    """Tests for the TfPolicyEvaluations service."""

    @pytest.fixture
    def mock_transport(self):
        return Mock(spec=HTTPTransport)

    @pytest.fixture
    def service(self, mock_transport):
        return TfPolicyEvaluations(mock_transport)

    @pytest.fixture
    def eval_api_data(self):
        """Minimal evaluation API data object."""
        return {
            "id": _EVAL_ID,
            "type": "tf-policy-evaluations",
            "attributes": {
                "status": "passed",
                "stage-type": "Plan",
                "result-count": {
                    "advisory-failed": 0,
                    "mandatory-failed": 0,
                    "passed": 3,
                    "errored": 0,
                    "unknown": 0,
                },
            },
            "relationships": {
                "run": {"data": {"id": _RUN_ID, "type": "runs"}},
            },
        }

    @pytest.fixture
    def awaiting_override_data(self):
        """Evaluation data in awaiting_override status."""
        return {
            "id": _EVAL_ID,
            "type": "tf-policy-evaluations",
            "attributes": {
                "status": "awaiting_override",
                "stage-type": "Plan",
                "actions": {"is-overridable": True},
                "permissions": {"can-override": True},
            },
        }

    # ── Model tests ──────────────────────────────────────────────────────────

    def test_evaluation_model_fields(self, eval_api_data):
        """TfPolicyEvaluation parses id, status, and stage-type."""
        attrs = {**eval_api_data["attributes"], "id": eval_api_data["id"]}
        model = TfPolicyEvaluation.model_validate(attrs)
        assert model.id == _EVAL_ID
        assert model.status == TfPolicyEvaluationStatus.PASSED
        assert model.stage_type == TfPolicyStage.PLAN

    def test_evaluation_result_count(self, eval_api_data):
        """result_count sub-model parsed correctly."""
        attrs = {**eval_api_data["attributes"], "id": eval_api_data["id"]}
        model = TfPolicyEvaluation.model_validate(attrs)
        assert model.result_count is not None
        assert model.result_count.passed == 3
        assert model.result_count.mandatory_failed == 0

    def test_list_options_serializes(self):
        """TfPolicyEvaluationListOptions serialises page params with alias."""
        opts = TfPolicyEvaluationListOptions(page_size=20)
        dumped = opts.model_dump(by_alias=True, exclude_none=True)
        assert dumped == {"page[size]": 20}

    def test_override_options_serializes(self):
        """TfPolicyEvaluationOverrideOptions serialises comment."""
        opts = TfPolicyEvaluationOverrideOptions(comment="approved")
        dumped = opts.model_dump(exclude_none=True)
        assert dumped == {"comment": "approved"}

    def test_override_options_no_comment(self):
        """TfPolicyEvaluationOverrideOptions with no comment dumps to empty dict."""
        opts = TfPolicyEvaluationOverrideOptions()
        assert opts.model_dump(exclude_none=True) == {}

    # ── Parser tests ─────────────────────────────────────────────────────────

    def test_tf_policy_evaluation_from(self, service, eval_api_data):
        """_tf_policy_evaluation_from builds TfPolicyEvaluation from API data."""
        result = service._tf_policy_evaluation_from(eval_api_data)
        assert isinstance(result, TfPolicyEvaluation)
        assert result.id == _EVAL_ID
        assert result.status == TfPolicyEvaluationStatus.PASSED

    def test_tf_policy_evaluation_from_missing_attrs(self, service):
        """_tf_policy_evaluation_from handles missing attributes gracefully."""
        data = {"id": _EVAL_ID, "attributes": {}}
        result = service._tf_policy_evaluation_from(data)
        assert result.id == _EVAL_ID
        assert result.status is None

    # ── list() tests ─────────────────────────────────────────────────────────

    def test_list_success(self, service, eval_api_data):
        """list() yields TfPolicyEvaluation objects for each API item."""
        service._list = Mock(return_value=[eval_api_data])

        results = list(service.list(_RUN_ID))

        service._list.assert_called_once_with(
            f"/api/v2/runs/{_RUN_ID}/tf-policy-evaluations", params={}
        )
        assert len(results) == 1
        assert isinstance(results[0], TfPolicyEvaluation)
        assert results[0].id == _EVAL_ID

    def test_list_with_options(self, service, eval_api_data):
        """list() forwards page params from options."""
        service._list = Mock(return_value=[eval_api_data])
        opts = TfPolicyEvaluationListOptions(page_size=5)

        list(service.list(_RUN_ID, options=opts))

        _, kwargs = service._list.call_args
        assert kwargs["params"]["page[size]"] == 5

    def test_list_empty(self, service):
        """list() returns empty iterator when no evaluations exist."""
        service._list = Mock(return_value=[])
        assert list(service.list(_RUN_ID)) == []

    def test_list_invalid_run_id(self, service):
        """list() raises InvalidRunIDError for a bad run ID."""
        with pytest.raises(InvalidRunIDError):
            list(service.list("not valid!"))

    def test_list_empty_run_id(self, service):
        """list() raises InvalidRunIDError for an empty run ID."""
        with pytest.raises(InvalidRunIDError):
            list(service.list(""))

    # ── read() tests ─────────────────────────────────────────────────────────

    def test_read_success(self, service, mock_transport, eval_api_data):
        """read() GETs the correct path and returns TfPolicyEvaluation."""
        mock_response = Mock()
        mock_response.json.return_value = {"data": eval_api_data}
        mock_transport.request.return_value = mock_response

        result = service.read(_EVAL_ID)

        mock_transport.request.assert_called_once_with(
            "GET", f"/api/v2/tf-policy-evaluations/{_EVAL_ID}", params={}
        )
        assert isinstance(result, TfPolicyEvaluation)
        assert result.id == _EVAL_ID

    def test_read_with_include(self, service, mock_transport, eval_api_data):
        """read() forwards include param when set in options."""
        mock_response = Mock()
        mock_response.json.return_value = {"data": eval_api_data, "included": []}
        mock_transport.request.return_value = mock_response

        opts = TfPolicyEvaluationListOptions(include="tf_policy_set_outcomes")
        service.read(_EVAL_ID, options=opts)

        _, kwargs = mock_transport.request.call_args
        assert kwargs["params"]["include"] == "tf_policy_set_outcomes"

    def test_read_invalid_id(self, service):
        """read() raises InvalidTfPolicyEvaluationIDError for a bad ID."""
        with pytest.raises(InvalidTfPolicyEvaluationIDError):
            service.read("not valid!")

    def test_read_empty_id(self, service):
        """read() raises InvalidTfPolicyEvaluationIDError for an empty ID."""
        with pytest.raises(InvalidTfPolicyEvaluationIDError):
            service.read("")

    # ── override() tests ─────────────────────────────────────────────────────

    def test_override_success(self, service, mock_transport, awaiting_override_data):
        """override() POSTs to the correct path and returns TfPolicyEvaluation."""
        overridden = dict(awaiting_override_data)
        overridden["attributes"] = {
            **awaiting_override_data["attributes"],
            "status": "overridden",
        }
        mock_response = Mock()
        mock_response.json.return_value = {"data": overridden}
        mock_transport.request.return_value = mock_response

        result = service.override(
            _EVAL_ID, TfPolicyEvaluationOverrideOptions(comment="ops approved")
        )

        mock_transport.request.assert_called_once_with(
            "POST",
            f"/api/v2/tf-policy-evaluations/{_EVAL_ID}/actions/override",
            json_body={"comment": "ops approved"},
        )
        assert isinstance(result, TfPolicyEvaluation)
        assert result.status == TfPolicyEvaluationStatus.OVERRIDDEN

    def test_override_no_comment(self, service, mock_transport, awaiting_override_data):
        """override() sends empty body when no comment provided."""
        mock_response = Mock()
        mock_response.json.return_value = {"data": awaiting_override_data}
        mock_transport.request.return_value = mock_response

        service.override(_EVAL_ID)

        _, kwargs = mock_transport.request.call_args
        assert kwargs["json_body"] == {}

    def test_override_invalid_id(self, service):
        """override() raises InvalidTfPolicyEvaluationIDError for a bad ID."""
        with pytest.raises(InvalidTfPolicyEvaluationIDError):
            service.override("not valid!")

    def test_override_empty_id(self, service):
        """override() raises InvalidTfPolicyEvaluationIDError for an empty ID."""
        with pytest.raises(InvalidTfPolicyEvaluationIDError):
            service.override("")

    # ── list_set_outcomes() tests ────────────────────────────────────────────

    @pytest.fixture
    def set_outcome_api_data(self):
        """Minimal TfPolicySetOutcome API data object."""
        return {
            "id": "tfpsout-xyz789",
            "type": "tf-policy-set-outcomes",
            "attributes": {
                "policy-set-name": "my-policy-set",
                "overridable": True,
                "outcomes": [],
            },
        }

    def test_list_set_outcomes_success(self, service, set_outcome_api_data):
        """list_set_outcomes() yields TfPolicySetOutcome objects."""
        service._list = Mock(return_value=[set_outcome_api_data])

        results = list(service.list_set_outcomes(_EVAL_ID))

        service._list.assert_called_once_with(
            f"/api/v2/tf-policy-evaluations/{_EVAL_ID}/tf-policy-set-outcomes",
            params={},
        )
        assert len(results) == 1
        assert isinstance(results[0], TfPolicySetOutcome)
        assert results[0].id == "tfpsout-xyz789"

    def test_list_set_outcomes_with_filter(self, service, set_outcome_api_data):
        """list_set_outcomes() builds filter params from options."""
        service._list = Mock(return_value=[set_outcome_api_data])
        opts = TfPolicySetOutcomeListOptions(filter_status="failed")

        list(service.list_set_outcomes(_EVAL_ID, options=opts))

        _, kwargs = service._list.call_args
        assert kwargs["params"]["filter[outcomes][status]"] == "failed"

    def test_list_set_outcomes_enforcement_level_filter(
        self, service, set_outcome_api_data
    ):
        """list_set_outcomes() builds enforcement_level filter param."""
        service._list = Mock(return_value=[set_outcome_api_data])
        opts = TfPolicySetOutcomeListOptions(
            filter_enforcement_level="mandatory_overridable"
        )

        list(service.list_set_outcomes(_EVAL_ID, options=opts))

        _, kwargs = service._list.call_args
        assert (
            kwargs["params"]["filter[outcomes][enforcement_level]"]
            == "mandatory_overridable"
        )

    def test_list_set_outcomes_invalid_id(self, service):
        """list_set_outcomes() raises InvalidTfPolicyEvaluationIDError for a bad ID."""
        with pytest.raises(InvalidTfPolicyEvaluationIDError):
            list(service.list_set_outcomes("not valid!"))

    def test_list_set_outcomes_empty_id(self, service):
        """list_set_outcomes() raises InvalidTfPolicyEvaluationIDError for an empty ID."""
        with pytest.raises(InvalidTfPolicyEvaluationIDError):
            list(service.list_set_outcomes(""))
