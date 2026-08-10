# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""Unit tests for TfPolicySetOutcomes resource."""

from unittest.mock import Mock

import pytest

from pytfe._http import HTTPTransport
from pytfe.errors import InvalidTfPolicySetOutcomeIDError
from pytfe.models.policy_types import TfPolicyEnforcementLevel, TfPolicyEvaluationStatus
from pytfe.models.tf_policy_set_outcome import (
    PassedResource,
    PolicyOutcome,
    TfPolicySetOutcome,
    TfPolicySetOutcomeListOptions,
    TraversalValue,
)
from pytfe.resources.tf_policy_set_outcome import TfPolicySetOutcomes

_OUTCOME_ID = "tfpsout-abc123"


class TestTfPolicySetOutcomes:
    """Tests for the TfPolicySetOutcomes service."""

    @pytest.fixture
    def mock_transport(self):
        return Mock(spec=HTTPTransport)

    @pytest.fixture
    def service(self, mock_transport):
        return TfPolicySetOutcomes(mock_transport)

    @pytest.fixture
    def outcome_api_data(self):
        """Minimal set-outcome API data object."""
        return {
            "id": _OUTCOME_ID,
            "type": "tf-policy-set-outcomes",
            "attributes": {
                "policy-set-name": "security-baseline",
                "policy-set-description": "Baseline security policies",
                "overridable": True,
                "error": None,
                "result-count": {
                    "advisory-failed": 0,
                    "mandatory-failed": 1,
                    "passed": 2,
                    "errored": 0,
                    "unknown": 0,
                },
                # Inner outcomes use snake_case (stored verbatim, not dash-transformed).
                "outcomes": [
                    {
                        "policy_name": "require-tags",
                        "enforcement_level": "mandatory_overridable",
                        "status": "failed",
                        "file_name": "policies/require-tags.tf",
                        "description": "Resources must have required tags",
                        "diagnostics": [],
                        "passed_resources": [],
                    }
                ],
            },
            "relationships": {
                "tf-policy-evaluation": {
                    "data": {"id": "tfpeval-xyz", "type": "tf-policy-evaluations"}
                }
            },
        }

    # ── Model tests ──────────────────────────────────────────────────────────

    def test_outcome_model_fields(self, outcome_api_data):
        """TfPolicySetOutcome parses id, name, and overridable."""
        attrs = {**outcome_api_data["attributes"], "id": outcome_api_data["id"]}
        model = TfPolicySetOutcome.model_validate(attrs)
        assert model.id == _OUTCOME_ID
        assert model.policy_set_name == "security-baseline"
        assert model.overridable is True

    def test_outcome_result_count(self, outcome_api_data):
        """result_count sub-model parses mandatory_failed."""
        attrs = {**outcome_api_data["attributes"], "id": outcome_api_data["id"]}
        model = TfPolicySetOutcome.model_validate(attrs)
        assert model.result_count is not None
        assert model.result_count.mandatory_failed == 1

    def test_snake_case_outcomes_parse(self, outcome_api_data):
        """Inner outcomes array uses snake_case keys and parses without error.

        Atlas stores outcomes verbatim (not dash-transformed). This test asserts
        ``enforcement_level=mandatory_overridable`` survives round-trip.
        """
        attrs = {**outcome_api_data["attributes"], "id": outcome_api_data["id"]}
        model = TfPolicySetOutcome.model_validate(attrs)

        assert len(model.outcomes) == 1
        outcome = model.outcomes[0]
        assert outcome.policy_name == "require-tags"
        assert (
            outcome.enforcement_level == TfPolicyEnforcementLevel.MANDATORY_OVERRIDABLE
        )
        assert outcome.status == TfPolicyEvaluationStatus.FAILED

    def test_mandatory_overridable_wire_value(self):
        """TfPolicyEnforcementLevel.MANDATORY_OVERRIDABLE has underscore, not hyphen."""
        assert (
            TfPolicyEnforcementLevel.MANDATORY_OVERRIDABLE.value
            == "mandatory_overridable"
        )

    def test_policy_outcome_model_diagnostics(self):
        """PolicyOutcome.diagnostics sub-objects parse correctly."""
        outcome = PolicyOutcome.model_validate(
            {
                "policy_name": "test-policy",
                "enforcement_level": "mandatory",
                "status": "failed",
                "diagnostics": [
                    {
                        "code": "E001",
                        "summary": "tag missing",
                        "resources": [
                            {
                                "resource_name": "aws_instance.web",
                                "error_message": "missing tag Environment",
                                "values": [
                                    {
                                        "traversal": "aws_instance.web.tags",
                                        "statement": "{}",
                                    }
                                ],
                            }
                        ],
                    }
                ],
            }
        )
        assert len(outcome.diagnostics) == 1
        diag = outcome.diagnostics[0]
        assert diag.code == "E001"
        assert len(diag.resources) == 1
        resource = diag.resources[0]
        assert resource.resource_name == "aws_instance.web"
        assert len(resource.values) == 1
        assert resource.values[0].traversal == "aws_instance.web.tags"

    def test_passed_resource_parses(self):
        """PassedResource model parses resource_name and info_messages."""
        pr = PassedResource.model_validate(
            {
                "resource_name": "aws_instance.app",
                "info_messages": ["all tags present"],
            }
        )
        assert pr.resource_name == "aws_instance.app"
        assert pr.info_messages == ["all tags present"]

    def test_list_options_filter_fields(self):
        """TfPolicySetOutcomeListOptions accepts filter fields."""
        opts = TfPolicySetOutcomeListOptions(
            filter_status="failed",
            filter_enforcement_level="mandatory_overridable",
        )
        assert opts.filter_status == "failed"
        assert opts.filter_enforcement_level == "mandatory_overridable"

    def test_traversal_value_parses(self):
        """TraversalValue model parses traversal and statement."""
        tv = TraversalValue.model_validate(
            {"traversal": "var.tags", "statement": '{"env": "prod"}'}
        )
        assert tv.traversal == "var.tags"
        assert tv.statement == '{"env": "prod"}'

    # ── Parser tests ─────────────────────────────────────────────────────────

    def test_read_success(self, service, mock_transport, outcome_api_data):
        """read() GETs the correct path and returns TfPolicySetOutcome."""
        mock_response = Mock()
        mock_response.json.return_value = {"data": outcome_api_data}
        mock_transport.request.return_value = mock_response

        result = service.read(_OUTCOME_ID)

        mock_transport.request.assert_called_once_with(
            "GET", f"/api/v2/tf-policy-set-outcomes/{_OUTCOME_ID}"
        )
        assert isinstance(result, TfPolicySetOutcome)
        assert result.id == _OUTCOME_ID
        assert result.policy_set_name == "security-baseline"

    def test_read_outcome_with_snake_case_outcomes(
        self, service, mock_transport, outcome_api_data
    ):
        """read() correctly parses inner snake_case outcomes array."""
        mock_response = Mock()
        mock_response.json.return_value = {"data": outcome_api_data}
        mock_transport.request.return_value = mock_response

        result = service.read(_OUTCOME_ID)

        assert len(result.outcomes) == 1
        assert (
            result.outcomes[0].enforcement_level
            == TfPolicyEnforcementLevel.MANDATORY_OVERRIDABLE
        )

    def test_read_invalid_id(self, service):
        """read() raises InvalidTfPolicySetOutcomeIDError for a bad ID."""
        with pytest.raises(InvalidTfPolicySetOutcomeIDError):
            service.read("not valid!")

    def test_read_empty_id(self, service):
        """read() raises InvalidTfPolicySetOutcomeIDError for an empty ID."""
        with pytest.raises(InvalidTfPolicySetOutcomeIDError):
            service.read("")

    def test_read_null_error_field(self, service, mock_transport, outcome_api_data):
        """read() handles null error field gracefully."""
        outcome_api_data["attributes"]["error"] = None
        mock_response = Mock()
        mock_response.json.return_value = {"data": outcome_api_data}
        mock_transport.request.return_value = mock_response

        result = service.read(_OUTCOME_ID)
        assert result.error is None
