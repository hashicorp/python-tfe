"""Unit tests for the policy_check module."""

from unittest.mock import Mock, patch

import pytest

from pytfe._http import HTTPTransport
from pytfe.errors import InvalidPolicyCheckIDError, InvalidRunIDError
from pytfe.models.policy_check import (
    PolicyCheck,
    PolicyCheckIncludeOpt,
    PolicyCheckListOptions,
    PolicyStatus,
)
from pytfe.resources.policy_check import PolicyChecks


class TestPolicyChecks:
    """Test the PolicyChecks service class."""

    @pytest.fixture
    def mock_transport(self):
        """Create a mock HTTPTransport."""
        return Mock(spec=HTTPTransport)

    @pytest.fixture
    def policy_checks_service(self, mock_transport):
        """Create a PolicyChecks service with mocked transport."""
        return PolicyChecks(mock_transport)

    def test_list_policy_checks_validation(self, policy_checks_service):
        """Test list() with invalid run ID."""
        with pytest.raises(InvalidRunIDError):
            list(policy_checks_service.list(""))

    def test_list_policy_checks_iterator(self, policy_checks_service):
        """Test list() returns an iterator of PolicyCheck models."""
        # Mock items match the raw data objects yielded by _list() as per the
        # List Policy Checks API response:
        # https://developer.hashicorp.com/terraform/cloud-docs/api-docs/policy-checks#list-policy-checks
        mock_items = [
            {
                "id": "polchk-9VYRc9bpfJEsnwum",
                "type": "policy-checks",
                "attributes": {
                    "result": {
                        "result": False,
                        "passed": 0,
                        "total-failed": 1,
                        "hard-failed": 0,
                        "soft-failed": 1,
                        "advisory-failed": 0,
                        "duration-ms": 0,
                        "sentinel": None,
                    },
                    "scope": "organization",
                    "status": "soft_failed",
                    "status-timestamps": {
                        "queued-at": "2017-11-29T20:02:17+00:00",
                        "soft-failed-at": "2017-11-29T20:02:20+00:00",
                    },
                    "actions": {"is-overridable": True},
                    "permissions": {"can-override": False},
                },
                "relationships": {
                    "run": {"data": {"id": "run-veDoQbv6xh6TbnJD", "type": "runs"}}
                },
                "links": {
                    "output": "/api/v2/policy-checks/polchk-9VYRc9bpfJEsnwum/output"
                },
            },
            {
                "id": "polchk-passed456",
                "type": "policy-checks",
                "attributes": {
                    "result": {
                        "result": True,
                        "passed": 3,
                        "total-failed": 0,
                        "hard-failed": 0,
                        "soft-failed": 0,
                        "advisory-failed": 0,
                        "duration-ms": 120,
                        "sentinel": None,
                    },
                    "scope": "workspace",
                    "status": "passed",
                    "status-timestamps": {
                        "queued-at": "2017-11-29T20:02:17+00:00",
                        "passed-at": "2017-11-29T20:02:19+00:00",
                    },
                    "actions": {"is-overridable": False},
                    "permissions": {"can-override": False},
                },
                "relationships": {
                    "run": {"data": {"id": "run-veDoQbv6xh6TbnJD", "type": "runs"}}
                },
                "links": {"output": "/api/v2/policy-checks/polchk-passed456/output"},
            },
        ]

        with patch.object(policy_checks_service, "_list") as mock_list:
            mock_list.return_value = mock_items

            options = PolicyCheckListOptions(
                page_size=25,
                include=[PolicyCheckIncludeOpt.POLICY_CHECK_RUN],
            )
            result = list(policy_checks_service.list("run-1", options))

            mock_list.assert_called_once()
            call_args = mock_list.call_args
            assert call_args[0][0] == "/api/v2/runs/run-1/policy-checks"
            params = call_args[1]["params"]
            assert params["page[size]"] == 25

            assert len(result) == 2
            assert all(isinstance(item, PolicyCheck) for item in result)

            pc0 = result[0]
            assert pc0.id == "polchk-9VYRc9bpfJEsnwum"
            assert pc0.status == PolicyStatus.POLICY_SOFT_FAILED
            assert pc0.scope.value == "organization"
            assert pc0.result is not None
            assert pc0.result.soft_failed == 1
            assert pc0.result.passed == 0
            assert pc0.result.total_failed == 1
            assert pc0.actions.is_overridable is True
            assert pc0.permissions.can_override is False
            assert pc0.status_timestamps.queued_at is not None
            assert pc0.status_timestamps.soft_failed_at is not None

            pc1 = result[1]
            assert pc1.id == "polchk-passed456"
            assert pc1.status == PolicyStatus.POLICY_PASSES
            assert pc1.scope.value == "workspace"
            assert pc1.result.passed == 3
            assert pc1.result.total_failed == 0

    def test_read_policy_check(self, policy_checks_service, mock_transport):
        """Test read() for a policy check.

        Mock matches the Show Policy Check API response:
        https://developer.hashicorp.com/terraform/cloud-docs/api-docs/policy-checks#show-policy-check
        """
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {
                "id": "polchk-9VYRc9bpfJEsnwum",
                "type": "policy-checks",
                "attributes": {
                    "result": {
                        "result": False,
                        "passed": 0,
                        "total-failed": 1,
                        "hard-failed": 0,
                        "soft-failed": 1,
                        "advisory-failed": 0,
                        "duration-ms": 0,
                        "sentinel": None,
                    },
                    "scope": "organization",
                    "status": "soft_failed",
                    "status-timestamps": {
                        "queued-at": "2017-11-29T20:02:17+00:00",
                        "soft-failed-at": "2017-11-29T20:02:20+00:00",
                    },
                    "actions": {"is-overridable": True},
                    "permissions": {"can-override": False},
                },
                "relationships": {
                    "run": {"data": {"id": "run-veDoQbv6xh6TbnJD", "type": "runs"}}
                },
                "links": {
                    "output": "/api/v2/policy-checks/polchk-9VYRc9bpfJEsnwum/output"
                },
            }
        }
        mock_transport.request.return_value = mock_response

        result = policy_checks_service.read("polchk-9VYRc9bpfJEsnwum")

        mock_transport.request.assert_called_once_with(
            "GET", "/api/v2/policy-checks/polchk-9VYRc9bpfJEsnwum"
        )
        assert result.id == "polchk-9VYRc9bpfJEsnwum"
        assert result.status == PolicyStatus.POLICY_SOFT_FAILED
        assert result.scope.value == "organization"
        assert result.result is not None
        assert result.result.soft_failed == 1
        assert result.result.total_failed == 1
        assert result.result.passed == 0
        assert result.result.result is False
        assert result.actions.is_overridable is True
        assert result.permissions.can_override is False
        assert result.status_timestamps.queued_at is not None
        assert result.status_timestamps.soft_failed_at is not None

    def test_override_policy_check(self, policy_checks_service, mock_transport):
        """Test override() for a policy check.

        Mock matches the Override Policy API response:
        https://developer.hashicorp.com/terraform/cloud-docs/api-docs/policy-checks#override-policy
        """
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {
                "id": "polchk-EasPB4Srx5NAiWAU",
                "type": "policy-checks",
                "attributes": {
                    "result": {
                        "result": False,
                        "passed": 0,
                        "total-failed": 1,
                        "hard-failed": 0,
                        "soft-failed": 1,
                        "advisory-failed": 0,
                        "duration-ms": 0,
                        "sentinel": None,
                    },
                    "scope": "organization",
                    "status": "overridden",
                    "status-timestamps": {
                        "queued-at": "2017-11-29T20:13:37+00:00",
                        "soft-failed-at": "2017-11-29T20:13:40+00:00",
                        "overridden-at": "2017-11-29T20:14:11+00:00",
                    },
                    "actions": {"is-overridable": True},
                    "permissions": {"can-override": False},
                },
                "links": {
                    "output": "/api/v2/policy-checks/polchk-EasPB4Srx5NAiWAU/output"
                },
            }
        }
        mock_transport.request.return_value = mock_response

        result = policy_checks_service.override("polchk-EasPB4Srx5NAiWAU")

        mock_transport.request.assert_called_once_with(
            "POST", "/api/v2/policy-checks/polchk-EasPB4Srx5NAiWAU/actions/override"
        )
        assert result.id == "polchk-EasPB4Srx5NAiWAU"
        assert result.status == PolicyStatus.POLICY_OVERRIDDEN
        assert result.scope.value == "organization"
        assert result.result.soft_failed == 1
        assert result.actions.is_overridable is True
        assert result.status_timestamps.soft_failed_at is not None
        assert result.status_timestamps.queued_at is not None

    def test_logs_invalid_id(self, policy_checks_service):
        """Test logs() with invalid policy check ID."""
        with pytest.raises(InvalidPolicyCheckIDError):
            policy_checks_service.logs("")

    def test_logs_waits_until_ready(self, policy_checks_service, mock_transport):
        """Test logs() polling until policy status is no longer pending/queued."""
        pending_pc = PolicyCheck(id="pc-1", status=PolicyStatus.POLICY_PENDING)
        passed_pc = PolicyCheck(id="pc-1", status=PolicyStatus.POLICY_PASSES)

        with (
            patch.object(policy_checks_service, "read") as mock_read,
            patch("pytfe.resources.policy_check.time.sleep") as mock_sleep,
        ):
            mock_read.side_effect = [pending_pc, passed_pc]
            mock_response = Mock()
            mock_response.text = "policy output"
            mock_transport.request.return_value = mock_response

            logs = policy_checks_service.logs("pc-1")

            assert logs == "policy output"
            assert mock_read.call_count == 2
            mock_sleep.assert_called_once_with(0.5)
            mock_transport.request.assert_called_once_with(
                "GET", "/api/v2/policy-checks/pc-1/output"
            )


def test_policy_check_list_options_has_no_page_number():
    """Ensure iterator-style list options no longer expose page_number."""
    options = PolicyCheckListOptions(page_size=10)
    dumped = options.model_dump(by_alias=True, exclude_none=True)
    assert dumped == {"page[size]": 10}
