# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from unittest.mock import Mock

import pytest

from pytfe._http import HTTPTransport
from pytfe.errors import (
    InvalidAccessTokenError,
    InvalidCallbackURLError,
    InvalidTaskResultsCallbackStatusError,
    TFEError,
)
from pytfe.models.run_task_integration import (
    TaskResultCallbackRequestOptions,
    TaskResultOutcome,
    TaskResultStatus,
    TaskResultTag,
)
from pytfe.resources._base import _Service
from pytfe.resources.run_task_integration import RunTaskIntegrations

CALLBACK_URL = "https://app.terraform.io/api/v2/task-results/taskrs-abc/callback"
ACCESS_TOKEN = "v1.callback-token"


@pytest.fixture
def transport() -> Mock:
    return Mock(spec=HTTPTransport)


@pytest.fixture
def service(transport: Mock) -> RunTaskIntegrations:
    return RunTaskIntegrations(transport)


def _basic_options() -> TaskResultCallbackRequestOptions:
    return TaskResultCallbackRequestOptions(
        status=TaskResultStatus.passed,
        message="All good",
        url="https://example.com/details",
    )


# ─── Architectural sanity ─────────────────────────────────────────────────────


def test_service_extends_base_service():
    assert issubclass(RunTaskIntegrations, _Service)


def test_service_uses_transport(transport, service):
    assert service.t is transport


def test_typed_errors_subclass_tfe_error():
    assert issubclass(InvalidCallbackURLError, TFEError)
    assert issubclass(InvalidAccessTokenError, TFEError)
    assert issubclass(InvalidTaskResultsCallbackStatusError, TFEError)


# ─── Validation: callback URL ─────────────────────────────────────────────────


@pytest.mark.parametrize("bad_url", ["", "   ", "\t\n", None])
def test_callback_invalid_url_raises_typed_error(service, bad_url):
    with pytest.raises(InvalidCallbackURLError):
        service.callback(bad_url, ACCESS_TOKEN, _basic_options())  # type: ignore[arg-type]


# ─── Validation: access token ─────────────────────────────────────────────────


@pytest.mark.parametrize("bad_token", ["", "   ", "\t\n", None])
def test_callback_invalid_token_raises_typed_error(service, bad_token):
    with pytest.raises(InvalidAccessTokenError):
        service.callback(CALLBACK_URL, bad_token, _basic_options())  # type: ignore[arg-type]


# ─── Validation: status ───────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "good_status",
    [TaskResultStatus.passed, TaskResultStatus.failed, TaskResultStatus.running],
)
def test_callback_accepts_all_valid_statuses(service, transport, good_status):
    options = TaskResultCallbackRequestOptions(status=good_status)
    service.callback(CALLBACK_URL, ACCESS_TOKEN, options)
    attrs = transport.request.call_args.kwargs["json_body"]["data"]["attributes"]
    assert attrs["status"] == good_status.value


@pytest.mark.parametrize(
    "bad_status",
    ["pending", "errored", "unreachable", "", "PASSED", "unknown", None, 123],
)
def test_callback_rejects_invalid_statuses(service, bad_status):
    options = TaskResultCallbackRequestOptions(status=TaskResultStatus.passed)
    options.status = bad_status  # type: ignore[assignment]
    with pytest.raises(InvalidTaskResultsCallbackStatusError):
        service.callback(CALLBACK_URL, ACCESS_TOKEN, options)


# ─── Transport invocation ─────────────────────────────────────────────────────


def test_callback_invokes_transport_with_exact_args(service, transport):
    expected_payload = {
        "data": {
            "type": "task-results",
            "attributes": {
                "status": "passed",
                "message": "All good",
                "url": "https://example.com/details",
            },
        }
    }
    service.callback(CALLBACK_URL, ACCESS_TOKEN, _basic_options())

    transport.request.assert_called_once_with(
        "PATCH",
        CALLBACK_URL,
        json_body=expected_payload,
        headers={
            "Authorization": f"Bearer {ACCESS_TOKEN}",
            "Content-Type": "application/vnd.api+json",
        },
    )


def test_callback_passes_absolute_url_unchanged(service, transport):
    service.callback(CALLBACK_URL, ACCESS_TOKEN, _basic_options())
    args, _ = transport.request.call_args
    assert args[0] == "PATCH"
    assert args[1] == CALLBACK_URL
    assert args[1].startswith("https://")


def test_authorization_header_uses_callback_token(service, transport):
    service.callback(CALLBACK_URL, ACCESS_TOKEN, _basic_options())
    kwargs = transport.request.call_args.kwargs
    assert kwargs["headers"] == {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/vnd.api+json",
    }


def test_callback_does_not_call_transport_on_validation_failure(service, transport):
    with pytest.raises(InvalidCallbackURLError):
        service.callback("", ACCESS_TOKEN, _basic_options())
    transport.request.assert_not_called()


# ─── Payload serialization: exact JSON:API shape ──────────────────────────────


def test_payload_basic_exact_shape(service, transport):
    service.callback(CALLBACK_URL, ACCESS_TOKEN, _basic_options())
    assert transport.request.call_args.kwargs["json_body"] == {
        "data": {
            "type": "task-results",
            "attributes": {
                "status": "passed",
                "message": "All good",
                "url": "https://example.com/details",
            },
        }
    }


def test_payload_status_only_exact_shape(service, transport):
    options = TaskResultCallbackRequestOptions(status=TaskResultStatus.running)
    service.callback(CALLBACK_URL, ACCESS_TOKEN, options)
    assert transport.request.call_args.kwargs["json_body"] == {
        "data": {
            "type": "task-results",
            "attributes": {"status": "running"},
        }
    }


def test_payload_with_outcomes_and_tags_exact_shape(service, transport):
    outcome = TaskResultOutcome(
        outcome_id="o-1",
        description="desc",
        body="body",
        url="https://example.com/o1",
        tags={
            "severity": [
                TaskResultTag(label="high", level="error"),
                TaskResultTag(label="cve"),
            ]
        },
    )
    options = TaskResultCallbackRequestOptions(
        status=TaskResultStatus.failed, outcomes=[outcome]
    )
    service.callback(CALLBACK_URL, ACCESS_TOKEN, options)

    assert transport.request.call_args.kwargs["json_body"] == {
        "data": {
            "type": "task-results",
            "attributes": {"status": "failed"},
            "relationships": {
                "outcomes": {
                    "data": [
                        {
                            "type": "task-result-outcomes",
                            "attributes": {
                                "outcome-id": "o-1",
                                "description": "desc",
                                "body": "body",
                                "url": "https://example.com/o1",
                                "tags": {
                                    "severity": [
                                        {"label": "high", "level": "error"},
                                        {"label": "cve"},
                                    ]
                                },
                            },
                        }
                    ]
                }
            },
        }
    }


# ─── Omission (`omitempty` parity) ────────────────────────────────────────────


def test_message_omitted_when_none(service, transport):
    options = TaskResultCallbackRequestOptions(
        status=TaskResultStatus.passed, url="https://x"
    )
    service.callback(CALLBACK_URL, ACCESS_TOKEN, options)
    attrs = transport.request.call_args.kwargs["json_body"]["data"]["attributes"]
    assert "message" not in attrs


def test_url_omitted_when_none(service, transport):
    options = TaskResultCallbackRequestOptions(
        status=TaskResultStatus.passed, message="m"
    )
    service.callback(CALLBACK_URL, ACCESS_TOKEN, options)
    attrs = transport.request.call_args.kwargs["json_body"]["data"]["attributes"]
    assert "url" not in attrs


def test_relationships_omitted_when_outcomes_none(service, transport):
    options = TaskResultCallbackRequestOptions(status=TaskResultStatus.passed)
    service.callback(CALLBACK_URL, ACCESS_TOKEN, options)
    body = transport.request.call_args.kwargs["json_body"]
    assert "relationships" not in body["data"]


def test_relationships_omitted_when_outcomes_empty_list(service, transport):
    options = TaskResultCallbackRequestOptions(
        status=TaskResultStatus.passed, outcomes=[]
    )
    service.callback(CALLBACK_URL, ACCESS_TOKEN, options)
    body = transport.request.call_args.kwargs["json_body"]
    assert "relationships" not in body["data"]


def test_outcome_attributes_omit_none_fields(service, transport):
    options = TaskResultCallbackRequestOptions(
        status=TaskResultStatus.passed, outcomes=[TaskResultOutcome()]
    )
    service.callback(CALLBACK_URL, ACCESS_TOKEN, options)
    entry = transport.request.call_args.kwargs["json_body"]["data"]["relationships"][
        "outcomes"
    ]["data"][0]
    assert entry == {"type": "task-result-outcomes", "attributes": {}}


def test_tag_level_omitted_when_none(service, transport):
    outcome = TaskResultOutcome(tags={"category": [TaskResultTag(label="only")]})
    options = TaskResultCallbackRequestOptions(
        status=TaskResultStatus.passed, outcomes=[outcome]
    )
    service.callback(CALLBACK_URL, ACCESS_TOKEN, options)
    tags = transport.request.call_args.kwargs["json_body"]["data"]["relationships"][
        "outcomes"
    ]["data"][0]["attributes"]["tags"]
    assert tags == {"category": [{"label": "only"}]}


def test_outcome_tags_omitted_when_none(service, transport):
    outcome = TaskResultOutcome(description="no tags here")
    options = TaskResultCallbackRequestOptions(
        status=TaskResultStatus.passed, outcomes=[outcome]
    )
    service.callback(CALLBACK_URL, ACCESS_TOKEN, options)
    attrs = transport.request.call_args.kwargs["json_body"]["data"]["relationships"][
        "outcomes"
    ]["data"][0]["attributes"]
    assert attrs == {"description": "no tags here"}


# ─── Edge cases ───────────────────────────────────────────────────────────────


def test_multiple_outcomes_preserve_order(service, transport):
    options = TaskResultCallbackRequestOptions(
        status=TaskResultStatus.passed,
        outcomes=[
            TaskResultOutcome(outcome_id="o-1", description="first"),
            TaskResultOutcome(outcome_id="o-2", description="second"),
            TaskResultOutcome(outcome_id="o-3", description="third"),
        ],
    )
    service.callback(CALLBACK_URL, ACCESS_TOKEN, options)
    outcomes = transport.request.call_args.kwargs["json_body"]["data"]["relationships"][
        "outcomes"
    ]["data"]
    assert [o["attributes"]["outcome-id"] for o in outcomes] == ["o-1", "o-2", "o-3"]


def test_multiple_tags_per_category(service, transport):
    outcome = TaskResultOutcome(
        tags={
            "severity": [
                TaskResultTag(label="critical", level="error"),
                TaskResultTag(label="high", level="error"),
                TaskResultTag(label="medium", level="warning"),
            ],
            "compliance": [TaskResultTag(label="pci-dss")],
        }
    )
    options = TaskResultCallbackRequestOptions(
        status=TaskResultStatus.failed, outcomes=[outcome]
    )
    service.callback(CALLBACK_URL, ACCESS_TOKEN, options)
    tags = transport.request.call_args.kwargs["json_body"]["data"]["relationships"][
        "outcomes"
    ]["data"][0]["attributes"]["tags"]
    assert tags == {
        "severity": [
            {"label": "critical", "level": "error"},
            {"label": "high", "level": "error"},
            {"label": "medium", "level": "warning"},
        ],
        "compliance": [{"label": "pci-dss"}],
    }


def test_unicode_message_and_body(service, transport):
    outcome = TaskResultOutcome(body="✓ all good — 通过")
    options = TaskResultCallbackRequestOptions(
        status=TaskResultStatus.passed,
        message="résumé 🎉",
        outcomes=[outcome],
    )
    service.callback(CALLBACK_URL, ACCESS_TOKEN, options)
    body = transport.request.call_args.kwargs["json_body"]
    assert body["data"]["attributes"]["message"] == "résumé 🎉"
    assert (
        body["data"]["relationships"]["outcomes"]["data"][0]["attributes"]["body"]
        == "✓ all good — 通过"
    )


def test_markdown_body_preserved_verbatim(service, transport):
    md = "## Results\n\n- [link](https://x)\n- **bold**\n\n```py\nprint('ok')\n```"
    outcome = TaskResultOutcome(body=md)
    options = TaskResultCallbackRequestOptions(
        status=TaskResultStatus.passed, outcomes=[outcome]
    )
    service.callback(CALLBACK_URL, ACCESS_TOKEN, options)
    serialized = transport.request.call_args.kwargs["json_body"]["data"][
        "relationships"
    ]["outcomes"]["data"][0]["attributes"]["body"]
    assert serialized == md


def test_status_serialized_as_plain_string(service, transport):
    service.callback(CALLBACK_URL, ACCESS_TOKEN, _basic_options())
    status = transport.request.call_args.kwargs["json_body"]["data"]["attributes"][
        "status"
    ]
    assert isinstance(status, str)
    assert status == "passed"


# ─── Pydantic alias / model behavior ──────────────────────────────────────────


def test_outcome_accepts_alias_input():
    outcome = TaskResultOutcome.model_validate({"outcome-id": "o-1"})
    assert outcome.outcome_id == "o-1"


def test_options_accepts_string_status():
    options = TaskResultCallbackRequestOptions.model_validate({"status": "passed"})
    assert options.status == TaskResultStatus.passed


# ─── SDK client wiring ────────────────────────────────────────────────────────


def test_client_wires_run_task_integrations():
    """The TFEClient must expose `run_task_integrations` as a RunTaskIntegrations
    bound to the client transport. Catches accidental rename / unwiring."""
    from pytfe import TFEClient, TFEConfig

    client = TFEClient(
        TFEConfig(address="https://app.terraform.io", token="dummy-token")
    )
    assert isinstance(client.run_task_integrations, RunTaskIntegrations)
    assert client.run_task_integrations.t is client._transport


# ─── Return value & idempotency ───────────────────────────────────────────────


def test_callback_returns_none(service, transport):
    transport.request.return_value = {"data": {"id": "ignored"}}
    assert service.callback(CALLBACK_URL, ACCESS_TOKEN, _basic_options()) is None


def test_to_payload_is_idempotent():
    """Calling to_payload twice must produce equal dicts and must not mutate
    the options instance — important because callers may inspect/log payloads."""
    options = TaskResultCallbackRequestOptions(
        status=TaskResultStatus.passed,
        message="hi",
        outcomes=[
            TaskResultOutcome(
                outcome_id="o-1",
                tags={"sev": [TaskResultTag(label="high", level="error")]},
            )
        ],
    )
    first = options.to_payload()
    second = options.to_payload()
    assert first == second
    # Mutating the returned payload must not affect the next serialization.
    first["data"]["attributes"]["status"] = "mutated"
    assert options.to_payload()["data"]["attributes"]["status"] == "passed"


def test_to_payload_is_json_serializable():
    """The transport ultimately json.dumps the body; the payload must contain
    only JSON-native types (no Enum, no Pydantic models)."""
    import json

    options = TaskResultCallbackRequestOptions(
        status=TaskResultStatus.failed,
        outcomes=[
            TaskResultOutcome(
                outcome_id="o-1",
                tags={"sev": [TaskResultTag(label="high", level="error")]},
            )
        ],
    )
    encoded = json.dumps(options.to_payload())
    assert json.loads(encoded) == options.to_payload()


# ─── Transport-side errors ────────────────────────────────────────────────────


def test_transport_exception_propagates(service, transport):
    """If the transport raises (e.g. network/HTTP error), the SDK must not
    swallow it — callers need the failure to retry/log."""
    transport.request.side_effect = RuntimeError("boom")
    with pytest.raises(RuntimeError, match="boom"):
        service.callback(CALLBACK_URL, ACCESS_TOKEN, _basic_options())


def test_sequential_callbacks_are_independent(service, transport):
    """Two callbacks on the same service must produce two distinct requests."""
    service.callback(CALLBACK_URL, ACCESS_TOKEN, _basic_options())
    service.callback(
        CALLBACK_URL,
        "v1.other-token",
        TaskResultCallbackRequestOptions(status=TaskResultStatus.failed),
    )
    assert transport.request.call_count == 2
    assert transport.request.call_args_list[0].kwargs["headers"] == {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/vnd.api+json",
    }
    assert transport.request.call_args_list[1].kwargs["headers"] == {
        "Authorization": "Bearer v1.other-token",
        "Content-Type": "application/vnd.api+json",
    }
    assert (
        transport.request.call_args_list[1].kwargs["json_body"]["data"]["attributes"][
            "status"
        ]
        == "failed"
    )


# ─── Current-behavior pins for empty-collection edge cases ────────────────────


def test_outcome_with_empty_tags_dict_emits_empty_object(service, transport):
    """Document current behavior: tags={} serializes as an empty object rather
    than being omitted. Go SDK ``omitempty`` would drop it; if parity is
    desired later, update both the model and this test together."""
    outcome = TaskResultOutcome(tags={})
    options = TaskResultCallbackRequestOptions(
        status=TaskResultStatus.passed, outcomes=[outcome]
    )
    service.callback(CALLBACK_URL, ACCESS_TOKEN, options)
    attrs = transport.request.call_args.kwargs["json_body"]["data"]["relationships"][
        "outcomes"
    ]["data"][0]["attributes"]
    assert attrs == {"tags": {}}
